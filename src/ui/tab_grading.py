"""
Pestaña de calificación en tiempo real
"""

import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
from src.utils.constants import (DEFAULT_CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
                                MSG_NO_SHEET_DETECTED, MSG_INVALID_CONFIG)
from src.core.grade_calculator import GradeCalculator


class GradingTab:
    """
    Pestaña para calificar pruebas en tiempo real usando la cámara
    """
    
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data

        self.camera = None
        self.camera_running = False
        self.current_frame = None
        self.detected_matricula = None
        self.detected_answers = {}
        self.available_cameras = []
        self.selected_camera_index = 0

        # Crear frame principal
        self.main_frame = ctk.CTkFrame(parent)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Detectar cámaras disponibles
        self.detect_available_cameras()

        self.create_widgets()

    def detect_available_cameras(self):
        """Detecta todas las cámaras disponibles en el sistema"""
        self.available_cameras = []
        # Probar hasta 10 índices de cámara
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Intentar leer un frame para confirmar que funciona
                ret, _ = cap.read()
                if ret:
                    self.available_cameras.append(i)
                cap.release()
            else:
                # Si no se puede abrir, probablemente no hay más cámaras
                break

        # Si no se encontraron cámaras, agregar índice 0 por defecto
        if not self.available_cameras:
            self.available_cameras = [0]
            print("⚠️ Advertencia: No se detectaron cámaras, usando índice 0 por defecto")
        else:
            print(f"✅ Cámaras detectadas: {self.available_cameras}")

    def on_camera_selected(self, choice):
        """Callback cuando se selecciona una cámara diferente"""
        # Extraer el índice de la cámara del texto "Cámara X"
        camera_index = int(choice.split()[-1])
        self.selected_camera_index = camera_index
        print(f"📹 Cámara seleccionada: índice {camera_index}")

        # Si la cámara está corriendo, reiniciarla con el nuevo índice
        if self.camera_running:
            self.stop_camera()
            # Dar un momento para que se libere la cámara anterior
            self.parent.after(500, self.start_camera)

    def create_widgets(self):
        """Crea todos los widgets de la pestaña"""
        
        # Frame superior con controles
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", pady=10)

        # Label y selector de cámara
        camera_select_label = ctk.CTkLabel(control_frame,
                                           text="Cámara:",
                                           font=ctk.CTkFont(size=12))
        camera_select_label.pack(side="left", padx=(10, 5))

        # ComboBox para seleccionar cámara
        camera_options = [f"Cámara {i}" for i in self.available_cameras]
        self.camera_selector = ctk.CTkComboBox(control_frame,
                                               values=camera_options,
                                               command=self.on_camera_selected,
                                               width=120,
                                               state="readonly")
        self.camera_selector.set(camera_options[0])
        self.camera_selector.pack(side="left", padx=5)

        # Botón para iniciar cámara
        self.start_camera_btn = ctk.CTkButton(control_frame,
                                             text="📹 Iniciar Cámara",
                                             command=self.start_camera,
                                             height=40,
                                             width=150)
        self.start_camera_btn.pack(side="left", padx=10)
        
        # Botón para detener cámara
        self.stop_camera_btn = ctk.CTkButton(control_frame,
                                            text="⏹ Detener Cámara",
                                            command=self.stop_camera,
                                            height=40,
                                            width=150,
                                            state="disabled")
        self.stop_camera_btn.pack(side="left", padx=10)
        
        # Botón para calificar
        self.grade_btn = ctk.CTkButton(control_frame,
                                      text="✅ Calificar",
                                      command=self.grade_current_sheet,
                                      height=40,
                                      width=150,
                                      state="disabled",
                                      fg_color="green",
                                      hover_color="darkgreen")
        self.grade_btn.pack(side="left", padx=10)
        
        # Label con información
        self.info_label = ctk.CTkLabel(control_frame,
                                      text="Presione 'Iniciar Cámara' para comenzar",
                                      font=ctk.CTkFont(size=12))
        self.info_label.pack(side="left", padx=20)
        
        # Frame para la vista de cámara
        camera_frame = ctk.CTkFrame(self.main_frame)
        camera_frame.pack(fill="both", expand=True, pady=10)
        
        # Label para mostrar el video
        self.camera_label = ctk.CTkLabel(camera_frame, text="")
        self.camera_label.pack(expand=True, padx=20, pady=20)
        
        # Frame inferior con resultados
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="x", pady=10)
        
        results_title = ctk.CTkLabel(self.results_frame,
                                    text="Resultados de la Calificación",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        results_title.pack(pady=10)
        
        self.results_text = ctk.CTkTextbox(self.results_frame, height=150)
        self.results_text.pack(fill="x", padx=20, pady=10)
    
    def start_camera(self):
        """Inicia la cámara"""
        if self.camera_running:
            return

        try:
            # Usar la cámara seleccionada por el usuario
            self.camera = cv2.VideoCapture(self.selected_camera_index)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

            if not self.camera.isOpened():
                raise Exception(f"No se pudo abrir la cámara {self.selected_camera_index}")

            self.camera_running = True
            self.start_camera_btn.configure(state="disabled")
            self.stop_camera_btn.configure(state="normal")
            self.grade_btn.configure(state="normal")
            self.camera_selector.configure(state="disabled")  # Deshabilitar selector mientras cámara activa
            self.info_label.configure(text=f"Cámara {self.selected_camera_index} activa - Acerque la hoja de respuestas")

            # Iniciar thread para actualizar video
            self.update_camera()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar la cámara:\n{str(e)}")
            self.stop_camera()
    
    def stop_camera(self):
        """Detiene la cámara"""
        self.camera_running = False

        if self.camera:
            self.camera.release()
            self.camera = None

        self.start_camera_btn.configure(state="normal")
        self.stop_camera_btn.configure(state="disabled")
        self.grade_btn.configure(state="disabled")
        self.camera_selector.configure(state="readonly")  # Habilitar selector nuevamente
        self.info_label.configure(text="Cámara detenida")
        self.camera_label.configure(image="", text="Cámara detenida")
    
    def update_camera(self):
        """Actualiza el frame de la cámara"""
        if not self.camera_running:
            return
        
        ret, frame = self.camera.read()
        
        if ret:
            self.current_frame = frame.copy()
            
            # TODO: Aquí se implementará la detección de marcadores ArUco
            # y el overlay de respuestas
            
            # Convertir frame para mostrar
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # Redimensionar para ajustar a la ventana
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_label.imgtk = imgtk
            self.camera_label.configure(image=imgtk, text="")
        
        # Programar siguiente actualización
        if self.camera_running:
            self.parent.after(30, self.update_camera)
    
    def grade_current_sheet(self):
        """Califica la hoja de respuestas actual"""
        # Verificar configuración
        if self.app_data.get('num_questions', 0) == 0:
            messagebox.showerror("Error", MSG_INVALID_CONFIG)
            return
        
        if not self.app_data.get('answer_key'):
            messagebox.showerror("Error", "Debe configurar la pauta de respuestas")
            return
        
        if not self.app_data.get('excel_handler'):
            messagebox.showerror("Error", "Debe cargar un archivo Excel")
            return
        
        if self.current_frame is None:
            messagebox.showerror("Error", MSG_NO_SHEET_DETECTED)
            return
        
        # TODO: Aquí se implementará toda la lógica de:
        # 1. Detección de marcadores ArUco
        # 2. Corrección de perspectiva
        # 3. Detección de matrícula
        # 4. Detección de respuestas marcadas
        # 5. Comparación con pauta
        # 6. Cálculo de nota
        # 7. Guardado en Excel
        
        # Por ahora, mostrar mensaje de que está en desarrollo
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", 
            "🚧 Función en desarrollo 🚧\n\n" +
            "Esta función implementará:\n" +
            "- Detección de marcadores ArUco\n" +
            "- Lectura de matrícula del estudiante\n" +
            "- Detección de respuestas marcadas\n" +
            "- Overlay visual (verde/rojo/amarillo)\n" +
            "- Cálculo automático de nota\n" +
            "- Guardado en Excel\n"
        )
        
        messagebox.showinfo("Información", 
                           "La funcionalidad de calificación está en desarrollo.\n" +
                           "Próximos pasos: implementar detección ArUco y OMR.")