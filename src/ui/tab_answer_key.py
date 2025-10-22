"""
Pestaña para configurar la pauta de respuestas correctas
"""

import customtkinter as ctk
from tkinter import messagebox
from src.utils.constants import ALTERNATIVES, MAX_QUESTIONS


class AnswerKeyTab:
    """
    Pestaña para construir la pauta de respuestas correctas
    """
    
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data
        self.answer_widgets = {}  # {pregunta: combobox}
        
        # Crear frame principal con scroll
        self.main_frame = ctk.CTkScrollableFrame(parent)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crea todos los widgets de la pestaña"""
        
        # Título
        title_label = ctk.CTkLabel(self.main_frame, 
                                   text="Pauta de Respuestas Correctas",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(0, 20))
        
        # Mensaje informativo
        info_label = ctk.CTkLabel(self.main_frame,
                                 text="Primero configure los parámetros en la pestaña de Configuración",
                                 text_color="gray")
        info_label.pack(pady=10)
        
        # Botón para cargar preguntas
        self.load_button = ctk.CTkButton(self.main_frame,
                                        text="📝 Cargar Preguntas",
                                        command=self.load_questions,
                                        height=40,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.load_button.pack(pady=20)
        
        # Frame para las preguntas (se crea dinámicamente)
        self.questions_frame = None
        
        # Botón para guardar pauta (inicialmente oculto)
        self.save_button = ctk.CTkButton(self.main_frame,
                                        text="💾 Guardar Pauta",
                                        command=self.save_answer_key,
                                        height=40,
                                        font=ctk.CTkFont(size=14, weight="bold"))
    
    def load_questions(self):
        """Carga las preguntas según la configuración"""
        num_questions = self.app_data.get('num_questions', 0)
        
        if num_questions == 0:
            messagebox.showwarning("Advertencia",
                                 "Primero debe configurar la cantidad de preguntas\n" +
                                 "en la pestaña de Configuración")
            return
        
        # Limpiar frame anterior si existe
        if self.questions_frame:
            self.questions_frame.destroy()
            self.answer_widgets.clear()
        
        # Crear nuevo frame para preguntas
        self.questions_frame = ctk.CTkFrame(self.main_frame)
        self.questions_frame.pack(fill="both", expand=True, pady=20)
        
        # Crear grid de preguntas (4 columnas)
        columns = 4
        
        for i in range(1, num_questions + 1):
            row = (i - 1) // columns
            col = (i - 1) % columns
            
            # Frame para cada pregunta
            q_frame = ctk.CTkFrame(self.questions_frame)
            q_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            # Etiqueta de número de pregunta
            q_label = ctk.CTkLabel(q_frame, 
                                  text=f"Pregunta {i}:",
                                  font=ctk.CTkFont(size=12, weight="bold"))
            q_label.pack(pady=5)
            
            # ComboBox para seleccionar alternativa
            combo = ctk.CTkComboBox(q_frame,
                                   values=ALTERNATIVES,
                                   width=80,
                                   state="readonly")
            combo.set(ALTERNATIVES[0])  # Seleccionar 'A' por defecto
            combo.pack(pady=5)
            
            self.answer_widgets[i] = combo
        
        # Configurar columnas para que se expandan uniformemente
        for col in range(columns):
            self.questions_frame.grid_columnconfigure(col, weight=1)
        
        # Mostrar botón de guardar
        self.save_button.pack(pady=20)
        
        messagebox.showinfo("Preguntas cargadas",
                           f"Se han cargado {num_questions} preguntas\n" +
                           "Seleccione la alternativa correcta para cada una")
    
    def save_answer_key(self):
        """Guarda la pauta de respuestas en app_data"""
        if not self.answer_widgets:
            messagebox.showwarning("Advertencia",
                                 "Primero debe cargar las preguntas")
            return
        
        # Recopilar respuestas
        answer_key = {}
        for question_num, combo in self.answer_widgets.items():
            answer_key[question_num] = combo.get()
        
        # Guardar en app_data
        self.app_data['answer_key'] = answer_key
        
        # Mostrar resumen
        summary = f"Pauta guardada correctamente\n\n"
        summary += f"Total de preguntas: {len(answer_key)}\n\n"
        summary += "Primeras 10 respuestas:\n"
        
        for i in range(1, min(11, len(answer_key) + 1)):
            summary += f"Pregunta {i}: {answer_key[i]}\n"
        
        if len(answer_key) > 10:
            summary += "...\n"
        
        messagebox.showinfo("Pauta guardada", summary)
    
    def get_answer_key(self):
        """Retorna la pauta de respuestas actual"""
        return self.app_data.get('answer_key', {})