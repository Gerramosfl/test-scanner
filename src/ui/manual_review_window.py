"""
Ventana de revisión manual para corregir respuestas ambiguas o con baja confianza
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Callable


class ManualReviewWindow(ctk.CTkToplevel):
    """
    Ventana modal para revisar y corregir manualmente hojas con baja confianza
    """

    def __init__(self, parent, sheets_to_review: List[Dict],
                 omr_detector, app_data, on_save_callback: Optional[Callable] = None):
        """
        Inicializa la ventana de revisión manual

        Args:
            parent: Ventana padre
            sheets_to_review: Lista de hojas que necesitan revisión
            omr_detector: Instancia de OMRDetector para obtener posiciones de círculos
            app_data: Datos de la aplicación (pauta, Excel, etc.)
            on_save_callback: Función a llamar cuando se guarda una hoja
        """
        super().__init__(parent)

        self.sheets_to_review = sheets_to_review
        self.current_index = 0
        self.omr_detector = omr_detector
        self.app_data = app_data
        self.on_save_callback = on_save_callback

        # Configuración de la ventana
        self.title("Revisión Manual de Hojas")
        self.geometry("1200x800")

        # Hacer la ventana redimensionable y con botones min/max
        self.resizable(True, True)

        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()

        # Variables de edición
        self.edited_matricula = None
        self.edited_respuestas = {}

        # Track de círculos dibujados manualmente por el usuario
        self.manual_circles = []  # Lista de círculos verdes dibujados por el usuario

        # Factor de escala para la imagen
        self.scale_factor = 1.0
        self.display_width = 1100  # Ancho deseado para la imagen

        # Crear interfaz
        self.create_widgets()

        # Cargar primera hoja
        self.load_current_sheet()

    def create_widgets(self):
        """Crea todos los widgets de la ventana"""

        # ===== ENCABEZADO =====
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(header_frame,
                                        text="",
                                        font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=5)

        # ===== INFORMACIÓN DE LA HOJA =====
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=5)

        # Matrícula
        matricula_frame = ctk.CTkFrame(info_frame)
        matricula_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(matricula_frame, text="Matrícula detectada:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)

        self.matricula_entry = ctk.CTkEntry(matricula_frame, width=150,
                                           font=ctk.CTkFont(size=14))
        self.matricula_entry.pack(side="left", padx=5)

        # Confianza
        self.confidence_label = ctk.CTkLabel(info_frame, text="",
                                            font=ctk.CTkFont(size=12))
        self.confidence_label.pack(pady=5)

        # ===== ÁREA DE IMAGEN =====
        image_frame = ctk.CTkFrame(self)
        image_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas con scrollbars para la imagen
        self.canvas = ctk.CTkCanvas(image_frame, bg="gray20", highlightthickness=0)

        h_scrollbar = ctk.CTkScrollbar(image_frame, orientation="horizontal",
                                       command=self.canvas.xview)
        v_scrollbar = ctk.CTkScrollbar(image_frame, orientation="vertical",
                                       command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=h_scrollbar.set,
                             yscrollcommand=v_scrollbar.set)

        h_scrollbar.pack(side="bottom", fill="x")
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bind click en canvas
        self.canvas.bind("<Button-1>", self.on_image_click)

        # Bind scroll con rueda del ratón
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)

        # ===== PANEL DE CORRECCIÓN RÁPIDA =====
        correction_frame = ctk.CTkFrame(self)
        correction_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(correction_frame, text="Corrección rápida:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

        ctk.CTkLabel(correction_frame, text="Pregunta:").pack(side="left", padx=5)
        self.question_entry = ctk.CTkEntry(correction_frame, width=60)
        self.question_entry.pack(side="left", padx=5)

        ctk.CTkLabel(correction_frame, text="Respuesta:").pack(side="left", padx=5)

        # Radio buttons para respuestas
        self.answer_var = ctk.StringVar(value="")
        for alt in ["A", "B", "C", "D", "E"]:
            ctk.CTkRadioButton(correction_frame, text=alt, variable=self.answer_var,
                              value=alt, command=self.on_quick_correction).pack(side="left", padx=2)

        ctk.CTkButton(correction_frame, text="Aplicar", width=80,
                     command=self.apply_quick_correction).pack(side="left", padx=10)

        # Botón para limpiar respuesta
        ctk.CTkButton(correction_frame, text="Limpiar Respuesta", width=120,
                     command=self.clear_answer, fg_color="orange",
                     hover_color="darkorange").pack(side="left", padx=5)

        # ===== INSTRUCCIONES =====
        instruction_frame = ctk.CTkFrame(self)
        instruction_frame.pack(fill="x", padx=10, pady=5)

        instructions = ("💡 Instrucciones: Haz click en los círculos de la imagen para marcar/desmarcar respuestas. "
                       "O usa la corrección rápida ingresando número de pregunta y seleccionando la respuesta.")
        ctk.CTkLabel(instruction_frame, text=instructions,
                    font=ctk.CTkFont(size=11), wraplength=1100).pack(pady=5)

        # ===== BOTONES DE NAVEGACIÓN =====
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(fill="x", padx=10, pady=10)

        self.prev_btn = ctk.CTkButton(nav_frame, text="◄ Anterior", width=120,
                                     command=self.go_previous)
        self.prev_btn.pack(side="left", padx=10)

        self.skip_btn = ctk.CTkButton(nav_frame, text="Omitir", width=120,
                                     command=self.skip_current,
                                     fg_color="gray", hover_color="darkgray")
        self.skip_btn.pack(side="left", padx=10)

        self.save_btn = ctk.CTkButton(nav_frame, text="Guardar y Continuar", width=180,
                                     command=self.save_and_continue,
                                     fg_color="green", hover_color="darkgreen")
        self.save_btn.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(nav_frame, text="Siguiente ►", width=120,
                                     command=self.go_next)
        self.next_btn.pack(side="left", padx=10)

        # Botón cerrar
        ctk.CTkButton(nav_frame, text="Cerrar", width=120,
                     command=self.close_window,
                     fg_color="red", hover_color="darkred").pack(side="right", padx=10)

    def load_current_sheet(self):
        """Carga la hoja actual en la interfaz"""
        if not self.sheets_to_review or self.current_index >= len(self.sheets_to_review):
            self.close_window()
            return

        sheet = self.sheets_to_review[self.current_index]

        # Actualizar título
        total = len(self.sheets_to_review)
        self.title_label.configure(
            text=f"Revisión Manual - Hoja {self.current_index + 1} de {total}"
        )

        # Cargar matrícula
        self.edited_matricula = sheet['result']['matricula']
        self.matricula_entry.delete(0, "end")
        self.matricula_entry.insert(0, self.edited_matricula)

        # Cargar respuestas (hacer una copia para editar)
        self.edited_respuestas = sheet['result']['respuestas'].copy()

        # Limpiar círculos manuales anteriores
        self.manual_circles = []

        # Mostrar confianza
        confidence = sheet['result']['confidence']
        self.confidence_label.configure(
            text=f"Confianza de detección: {confidence:.1f}% (< 99% - Requiere revisión)"
        )

        # Cargar y mostrar imagen
        self.load_image(sheet)

        # Actualizar estado de botones
        self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_index < total - 1 else "disabled")

    def load_image(self, sheet: Dict):
        """Carga la imagen de overlay en el canvas - solo muestra detecciones en verde"""
        try:
            # Obtener la imagen warped original
            warped_image = sheet.get('warped_image')

            if warped_image is None:
                messagebox.showerror("Error", "No se pudo cargar la imagen de la hoja")
                return

            # Generar overlay de REVISIÓN (solo círculos verdes en detecciones, sin comparar con pauta)
            review_overlay = self.create_review_overlay(
                warped_image,
                sheet['detection_result']
            )

            # Guardar imagen original (sin escalar) para generar overlay final
            self.current_image_bgr = review_overlay

            # Calcular factor de escala para ajustar imagen a la ventana
            original_height, original_width = review_overlay.shape[:2]
            self.scale_factor = self.display_width / original_width

            # Redimensionar imagen para visualización
            new_width = int(original_width * self.scale_factor)
            new_height = int(original_height * self.scale_factor)
            resized_image = cv2.resize(review_overlay, (new_width, new_height),
                                      interpolation=cv2.INTER_AREA)

            # Convertir BGR a RGB
            image_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)

            # Convertir a PIL Image
            pil_image = Image.fromarray(image_rgb)
            self.current_pil_image = pil_image

            # Convertir a PhotoImage para tkinter
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # Actualizar canvas
            self.canvas.delete("all")
            self.image_id = self.canvas.create_image(0, 0, anchor="nw",
                                                     image=self.photo_image)

            # Configurar región de scroll
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar imagen: {e}")

    def create_review_overlay(self, warped_image, detection_result):
        """
        Crea overlay de REVISIÓN mostrando solo círculos verdes en detecciones automáticas
        NO compara con la pauta, NO muestra colores de corrección
        """
        # Copiar imagen para no modificar la original
        overlay = warped_image.copy()

        # Color verde para todas las detecciones
        COLOR_DETECTED = (0, 255, 0)  # Verde

        calibration = self.omr_detector.calibration_data

        # ===== DIBUJAR MATRÍCULA DETECTADA =====
        matricula_circles = calibration['matricula']
        matricula_detection = detection_result['matricula']
        matricula_str = matricula_detection.get('matricula', '')
        matricula_details = matricula_detection.get('details', {})

        if len(matricula_str) == 10:
            for col_idx, digito_char in enumerate(matricula_str):
                try:
                    digito = int(digito_char)
                    col_num = col_idx + 1
                    col_key = f'col_{col_num}'

                    # Encontrar el círculo correspondiente
                    matching_circle = next(
                        (c for c in matricula_circles
                         if c['columna'] == col_num and c['digito'] == digito),
                        None
                    )

                    if matching_circle:
                        # Dibujar círculo verde
                        cv2.circle(
                            overlay,
                            (matching_circle['x'], matching_circle['y']),
                            matching_circle['radius'],
                            COLOR_DETECTED,
                            2
                        )
                except ValueError:
                    continue

        # ===== DIBUJAR RESPUESTAS DETECTADAS =====
        respuestas_circles = calibration['respuestas']
        respuestas_detected = detection_result['respuestas'].get('respuestas', {})
        respuestas_details = detection_result['respuestas'].get('details', {})

        for pregunta, alternativa in respuestas_detected.items():
            if alternativa is None:
                continue

            detail = respuestas_details.get(pregunta, {})
            status = detail.get('status', '')

            # Solo dibujar si no es 'empty' o 'multiple'
            if status == 'empty':
                continue
            elif status == 'multiple':
                # En múltiples marcas, dibujar todas las alternativas detectadas en verde
                marked_alternatives = detail.get('marked_alternatives', [])
                for alt in marked_alternatives:
                    matching_circle = next(
                        (c for c in respuestas_circles
                         if c['pregunta'] == pregunta and c['alternativa'] == alt),
                        None
                    )
                    if matching_circle:
                        cv2.circle(
                            overlay,
                            (matching_circle['x'], matching_circle['y']),
                            matching_circle['radius'],
                            COLOR_DETECTED,
                            2
                        )
            else:
                # Respuesta detectada normalmente - dibujar en verde
                matching_circle = next(
                    (c for c in respuestas_circles
                     if c['pregunta'] == pregunta and c['alternativa'] == alternativa),
                    None
                )
                if matching_circle:
                    cv2.circle(
                        overlay,
                        (matching_circle['x'], matching_circle['y']),
                        matching_circle['radius'],
                        COLOR_DETECTED,
                        2
                    )

        return overlay

    def on_mousewheel(self, event):
        """Maneja el scroll vertical con la rueda del ratón"""
        # En Windows, event.delta es positivo para arriba, negativo para abajo
        # Dividir por 120 para normalizar (Windows usa múltiplos de 120)
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_shift_mousewheel(self, event):
        """Maneja el scroll horizontal con Shift + rueda del ratón"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def draw_permanent_circle(self, x, y, radius):
        """Dibuja un círculo verde PERMANENTE en el canvas"""
        # Escalar coordenadas según el factor de escala de la imagen
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        scaled_radius = int(radius * self.scale_factor)

        # Dibujar círculo verde permanente
        circle_id = self.canvas.create_oval(
            scaled_x - scaled_radius,
            scaled_y - scaled_radius,
            scaled_x + scaled_radius,
            scaled_y + scaled_radius,
            outline="green",
            width=3,
            tags="manual_circle"
        )

        # Guardar en la lista de círculos manuales
        self.manual_circles.append({
            'id': circle_id,
            'x': x,  # Coordenadas originales (sin escalar)
            'y': y,
            'radius': radius
        })

    def on_image_click(self, event):
        """Maneja clicks en la imagen para seleccionar respuestas o matrícula"""
        # Obtener coordenadas del click en el canvas (considerando scroll)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Convertir a coordenadas de imagen original (sin escala)
        image_x = int(canvas_x / self.scale_factor)
        image_y = int(canvas_y / self.scale_factor)

        calibration = self.omr_detector.calibration_data

        # Primero verificar si el click fue en un círculo de matrícula
        matricula_circles = calibration['matricula']
        clicked_matricula = None
        min_distance_matricula = float('inf')

        for circle in matricula_circles:
            x, y = circle['x'], circle['y']
            radius = circle['radius']

            # Calcular distancia del click al centro del círculo (en coordenadas originales)
            distance = np.sqrt((image_x - x)**2 + (image_y - y)**2)

            # Si está dentro del círculo y es el más cercano
            if distance <= radius * 1.5 and distance < min_distance_matricula:
                clicked_matricula = circle
                min_distance_matricula = distance

        if clicked_matricula:
            # Usuario hizo click en un círculo de matrícula
            columna = clicked_matricula['columna']
            digito = clicked_matricula['digito']

            # Dibujar círculo verde PERMANENTE
            self.draw_permanent_circle(clicked_matricula['x'], clicked_matricula['y'],
                                      clicked_matricula['radius'])

            # Actualizar matrícula
            # Convertir matrícula actual a lista de dígitos
            matricula_list = list(self.edited_matricula) if len(self.edited_matricula) == 10 else ['0'] * 10

            # Actualizar el dígito en la columna correspondiente (columna empieza en 1)
            matricula_list[columna - 1] = str(digito)

            # Convertir de vuelta a string
            self.edited_matricula = ''.join(matricula_list)

            # Actualizar entry
            self.matricula_entry.delete(0, "end")
            self.matricula_entry.insert(0, self.edited_matricula)

            # Mostrar feedback
            self.show_feedback(f"Matrícula col {columna}: {digito}")
            return

        # Si no fue click en matrícula, buscar en círculos de respuesta
        respuestas_circles = calibration['respuestas']
        clicked_circle = None
        min_distance = float('inf')

        for circle in respuestas_circles:
            x, y = circle['x'], circle['y']
            radius = circle['radius']

            # Calcular distancia del click al centro del círculo (en coordenadas originales)
            distance = np.sqrt((image_x - x)**2 + (image_y - y)**2)

            # Si está dentro del círculo y es el más cercano
            if distance <= radius * 1.5 and distance < min_distance:
                clicked_circle = circle
                min_distance = distance

        if clicked_circle:
            # Usuario hizo click en un círculo de respuesta
            pregunta = clicked_circle['pregunta']
            alternativa = clicked_circle['alternativa']

            # Dibujar círculo verde PERMANENTE
            self.draw_permanent_circle(clicked_circle['x'], clicked_circle['y'],
                                      clicked_circle['radius'])

            # Actualizar respuesta
            self.edited_respuestas[pregunta] = alternativa

            # Mostrar feedback
            self.show_feedback(f"P{pregunta}: {alternativa}")

    def generate_final_overlay(self, sheet: Dict):
        """
        Genera el overlay FINAL con comparación de pauta y colores de corrección
        Solo se llama al guardar, NO durante la edición
        """
        try:
            # Actualizar details de respuestas para incluir correcciones manuales
            original_details = sheet['detection_result']['respuestas'].get('details', {})
            updated_details = {}

            # Para cada respuesta editada, crear o actualizar su detail
            for pregunta, respuesta in self.edited_respuestas.items():
                if pregunta in original_details:
                    # Si ya existía, actualizar
                    updated_details[pregunta] = original_details[pregunta].copy()
                    updated_details[pregunta]['manually_corrected'] = True
                    updated_details[pregunta]['alternativa'] = respuesta
                else:
                    # Si no existía (fue agregada manualmente), crear detail nuevo
                    # IMPORTANTE: Usar 'status': 'ok' para que create_visual_overlay dibuje el círculo
                    updated_details[pregunta] = {
                        'status': 'ok',  # Estado OK para que se dibuje correctamente
                        'alternativa': respuesta,  # Alternativa seleccionada
                        'confidence': 100.0,   # Alta confianza (corrección manual)
                        'manually_corrected': True,
                        'fill_percentage': 100.0,  # Completamente marcado (manual)
                        'difference': 100.0  # Diferencia máxima (manual)
                    }

            # Copiar detalles de preguntas no editadas
            for pregunta, detail in original_details.items():
                if pregunta not in updated_details:
                    updated_details[pregunta] = detail

            # Actualizar matrícula y sus detalles
            matricula_detection = sheet['detection_result']['matricula'].copy()
            matricula_detection['matricula'] = self.edited_matricula

            # Crear detalles de matrícula para visualización
            original_matricula_details = matricula_detection.get('details', {})
            matricula_details = {}

            # Para cada columna de la matrícula, crear o actualizar su detail
            if len(self.edited_matricula) == 10:
                for col_idx, digito_char in enumerate(self.edited_matricula):
                    col_num = col_idx + 1  # Columnas empiezan en 1
                    col_key = f'col_{col_num}'

                    try:
                        digito = int(digito_char)
                        # Verificar si este dígito fue corregido manualmente
                        is_corrected = (col_key not in original_matricula_details or
                                      original_matricula_details[col_key].get('digito') != digito)

                        matricula_details[col_key] = {
                            'digito': digito,
                            'confidence': 100.0,
                            'manually_corrected': is_corrected,
                            'fill_percentage': 100.0 if is_corrected else original_matricula_details.get(col_key, {}).get('fill_percentage', 100.0),
                            'difference': 100.0 if is_corrected else original_matricula_details.get(col_key, {}).get('difference', 100.0)
                        }
                    except ValueError:
                        # Si el carácter no es un dígito, mantener el original si existe
                        if col_key in original_matricula_details:
                            matricula_details[col_key] = original_matricula_details[col_key]

                matricula_detection['details'] = matricula_details

            if self.edited_matricula != sheet['result']['matricula']:
                matricula_detection['manually_corrected'] = True

            # Crear detection_result modificado con respuestas editadas
            detection_result = {
                'matricula': matricula_detection,
                'respuestas': {
                    'respuestas': self.edited_respuestas.copy(),
                    'details': updated_details,
                    'confidence': 100.0,  # Alta confianza por corrección manual
                    'success': True
                },
                'overall_confidence': 100.0,  # Alta confianza por corrección manual
                'success': True
            }

            # Generar overlay final con comparación de pauta
            overlay = self.omr_detector.create_visual_overlay(
                sheet['warped_image'],
                detection_result,
                answer_key=self.app_data.get('answer_key')
            )

            return overlay

        except Exception as e:
            print(f"Error al generar overlay final: {e}")
            return None

    def show_feedback(self, message: str):
        """Muestra mensaje temporal de feedback"""
        # Actualizar label de confianza temporalmente
        original_text = self.confidence_label.cget("text")
        self.confidence_label.configure(text=f"✓ Actualizado: {message}")

        # Restaurar después de 2 segundos
        self.after(2000, lambda: self.confidence_label.configure(text=original_text))

    def on_quick_correction(self):
        """Callback cuando se selecciona una respuesta en corrección rápida"""
        pass  # Solo para actualizar el radio button

    def apply_quick_correction(self):
        """Aplica la corrección rápida ingresada manualmente"""
        try:
            question_str = self.question_entry.get().strip()
            if not question_str:
                messagebox.showwarning("Advertencia", "Ingresa el número de pregunta")
                return

            question = int(question_str)
            answer = self.answer_var.get()

            if not answer:
                messagebox.showwarning("Advertencia", "Selecciona una respuesta")
                return

            # Verificar que la pregunta esté en rango
            num_questions = self.app_data.get('num_questions', 100)
            if question < 1 or question > num_questions:
                messagebox.showerror("Error",
                                   f"Pregunta debe estar entre 1 y {num_questions}")
                return

            # Actualizar respuesta
            self.edited_respuestas[question] = answer

            # Buscar el círculo correspondiente y dibujarlo
            calibration = self.omr_detector.calibration_data
            respuestas_circles = calibration['respuestas']
            matching_circle = next(
                (c for c in respuestas_circles
                 if c['pregunta'] == question and c['alternativa'] == answer),
                None
            )

            if matching_circle:
                # Dibujar círculo verde permanente
                self.draw_permanent_circle(matching_circle['x'], matching_circle['y'],
                                          matching_circle['radius'])

            # Limpiar campos
            self.question_entry.delete(0, "end")
            self.answer_var.set("")

            # Mostrar feedback
            self.show_feedback(f"P{question}: {answer}")

        except ValueError:
            messagebox.showerror("Error", "Número de pregunta inválido")

    def clear_answer(self):
        """Limpia/elimina una respuesta"""
        try:
            question_str = self.question_entry.get().strip()
            if not question_str:
                messagebox.showwarning("Advertencia", "Ingresa el número de pregunta")
                return

            question = int(question_str)

            # Eliminar respuesta
            if question in self.edited_respuestas:
                del self.edited_respuestas[question]

                # Buscar y eliminar círculos manuales de esta pregunta
                calibration = self.omr_detector.calibration_data
                respuestas_circles = calibration['respuestas']

                # Encontrar todos los círculos de esta pregunta
                question_circles = [c for c in respuestas_circles if c['pregunta'] == question]

                # Eliminar círculos manuales que coincidan
                for qc in question_circles:
                    for mc in self.manual_circles[:]:  # Iterar sobre copia
                        # Verificar si las coordenadas coinciden aproximadamente
                        if abs(mc['x'] - qc['x']) < 5 and abs(mc['y'] - qc['y']) < 5:
                            # Eliminar del canvas
                            self.canvas.delete(mc['id'])
                            # Eliminar de la lista
                            self.manual_circles.remove(mc)

                self.show_feedback(f"P{question}: Respuesta eliminada")
            else:
                messagebox.showinfo("Info", "Esa pregunta no tiene respuesta")

        except ValueError:
            messagebox.showerror("Error", "Número de pregunta inválido")

    def save_and_continue(self):
        """Guarda la hoja actual y continúa con la siguiente"""
        # Obtener matrícula editada
        new_matricula = self.matricula_entry.get().strip()

        # Validar matrícula
        if not new_matricula or len(new_matricula) != 10:
            if not messagebox.askyesno("Matrícula inválida",
                                      "La matrícula no tiene 10 dígitos. ¿Continuar de todos modos?"):
                return

        # Validar que la matrícula solo contenga dígitos (para nombre de archivo)
        if not new_matricula.isdigit():
            messagebox.showerror("Error",
                               "La matrícula debe contener solo dígitos (0-9)\n"
                               "Por favor corrige la matrícula antes de guardar.")
            return

        # Actualizar matrícula editada
        self.edited_matricula = new_matricula

        # Actualizar resultado
        sheet = self.sheets_to_review[self.current_index]
        sheet['result']['matricula'] = new_matricula
        sheet['result']['respuestas'] = self.edited_respuestas.copy()

        # IMPORTANTE: Actualizar image_path con la nueva matrícula corregida
        # Esto es crítico para que el archivo se guarde con el nombre correcto
        old_image_path = sheet['result'].get('image_path')
        if old_image_path:
            # Reconstruir el path con la nueva matrícula
            from pathlib import Path
            old_path = Path(old_image_path)
            output_dir = old_path.parent

            # Obtener el nombre de prueba del path original
            # Formato: {matricula}_{test_name}.jpg o {matricula}_{test_name}_pX.jpg
            old_filename = old_path.stem  # nombre sin extensión

            # Extraer la parte después del primer "_" (que es el nombre de prueba)
            parts = old_filename.split('_', 1)
            if len(parts) > 1:
                test_part = parts[1]  # Esto puede ser "test2" o "test2_p1"
                new_filename = f"{new_matricula}_{test_part}.jpg"
            else:
                # Fallback: usar solo la matrícula
                new_filename = f"{new_matricula}.jpg"

            new_image_path = output_dir / new_filename
            sheet['result']['image_path'] = str(new_image_path)

            print(f"📝 Ruta de imagen actualizada:")
            print(f"   Antigua: {old_image_path}")
            print(f"   Nueva:   {new_image_path}")

        # Recalcular nota
        self.recalculate_grade(sheet)

        # IMPORTANTE: Generar overlay FINAL con comparación de pauta
        final_overlay = self.generate_final_overlay(sheet)

        if final_overlay is None:
            messagebox.showerror("Error", "No se pudo generar el overlay final")
            return

        # Actualizar la imagen actual con el overlay final
        self.current_image_bgr = final_overlay

        # Guardar en Excel
        if self.on_save_callback:
            success = self.on_save_callback(sheet)
            if not success:
                messagebox.showerror("Error", "No se pudo guardar en Excel")
                return

        # Guardar imagen actualizada (con todas las correcciones visualizadas)
        self.save_updated_image(sheet)

        # Marcar como revisada
        sheet['reviewed'] = True

        messagebox.showinfo("Guardado",
                          f"Hoja guardada exitosamente\n"
                          f"Matrícula: {new_matricula}\n"
                          f"Nota: {sheet['result']['nota']:.1f}")

        # Ir a siguiente hoja o cerrar
        if self.current_index < len(self.sheets_to_review) - 1:
            self.current_index += 1
            self.load_current_sheet()
        else:
            messagebox.showinfo("Completado", "Todas las hojas han sido revisadas")
            self.close_window()

    def recalculate_grade(self, sheet: Dict):
        """Recalcula la nota basándose en las respuestas editadas"""
        if not self.app_data.get('answer_key'):
            return

        answer_key = self.app_data['answer_key']
        correctas = 0
        incorrectas = 0

        for pregunta, respuesta in sheet['result']['respuestas'].items():
            if respuesta is None:
                continue

            if pregunta in answer_key:
                if respuesta == answer_key[pregunta]:
                    correctas += 1
                else:
                    incorrectas += 1

        sheet['result']['correctas'] = correctas
        sheet['result']['incorrectas'] = incorrectas

        # Calcular nota
        from src.core.grade_calculator import GradeCalculator

        grade_calc = GradeCalculator(
            max_score=self.app_data.get('num_questions', 100),
            passing_percentage=self.app_data.get('passing_percentage', 60.0),
            min_grade=self.app_data.get('min_grade', 1.0),
            max_grade=self.app_data.get('max_grade', 7.0),
            passing_grade=self.app_data.get('passing_grade', 4.0)
        )

        sheet['result']['nota'] = grade_calc.calculate_grade(correctas)

    def save_updated_image(self, sheet: Dict):
        """Guarda la imagen de overlay actualizada con todas las correcciones"""
        try:
            if sheet['result'].get('image_path'):
                # Guardar la imagen con las correcciones visualizadas
                cv2.imwrite(sheet['result']['image_path'], self.current_image_bgr)
                # Actualizar flag de imagen guardada
                sheet['result']['image_saved'] = True
                print(f"✓ Imagen con correcciones guardada: {sheet['result']['image_path']}")
        except Exception as e:
            sheet['result']['image_saved'] = False
            print(f"❌ Error al guardar imagen actualizada: {e}")

    def skip_current(self):
        """Omite la hoja actual sin guardar"""
        if messagebox.askyesno("Omitir",
                              "¿Estás seguro de omitir esta hoja sin guardar?"):
            sheet = self.sheets_to_review[self.current_index]
            sheet['skipped'] = True

            # Ir a siguiente hoja o cerrar
            if self.current_index < len(self.sheets_to_review) - 1:
                self.current_index += 1
                self.load_current_sheet()
            else:
                messagebox.showinfo("Completado", "Todas las hojas han sido procesadas")
                self.close_window()

    def go_previous(self):
        """Va a la hoja anterior"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_sheet()

    def go_next(self):
        """Va a la siguiente hoja"""
        if self.current_index < len(self.sheets_to_review) - 1:
            self.current_index += 1
            self.load_current_sheet()

    def close_window(self):
        """Cierra la ventana"""
        # Verificar si hay hojas sin revisar
        unreviewed = [s for s in self.sheets_to_review
                     if not s.get('reviewed') and not s.get('skipped')]

        if unreviewed:
            if not messagebox.askyesno("Cerrar",
                                      f"Hay {len(unreviewed)} hoja(s) sin revisar.\n"
                                      "¿Cerrar de todos modos?"):
                return

        self.grab_release()
        self.destroy()
