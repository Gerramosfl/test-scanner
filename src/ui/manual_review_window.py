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

        # ===== INSTRUCCIONES =====
        instruction_frame = ctk.CTkFrame(self)
        instruction_frame.pack(fill="x", padx=10, pady=5)

        instructions = ("💡 Instrucciones: Haz click en los círculos de la imagen para marcar/desmarcar respuestas y matrícula.")
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

        # Cargar respuestas - ahora como diccionario de SETS para soportar múltiples alternativas
        # Formato: {pregunta: set(alternativas)}
        self.edited_respuestas = {}
        for pregunta, alternativa in sheet['result']['respuestas'].items():
            if alternativa is not None:
                # Verificar si es múltiple desde la detección original
                detail = sheet['detection_result']['respuestas'].get('details', {}).get(pregunta, {})
                if detail.get('status') == 'multiple':
                    # Obtener todas las alternativas marcadas
                    marked_alts = detail.get('marked_alternatives', [alternativa])
                    self.edited_respuestas[pregunta] = set(marked_alts)
                else:
                    # Respuesta única
                    self.edited_respuestas[pregunta] = {alternativa}
            else:
                # Sin respuesta
                self.edited_respuestas[pregunta] = set()

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

            # Dibujar círculos iniciales (detecciones + correcciones manuales)
            self.redraw_all_circles()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar imagen: {e}")

    def create_review_overlay(self, warped_image, detection_result):
        """
        Retorna la imagen warped SIN CÍRCULOS
        Los círculos se dibujarán en el canvas usando redraw_all_circles()
        """
        # Simplemente retornar la imagen sin modificar
        # NO dibujar círculos aquí para evitar duplicados
        return warped_image.copy()

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

        # Dibujar círculo verde brillante/fluorescente permanente
        circle_id = self.canvas.create_oval(
            scaled_x - scaled_radius,
            scaled_y - scaled_radius,
            scaled_x + scaled_radius,
            scaled_y + scaled_radius,
            outline="#00FF00",  # Verde brillante/fluorescente (lime green)
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

    def redraw_all_circles(self):
        """Redibuja TODOS los círculos verdes según el estado actual de edited_respuestas y edited_matricula"""
        # Eliminar todos los círculos manuales existentes
        self.canvas.delete("manual_circle")
        self.manual_circles = []

        calibration = self.omr_detector.calibration_data

        # Redibujar círculos de MATRÍCULA
        matricula_circles = calibration['matricula']
        if len(self.edited_matricula) == 10:
            for col_idx, digito_char in enumerate(self.edited_matricula):
                if digito_char == '?':
                    continue  # Saltar columnas sin dígito

                try:
                    digito = int(digito_char)
                    col_num = col_idx + 1

                    # Encontrar el círculo correspondiente
                    matching_circle = next(
                        (c for c in matricula_circles
                         if c['columna'] == col_num and c['digito'] == digito),
                        None
                    )

                    if matching_circle:
                        self.draw_permanent_circle(
                            matching_circle['x'],
                            matching_circle['y'],
                            matching_circle['radius']
                        )
                except ValueError:
                    continue

        # Redibujar círculos de RESPUESTAS
        respuestas_circles = calibration['respuestas']
        for pregunta, alternativas_set in self.edited_respuestas.items():
            for alternativa in alternativas_set:
                # Encontrar el círculo correspondiente
                matching_circle = next(
                    (c for c in respuestas_circles
                     if c['pregunta'] == pregunta and c['alternativa'] == alternativa),
                    None
                )

                if matching_circle:
                    self.draw_permanent_circle(
                        matching_circle['x'],
                        matching_circle['y'],
                        matching_circle['radius']
                    )

    def on_image_click(self, event):
        """Maneja clicks en la imagen para seleccionar/deseleccionar respuestas o matrícula (TOGGLE)"""
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

            # TOGGLE: Verificar si este dígito ya está seleccionado en esta columna
            matricula_list = list(self.edited_matricula) if len(self.edited_matricula) == 10 else ['?'] * 10
            current_digit = matricula_list[columna - 1]

            if current_digit == str(digito):
                # Ya estaba seleccionado → DESMARCAR (poner '?')
                matricula_list[columna - 1] = '?'
                feedback_msg = f"Matrícula col {columna}: Desmarcado"
            else:
                # No estaba seleccionado → MARCAR
                matricula_list[columna - 1] = str(digito)
                feedback_msg = f"Matrícula col {columna}: {digito}"

            # Actualizar matrícula
            self.edited_matricula = ''.join(matricula_list)

            # Actualizar entry
            self.matricula_entry.delete(0, "end")
            self.matricula_entry.insert(0, self.edited_matricula)

            # Redibujar todos los círculos
            self.redraw_all_circles()

            # Mostrar feedback
            self.show_feedback(feedback_msg)
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

            # TOGGLE: Verificar si esta alternativa ya está en el set
            if pregunta not in self.edited_respuestas:
                self.edited_respuestas[pregunta] = set()

            if alternativa in self.edited_respuestas[pregunta]:
                # Ya estaba seleccionada → DESMARCAR (eliminar del set)
                self.edited_respuestas[pregunta].remove(alternativa)
                feedback_msg = f"P{pregunta}: {alternativa} desmarcado"
            else:
                # No estaba seleccionada → MARCAR (agregar al set)
                self.edited_respuestas[pregunta].add(alternativa)
                feedback_msg = f"P{pregunta}: {alternativa} marcado"

            # Redibujar todos los círculos
            self.redraw_all_circles()

            # Mostrar feedback
            self.show_feedback(feedback_msg)

    def generate_final_overlay(self, sheet: Dict):
        """
        Genera el overlay FINAL con comparación de pauta y colores de corrección
        Solo se llama al guardar, NO durante la edición
        """
        try:
            # Actualizar details de respuestas para incluir correcciones manuales
            original_details = sheet['detection_result']['respuestas'].get('details', {})
            updated_details = {}
            final_respuestas = {}  # {pregunta: alternativa o None}

            # Para cada pregunta editada, determinar la respuesta final
            for pregunta, alternativas_set in self.edited_respuestas.items():
                num_alternativas = len(alternativas_set)

                if num_alternativas == 0:
                    # Sin respuesta (se eliminaron todas las marcas)
                    final_respuestas[pregunta] = None
                    updated_details[pregunta] = {
                        'status': 'empty',
                        'alternativa': None,
                        'confidence': 100.0,
                        'manually_corrected': True,
                        'fill_percentage': 0.0,
                        'difference': 0.0
                    }
                elif num_alternativas == 1:
                    # Respuesta única
                    alternativa = list(alternativas_set)[0]
                    final_respuestas[pregunta] = alternativa

                    if pregunta in original_details:
                        # Actualizar detail existente
                        updated_details[pregunta] = original_details[pregunta].copy()
                        updated_details[pregunta]['manually_corrected'] = True
                        updated_details[pregunta]['alternativa'] = alternativa
                        updated_details[pregunta]['status'] = 'ok'
                    else:
                        # Crear detail nuevo
                        updated_details[pregunta] = {
                            'status': 'ok',
                            'alternativa': alternativa,
                            'confidence': 100.0,
                            'manually_corrected': True,
                            'fill_percentage': 100.0,
                            'difference': 100.0
                        }
                else:
                    # Múltiples respuestas (2 o más)
                    # Guardar la primera alternativa como respuesta principal (para compatibilidad)
                    # Pero el detail indicará que son múltiples
                    final_respuestas[pregunta] = list(alternativas_set)[0]

                    updated_details[pregunta] = {
                        'status': 'multiple',
                        'alternativa': list(alternativas_set)[0],
                        'marked_alternatives': list(alternativas_set),
                        'confidence': 100.0,
                        'manually_corrected': True,
                        'fill_percentage': 100.0,
                        'difference': 100.0
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
                    'respuestas': final_respuestas,  # Usar final_respuestas en lugar de edited_respuestas
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

        # Convertir edited_respuestas (sets) a formato simple para guardar
        final_respuestas_simple = {}
        for pregunta, alternativas_set in self.edited_respuestas.items():
            if len(alternativas_set) == 1:
                # Respuesta única
                final_respuestas_simple[pregunta] = list(alternativas_set)[0]
            elif len(alternativas_set) > 1:
                # Múltiples respuestas - guardar la primera (pero el overlay mostrará todas)
                final_respuestas_simple[pregunta] = list(alternativas_set)[0]
            # Si len == 0, no se guarda (sin respuesta)

        sheet['result']['respuestas'] = final_respuestas_simple

        # IMPORTANTE: Actualizar image_path con la nueva matrícula corregida
        # Esto es crítico para que el archivo se guarde con el nombre correcto
        old_image_path = sheet['result'].get('image_path')
        if old_image_path:
            # Reconstruir el path con la nueva matrícula
            from pathlib import Path
            old_path = Path(old_image_path)

            # El output_dir es la carpeta de la prueba (ej: excel_dir/test_name/)
            # Mantener esta estructura
            output_dir = old_path.parent

            # Asegurar que la carpeta existe (en caso de que no exista por alguna razón)
            output_dir.mkdir(parents=True, exist_ok=True)

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

        # Recorrer las respuestas editadas (ahora son sets)
        for pregunta, alternativas_set in self.edited_respuestas.items():
            # Si no hay alternativas o hay múltiples, es incorrecta
            if len(alternativas_set) == 0 or len(alternativas_set) > 1:
                if pregunta in answer_key:
                    incorrectas += 1
                continue

            # Si hay exactamente una alternativa, verificar si es correcta
            alternativa = list(alternativas_set)[0]

            if pregunta in answer_key:
                if alternativa == answer_key[pregunta]:
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
