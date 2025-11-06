"""
Pestaña de calificación con procesamiento por lotes de PDFs escaneados
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
from pathlib import Path
import os
from typing import List, Dict

from src.utils.constants import (MSG_INVALID_CONFIG, MSG_NO_ANSWER_KEY,
                                MSG_NO_EXCEL_LOADED, MSG_GRADE_SAVED,
                                MSG_DUPLICATE_GRADE, MSG_STUDENT_NOT_FOUND)
from src.core.grade_calculator import GradeCalculator
from src.core.pdf_processor import PDFProcessor
from src.core.image_processor import ImageProcessor
from src.core.omr_detector import OMRDetector
from src.ui.manual_review_window import ManualReviewWindow


class GradingTab:
    """
    Pestaña para calificar pruebas usando PDFs escaneados con procesamiento por lotes
    """

    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data

        # Estado de procesamiento
        self.pdf_queue = []  # Lista de PDFs a procesar
        self.processing = False
        self.current_results = []  # Resultados de procesamiento

        # Procesadores
        try:
            self.pdf_processor = PDFProcessor(dpi=300)
            self.image_processor = ImageProcessor()
            self.omr_detector = OMRDetector()
            self.processors_ready = True
        except FileNotFoundError as e:
            self.processors_ready = False
            self.calibration_error = str(e)

        # Crear frame principal
        self.main_frame = ctk.CTkFrame(parent)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.create_widgets()

        # Mostrar error de calibración si corresponde
        if not self.processors_ready:
            messagebox.showwarning(
                "Calibración Requerida",
                f"No se pudo inicializar el sistema:\n\n{self.calibration_error}\n\n" +
                "Por favor ejecute el script de calibración:\n" +
                "python calibrate_from_pdf.py <hoja_blanca.pdf>"
            )

    def create_widgets(self):
        """Crea todos los widgets de la pestaña"""

        # ===== SECCIÓN SUPERIOR: CARGA DE PDFs =====
        upload_frame = ctk.CTkFrame(self.main_frame)
        upload_frame.pack(fill="x", pady=(0, 10))

        # Título
        title_label = ctk.CTkLabel(upload_frame,
                                   text="📄 Cargar Hojas de Respuestas Escaneadas",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)

        # Botones de carga
        buttons_frame = ctk.CTkFrame(upload_frame)
        buttons_frame.pack(pady=10)

        self.load_files_btn = ctk.CTkButton(buttons_frame,
                                           text="📁 Cargar PDFs",
                                           command=self.load_pdf_files,
                                           height=40,
                                           width=180)
        self.load_files_btn.pack(side="left", padx=10)

        self.load_folder_btn = ctk.CTkButton(buttons_frame,
                                            text="📂 Cargar Carpeta",
                                            command=self.load_pdf_folder,
                                            height=40,
                                            width=180)
        self.load_folder_btn.pack(side="left", padx=10)

        self.clear_queue_btn = ctk.CTkButton(buttons_frame,
                                            text="🗑️ Limpiar Lista",
                                            command=self.clear_queue,
                                            height=40,
                                            width=180,
                                            fg_color="gray",
                                            hover_color="darkgray")
        self.clear_queue_btn.pack(side="left", padx=10)

        # Área informativa de carga
        self.info_area = ctk.CTkFrame(upload_frame, height=100, border_width=2,
                                      border_color="gray")
        self.info_area.pack(fill="x", padx=20, pady=10)

        info_label = ctk.CTkLabel(self.info_area,
                                  text="📁 Usa los botones de arriba para agregar archivos PDF\n" +
                                       "Puedes agregar PDFs individuales o carpetas completas",
                                  font=ctk.CTkFont(size=14))
        info_label.pack(expand=True, pady=30)

        # ===== SECCIÓN MEDIA: LISTA DE PDFs =====
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)

        list_title = ctk.CTkLabel(list_frame,
                                 text="Lista de PDFs a Procesar",
                                 font=ctk.CTkFont(size=14, weight="bold"))
        list_title.pack(pady=5)

        # Scrollable frame para lista de PDFs
        self.pdf_list_frame = ctk.CTkScrollableFrame(list_frame, height=200)
        self.pdf_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Label para cuando está vacía
        self.empty_list_label = ctk.CTkLabel(self.pdf_list_frame,
                                            text="No hay PDFs cargados",
                                            font=ctk.CTkFont(size=12),
                                            text_color="gray")
        self.empty_list_label.pack(pady=20)

        # ===== SECCIÓN INFERIOR: PROCESAMIENTO =====
        process_frame = ctk.CTkFrame(self.main_frame)
        process_frame.pack(fill="x", pady=10)

        # Botón de procesar
        self.process_btn = ctk.CTkButton(process_frame,
                                        text="▶️ Procesar Todos",
                                        command=self.start_processing,
                                        height=50,
                                        width=200,
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color="green",
                                        hover_color="darkgreen",
                                        state="disabled")
        self.process_btn.pack(pady=10)

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(process_frame, width=600)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # Label de estado
        self.status_label = ctk.CTkLabel(process_frame,
                                        text="",
                                        font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=5)

        # ===== RESULTADOS =====
        results_frame = ctk.CTkFrame(self.main_frame)
        results_frame.pack(fill="both", expand=True, pady=10)

        results_title = ctk.CTkLabel(results_frame,
                                    text="Resultados del Procesamiento",
                                    font=ctk.CTkFont(size=14, weight="bold"))
        results_title.pack(pady=5)

        self.results_text = ctk.CTkTextbox(results_frame, height=150,
                                          font=ctk.CTkFont(family="Courier", size=11))
        self.results_text.pack(fill="both", expand=True, padx=10, pady=5)

    def load_pdf_files(self):
        """Abre diálogo para seleccionar archivos PDF"""
        files = filedialog.askopenfilenames(
            title="Seleccionar PDFs de Hojas de Respuestas",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )

        if files:
            self.add_pdfs_to_queue(list(files))

    def load_pdf_folder(self):
        """Abre diálogo para seleccionar carpeta con PDFs"""
        folder = filedialog.askdirectory(title="Seleccionar Carpeta con PDFs")

        if folder:
            folder_path = Path(folder)
            pdf_files = list(folder_path.glob('*.pdf')) + list(folder_path.glob('*.PDF'))

            if pdf_files:
                self.add_pdfs_to_queue([str(p) for p in pdf_files])
            else:
                messagebox.showwarning("Sin PDFs",
                                      f"No se encontraron archivos PDF en:\n{folder}")

    def add_pdfs_to_queue(self, pdf_paths: List[str]):
        """Agrega PDFs a la cola de procesamiento"""
        # Evitar duplicados
        existing_paths = {item['path'] for item in self.pdf_queue}
        new_pdfs = [p for p in pdf_paths if p not in existing_paths]

        if not new_pdfs:
            messagebox.showinfo("Info", "Todos los PDFs ya están en la lista")
            return

        # Agregar a la cola
        for pdf_path in new_pdfs:
            self.pdf_queue.append({
                'path': pdf_path,
                'filename': Path(pdf_path).name,
                'status': 'pending',  # pending, processing, success, error
                'result': None
            })

        # Actualizar interfaz
        self.update_pdf_list()
        self.process_btn.configure(state="normal")

        messagebox.showinfo("PDFs Cargados",
                           f"Se agregaron {len(new_pdfs)} PDFs a la cola\n" +
                           f"Total en cola: {len(self.pdf_queue)}")

    def clear_queue(self):
        """Limpia la cola de PDFs"""
        if not self.pdf_queue:
            return

        if messagebox.askyesno("Confirmar",
                              f"¿Eliminar {len(self.pdf_queue)} PDFs de la cola?"):
            self.pdf_queue = []
            self.update_pdf_list()
            self.process_btn.configure(state="disabled")
            self.results_text.delete("1.0", "end")

    def update_pdf_list(self):
        """Actualiza la visualización de la lista de PDFs"""
        # Limpiar lista actual
        for widget in self.pdf_list_frame.winfo_children():
            widget.destroy()

        if not self.pdf_queue:
            self.empty_list_label = ctk.CTkLabel(self.pdf_list_frame,
                                                text="No hay PDFs cargados",
                                                font=ctk.CTkFont(size=12),
                                                text_color="gray")
            self.empty_list_label.pack(pady=20)
            return

        # Mostrar cada PDF
        for idx, item in enumerate(self.pdf_queue, 1):
            # Frame para cada PDF
            item_frame = ctk.CTkFrame(self.pdf_list_frame)
            item_frame.pack(fill="x", pady=2, padx=5)

            # Emoji de estado
            status_emoji = {
                'pending': '⏳',
                'processing': '⚙️',
                'success': '✅',
                'error': '❌'
            }.get(item['status'], '❓')

            # Label con información
            label_text = f"{idx}. {status_emoji} {item['filename']}"
            label = ctk.CTkLabel(item_frame, text=label_text, anchor="w")
            label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

            # Botón para eliminar (solo si está pendiente)
            if item['status'] == 'pending':
                remove_btn = ctk.CTkButton(item_frame,
                                          text="❌",
                                          width=30,
                                          command=lambda i=idx-1: self.remove_pdf(i))
                remove_btn.pack(side="right", padx=5)

    def remove_pdf(self, index: int):
        """Elimina un PDF de la cola"""
        if 0 <= index < len(self.pdf_queue):
            self.pdf_queue.pop(index)
            self.update_pdf_list()

            if not self.pdf_queue:
                self.process_btn.configure(state="disabled")

    def start_processing(self):
        """Inicia el procesamiento por lotes de PDFs"""
        # Verificar que haya calibración
        if not self.processors_ready:
            messagebox.showerror("Error",
                               "Sistema no calibrado. Ejecute:\n" +
                               "python calibrate_from_pdf.py <hoja_blanca.pdf>")
            return

        # Verificar configuración
        if self.app_data.get('num_questions', 0) == 0:
            messagebox.showerror("Error", MSG_INVALID_CONFIG)
            return

        if not self.app_data.get('answer_key'):
            answer = messagebox.askyesno("Sin Pauta",
                                        "No hay pauta de respuestas configurada.\n\n" +
                                        "¿Desea continuar solo con detección (sin calificar)?")
            if not answer:
                return

        # Verificar que haya PDFs pendientes
        pending = [item for item in self.pdf_queue if item['status'] == 'pending']
        if not pending:
            messagebox.showinfo("Info", "No hay PDFs pendientes para procesar")
            return

        # Deshabilitar controles
        self.processing = True
        self.process_btn.configure(state="disabled")
        self.load_files_btn.configure(state="disabled")
        self.load_folder_btn.configure(state="disabled")
        self.clear_queue_btn.configure(state="disabled")

        # Limpiar resultados anteriores
        self.results_text.delete("1.0", "end")
        self.current_results = []

        # Iniciar procesamiento en thread separado
        thread = threading.Thread(target=self.process_all_pdfs, daemon=True)
        thread.start()

    def process_all_pdfs(self):
        """Procesa todos los PDFs de la cola (ejecuta en thread separado)"""
        pending = [item for item in self.pdf_queue if item['status'] == 'pending']
        total = len(pending)

        for idx, item in enumerate(pending, 1):
            # Actualizar estado
            item['status'] = 'processing'
            self.parent.after(0, self.update_pdf_list)
            self.parent.after(0, lambda i=idx, t=total:
                            self.status_label.configure(
                                text=f"Procesando {i}/{t}: {item['filename']}"))

            # Procesar PDF
            result = self.process_single_pdf(item['path'])
            item['result'] = result
            item['status'] = 'success' if result['success'] else 'error'

            # Actualizar progreso
            progress = idx / total
            self.parent.after(0, lambda p=progress: self.progress_bar.set(p))
            self.parent.after(0, self.update_pdf_list)

            # Agregar resultado
            self.current_results.append(result)
            self.parent.after(0, lambda r=result: self.append_result(r))

        # Finalizar
        self.parent.after(0, self.finish_processing)

    def process_single_pdf(self, pdf_path: str) -> Dict:
        """Procesa un solo PDF y retorna los resultados"""
        result = {
            'pdf_path': pdf_path,
            'filename': Path(pdf_path).name,
            'success': False,
            'matricula': None,
            'respuestas': {},
            'correctas': 0,
            'incorrectas': 0,
            'nota': 0.0,
            'confidence': 0.0,
            'message': '',
            'saved_to_excel': False,
            'image_saved': False,
            'image_path': None,
            'needs_review': False,
            'warped_image': None,
            'detection_result': None,
            'overlay_image': None
        }

        try:
            # Paso 1: Convertir PDF a imagen
            image = self.pdf_processor.pdf_to_image(pdf_path)
            if image is None:
                result['message'] = "Error al convertir PDF a imagen"
                return result

            # Paso 2: Detectar ArUco y corregir perspectiva
            process_result = self.image_processor.process_answer_sheet(image)
            if not process_result['success']:
                result['message'] = process_result['message']
                return result

            # Paso 3: Detección OMR
            detection_result = self.omr_detector.detect_answer_sheet(
                process_result['preprocessed']
            )

            # Guardar datos necesarios para revisión manual
            result['warped_image'] = process_result['warped_image']
            result['detection_result'] = detection_result

            # Extraer matrícula
            result['matricula'] = detection_result['matricula'].get('matricula', 'N/A')
            result['respuestas'] = detection_result['respuestas'].get('respuestas', {})
            result['confidence'] = detection_result.get('overall_confidence', 0.0)

            # Verificar si necesita revisión manual (confianza < 99%)
            CONFIDENCE_THRESHOLD = 99.0
            result['needs_review'] = result['confidence'] < CONFIDENCE_THRESHOLD

            # Paso 4: Generar y guardar imagen con overlay visual
            try:
                # Generar overlay visual
                overlay = self.omr_detector.create_visual_overlay(
                    process_result['warped_image'],
                    detection_result,
                    answer_key=self.app_data.get('answer_key')
                )

                # Guardar overlay en result (necesario para revisión manual)
                result['overlay_image'] = overlay

                # Determinar dónde guardar la imagen
                if self.app_data.get('excel_handler'):
                    # Guardar en la misma carpeta que el Excel
                    excel_path = self.app_data['excel_handler'].filepath
                    output_dir = Path(excel_path).parent
                else:
                    # Guardar en la carpeta del PDF si no hay Excel configurado
                    output_dir = Path(pdf_path).parent

                # Crear nombre de archivo: {matricula}_{nombre_prueba}.jpg
                test_name = self.app_data.get('test_name', 'Prueba')
                # Limpiar nombre de prueba para que sea válido en sistema de archivos
                safe_test_name = "".join(c for c in test_name if c.isalnum() or c in (' ', '_', '-')).strip()
                image_filename = f"{result['matricula']}_{safe_test_name}.jpg"
                image_path = output_dir / image_filename

                # Guardar la ruta para usar después
                result['image_path'] = str(image_path)

                # IMPORTANTE: Solo guardar imagen si NO necesita revisión manual
                # Si necesita revisión, la imagen se guardará DESPUÉS de las correcciones
                if not result['needs_review']:
                    cv2.imwrite(str(image_path), overlay)
                    result['image_saved'] = True
                else:
                    # No guardar todavía, se guardará después de la revisión manual
                    result['image_saved'] = False

            except Exception as e:
                # Si falla el guardado de imagen, continuar con el procesamiento
                result['image_saved'] = False
                result['image_path'] = None
                print(f"⚠️ Error al guardar imagen overlay: {e}")

            # Paso 5: Calificar si hay pauta
            if self.app_data.get('answer_key'):
                # Comparar respuestas con la pauta
                answer_key = self.app_data['answer_key']
                correctas = 0
                incorrectas = 0

                for pregunta, respuesta in result['respuestas'].items():
                    if respuesta is None:
                        continue  # Pregunta sin responder

                    if pregunta in answer_key:
                        if respuesta == answer_key[pregunta]:
                            correctas += 1
                        else:
                            incorrectas += 1

                result['correctas'] = correctas
                result['incorrectas'] = incorrectas

                # Calcular nota usando GradeCalculator
                num_questions = self.app_data.get('num_questions', 100)
                grade_calc = GradeCalculator(
                    max_score=num_questions,
                    passing_percentage=self.app_data.get('passing_percentage', 60.0),
                    min_grade=self.app_data.get('min_grade', 1.0),
                    max_grade=self.app_data.get('max_grade', 7.0),
                    passing_grade=self.app_data.get('passing_grade', 4.0)
                )

                result['nota'] = grade_calc.calculate_grade(correctas)

                # Paso 6: Guardar en Excel si está configurado
                # NO guardar si necesita revisión manual (confianza < 99%)
                if self.app_data.get('excel_handler') and result['matricula'] != 'N/A':
                    if not result['needs_review']:
                        # Solo guardar si la confianza es >= 99%
                        excel_handler = self.app_data['excel_handler']
                        save_result = excel_handler.save_grade(
                            matricula=result['matricula'],
                            grade=result['nota'],
                            test_name=self.app_data.get('test_name', 'Prueba')
                        )
                        result['saved_to_excel'] = save_result['success']
                        if not save_result['success']:
                            result['message'] = save_result['message']
                    else:
                        # Marcar que no se guardó porque necesita revisión
                        result['saved_to_excel'] = False
                        result['message'] = 'Requiere revisión manual (confianza < 99%)'

            result['success'] = True
            if result['needs_review']:
                result['message'] = "Procesado - Requiere revisión manual"
            else:
                result['message'] = "Procesado exitosamente"

        except Exception as e:
            result['message'] = f"Error: {str(e)}"

        return result

    def append_result(self, result: Dict):
        """Agrega un resultado al área de texto"""
        # Determinar emoji de estado
        if not result['success']:
            status = "❌"
        elif result.get('needs_review'):
            status = "⚠️"  # Advertencia para hojas que necesitan revisión
        else:
            status = "✅"

        text = f"\n{'='*80}\n"
        text += f"{status} {result['filename']}\n"
        text += f"{'='*80}\n"

        if result['success']:
            text += f"Matrícula: {result['matricula']}\n"
            text += f"Confianza: {result['confidence']:.1f}%\n"

            # Indicar si necesita revisión
            if result.get('needs_review'):
                text += "⚠️ REQUIERE REVISIÓN MANUAL (confianza < 99%)\n"

            if result['nota'] > 0:
                text += f"Correctas: {result['correctas']} | " \
                       f"Incorrectas: {result['incorrectas']}\n"
                text += f"Nota: {result['nota']:.1f}\n"

                if result['saved_to_excel']:
                    text += "💾 Guardado en Excel\n"
                else:
                    text += f"⚠️ No guardado: {result['message']}\n"

            # Mostrar información de imagen guardada
            if result.get('image_saved'):
                image_name = Path(result['image_path']).name
                # Indicar si fue guardada después de revisión manual
                if 'revisión manual' in result.get('message', ''):
                    text += f"🖼️ Imagen guardada (con correcciones manuales): {image_name}\n"
                else:
                    text += f"🖼️ Imagen guardada: {image_name}\n"
            elif result.get('needs_review') and result.get('image_path'):
                # Tiene ruta pero no se guardó porque necesita revisión
                text += f"🖼️ Imagen pendiente (se guardará después de revisión manual)\n"
        else:
            text += f"❌ Error: {result['message']}\n"

        self.results_text.insert("end", text)
        self.results_text.see("end")  # Scroll al final

    def finish_processing(self):
        """Finaliza el procesamiento y muestra resumen"""
        self.processing = False

        # Habilitar controles
        self.load_files_btn.configure(state="normal")
        self.load_folder_btn.configure(state="normal")
        self.clear_queue_btn.configure(state="normal")

        # Verificar si quedan PDFs pendientes
        pending = [item for item in self.pdf_queue if item['status'] == 'pending']
        if pending:
            self.process_btn.configure(state="normal")

        # Mostrar resumen
        total = len(self.current_results)
        successful = sum(1 for r in self.current_results if r['success'])
        failed = total - successful

        summary = f"\n{'='*80}\n"
        summary += "RESUMEN FINAL\n"
        summary += f"{'='*80}\n"
        summary += f"Total procesados: {total}\n"
        summary += f"Exitosos: {successful}\n"
        summary += f"Con errores: {failed}\n"

        if self.app_data.get('answer_key'):
            saved = sum(1 for r in self.current_results if r.get('saved_to_excel'))
            summary += f"Guardados en Excel: {saved}\n"

        # Información de imágenes guardadas
        images_saved = sum(1 for r in self.current_results if r.get('image_saved'))
        if images_saved > 0:
            summary += f"Imágenes con overlay guardadas: {images_saved}\n"

        # Verificar si hay hojas que necesitan revisión manual
        sheets_needing_review = [
            {
                'result': r,
                'warped_image': r.get('warped_image'),
                'detection_result': r.get('detection_result'),
                'overlay_image': r.get('overlay_image')
            }
            for r in self.current_results
            if r.get('success') and r.get('needs_review')
        ]

        if sheets_needing_review:
            summary += f"\n⚠️ Hojas que requieren revisión manual: {len(sheets_needing_review)}\n"

        self.results_text.insert("end", summary)
        self.status_label.configure(text="✅ Procesamiento completado")

        # Mostrar mensaje inicial
        msg = f"Procesamiento finalizado\n\nExitosos: {successful}/{total}\nCon errores: {failed}/{total}"

        if sheets_needing_review:
            msg += f"\n\n⚠️ {len(sheets_needing_review)} hoja(s) requieren revisión manual\n(confianza < 99%)"

            result = messagebox.askyesnocancel(
                "Completado",
                msg + "\n\n¿Deseas revisar las hojas ahora?",
                icon='warning'
            )

            if result:  # Si presiona "Sí"
                self.open_manual_review(sheets_needing_review)
        else:
            messagebox.showinfo("Completado", msg)

    def open_manual_review(self, sheets_to_review: List[Dict]):
        """Abre la ventana de revisión manual"""
        try:
            # Crear ventana de revisión manual
            review_window = ManualReviewWindow(
                parent=self.parent,
                sheets_to_review=sheets_to_review,
                omr_detector=self.omr_detector,
                app_data=self.app_data,
                on_save_callback=self.save_reviewed_sheet
            )

            # Esperar a que se cierre la ventana
            self.parent.wait_window(review_window)

            # Actualizar resultados después de la revisión
            self.update_results_after_review()

        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir ventana de revisión: {e}")

    def save_reviewed_sheet(self, sheet: Dict) -> bool:
        """
        Callback para guardar una hoja después de revisión manual

        Args:
            sheet: Diccionario con información de la hoja revisada

        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            result = sheet['result']

            # Guardar en Excel
            if self.app_data.get('excel_handler') and result['matricula'] != 'N/A':
                excel_handler = self.app_data['excel_handler']
                save_result = excel_handler.save_grade(
                    matricula=result['matricula'],
                    grade=result['nota'],
                    test_name=self.app_data.get('test_name', 'Prueba')
                )

                if save_result['success']:
                    # Actualizar resultado
                    result['saved_to_excel'] = True
                    result['needs_review'] = False
                    result['message'] = 'Guardado después de revisión manual'
                    return True
                else:
                    messagebox.showerror("Error al guardar",
                                       f"No se pudo guardar en Excel:\n{save_result['message']}")
                    return False

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar hoja revisada: {e}")
            return False

    def update_results_after_review(self):
        """Actualiza la visualización de resultados después de la revisión manual"""
        # Contar hojas guardadas después de revisión
        reviewed_saved = sum(1 for r in self.current_results
                           if r.get('success') and not r.get('needs_review')
                           and 'revisión manual' in r.get('message', ''))

        if reviewed_saved > 0:
            summary = f"\n{'='*80}\n"
            summary += "ACTUALIZACIÓN POST-REVISIÓN\n"
            summary += f"{'='*80}\n"
            summary += f"Hojas guardadas después de revisión manual: {reviewed_saved}\n"
            summary += f"{'='*80}\n"

            self.results_text.insert("end", summary)
            self.results_text.see("end")
