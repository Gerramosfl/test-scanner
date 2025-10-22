"""
Pestaña de configuración de la prueba
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.utils.constants import (MAX_QUESTIONS, DEFAULT_MIN_GRADE, DEFAULT_MAX_GRADE,
                                DEFAULT_PASSING_GRADE, DEFAULT_PASSING_PERCENTAGE)
from src.core.excel_handler import ExcelHandler


class ConfigurationTab:
    """
    Pestaña para configurar los parámetros de la prueba
    """
    
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data
        
        # Crear frame principal con scroll
        self.main_frame = ctk.CTkScrollableFrame(parent)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crea todos los widgets de la pestaña"""
        
        # Título
        title_label = ctk.CTkLabel(self.main_frame, 
                                   text="Configuración de la Prueba",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(0, 30))
        
        # Frame para configuración de preguntas
        questions_frame = ctk.CTkFrame(self.main_frame)
        questions_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(questions_frame, 
                    text="Configuración de Preguntas",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Cantidad de preguntas
        q_frame = ctk.CTkFrame(questions_frame)
        q_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(q_frame, text="Cantidad de preguntas:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.questions_entry = ctk.CTkEntry(q_frame, width=100, 
                                           placeholder_text=f"1-{MAX_QUESTIONS}")
        self.questions_entry.pack(side="left", padx=10)
        self.questions_entry.insert(0, "20")  # Valor por defecto
        
        # Frame para configuración de notas
        grades_frame = ctk.CTkFrame(self.main_frame)
        grades_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(grades_frame, 
                    text="Configuración de Notas",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Porcentaje de exigencia
        exig_frame = ctk.CTkFrame(grades_frame)
        exig_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(exig_frame, text="Porcentaje de exigencia (%):", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.exigencia_entry = ctk.CTkEntry(exig_frame, width=100, 
                                           placeholder_text="0-100")
        self.exigencia_entry.pack(side="left", padx=10)
        self.exigencia_entry.insert(0, str(DEFAULT_PASSING_PERCENTAGE))
        
        # Nota mínima
        min_frame = ctk.CTkFrame(grades_frame)
        min_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(min_frame, text="Nota mínima:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.min_grade_entry = ctk.CTkEntry(min_frame, width=100)
        self.min_grade_entry.pack(side="left", padx=10)
        self.min_grade_entry.insert(0, str(DEFAULT_MIN_GRADE))
        
        # Nota máxima
        max_frame = ctk.CTkFrame(grades_frame)
        max_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(max_frame, text="Nota máxima:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.max_grade_entry = ctk.CTkEntry(max_frame, width=100)
        self.max_grade_entry.pack(side="left", padx=10)
        self.max_grade_entry.insert(0, str(DEFAULT_MAX_GRADE))
        
        # Nota de aprobación
        pass_frame = ctk.CTkFrame(grades_frame)
        pass_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(pass_frame, text="Nota de aprobación:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.passing_grade_entry = ctk.CTkEntry(pass_frame, width=100)
        self.passing_grade_entry.pack(side="left", padx=10)
        self.passing_grade_entry.insert(0, str(DEFAULT_PASSING_GRADE))
        
        # Frame para archivo Excel
        excel_frame = ctk.CTkFrame(self.main_frame)
        excel_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(excel_frame, 
                    text="Archivo de Estudiantes",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        excel_btn_frame = ctk.CTkFrame(excel_frame)
        excel_btn_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(excel_btn_frame, text="Archivo Excel:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.excel_button = ctk.CTkButton(excel_btn_frame, 
                                         text="Cargar Excel",
                                         command=self.load_excel_file,
                                         width=150)
        self.excel_button.pack(side="left", padx=10)
        
        self.excel_label = ctk.CTkLabel(excel_btn_frame, 
                                       text="No se ha cargado ningún archivo",
                                       text_color="gray")
        self.excel_label.pack(side="left", padx=10)
        
        # Frame para nombre de prueba
        test_frame = ctk.CTkFrame(self.main_frame)
        test_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(test_frame, 
                    text="Identificación de la Prueba",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        name_frame = ctk.CTkFrame(test_frame)
        name_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(name_frame, text="Nombre de la prueba:", 
                    width=200, anchor="w").pack(side="left", padx=10)
        
        self.test_name_entry = ctk.CTkEntry(name_frame, width=300,
                                           placeholder_text="Ej: Test 1, Examen Final, etc.")
        self.test_name_entry.pack(side="left", padx=10)
        
        # Botón para guardar configuración
        save_button = ctk.CTkButton(self.main_frame, 
                                   text="💾 Guardar Configuración",
                                   command=self.save_configuration,
                                   height=40,
                                   font=ctk.CTkFont(size=14, weight="bold"))
        save_button.pack(pady=30)
    
    def load_excel_file(self):
        """Abre el diálogo para seleccionar el archivo Excel"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Intentar cargar el archivo
                excel_handler = ExcelHandler(filename)
                
                # Si se cargó correctamente, actualizar la interfaz
                self.app_data['excel_file'] = filename
                self.app_data['excel_handler'] = excel_handler
                
                num_students = len(excel_handler.get_all_students())
                self.excel_label.configure(
                    text=f"✓ {num_students} estudiantes cargados",
                    text_color="green"
                )
                
                messagebox.showinfo("Éxito", 
                                   f"Archivo cargado correctamente\n{num_students} estudiantes encontrados")
                
            except Exception as e:
                messagebox.showerror("Error", 
                                    f"No se pudo cargar el archivo:\n{str(e)}")
                self.excel_label.configure(
                    text="Error al cargar archivo",
                    text_color="red"
                )
    
    def save_configuration(self):
        """Guarda la configuración en app_data"""
        try:
            # Validar y guardar cantidad de preguntas
            num_questions = int(self.questions_entry.get())
            if num_questions < 1 or num_questions > MAX_QUESTIONS:
                raise ValueError(f"La cantidad de preguntas debe estar entre 1 y {MAX_QUESTIONS}")
            
            # Validar y guardar porcentaje de exigencia
            passing_percentage = float(self.exigencia_entry.get())
            if passing_percentage < 0 or passing_percentage > 100:
                raise ValueError("El porcentaje de exigencia debe estar entre 0 y 100")
            
            # Validar y guardar notas
            min_grade = float(self.min_grade_entry.get())
            max_grade = float(self.max_grade_entry.get())
            passing_grade = float(self.passing_grade_entry.get())
            
            if min_grade >= max_grade:
                raise ValueError("La nota mínima debe ser menor que la nota máxima")
            
            if passing_grade < min_grade or passing_grade > max_grade:
                raise ValueError("La nota de aprobación debe estar entre la nota mínima y máxima")
            
            # Validar nombre de prueba
            test_name = self.test_name_entry.get().strip()
            if not test_name:
                raise ValueError("Debe ingresar un nombre para la prueba")
            
            # Validar que se haya cargado el Excel
            if not self.app_data.get('excel_file'):
                raise ValueError("Debe cargar un archivo Excel antes de continuar")
            
            # Guardar en app_data
            self.app_data['num_questions'] = num_questions
            self.app_data['passing_percentage'] = passing_percentage
            self.app_data['min_grade'] = min_grade
            self.app_data['max_grade'] = max_grade
            self.app_data['passing_grade'] = passing_grade
            self.app_data['test_name'] = test_name
            
            messagebox.showinfo("Éxito", 
                               "Configuración guardada correctamente\n\n" +
                               "Ahora puede configurar la pauta de respuestas en la siguiente pestaña")
            
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")