"""
Ventana principal de la aplicación Test Scanner
"""

import customtkinter as ctk
from src.utils.constants import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from src.ui.tab_configuration import ConfigurationTab
from src.ui.tab_answer_key import AnswerKeyTab
from src.ui.tab_grading import GradingTab


class MainWindow(ctk.CTk):
    """
    Ventana principal que contiene las 3 pestañas de la aplicación
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.state('zoomed')  # Iniciar maximizada
        
        # Centrar ventana (ya que está maximizada, esto es opcional)
        #self.center_window()
        
        # Datos compartidos entre pestañas
        self.app_data = {
            'num_questions': 0,
            'passing_percentage': 60.0,
            'min_grade': 1.0,
            'max_grade': 7.0,
            'passing_grade': 4.0,
            'excel_file': None,
            'test_name': '',
            'answer_key': {},  # {pregunta: alternativa_correcta}
            'excel_handler': None
        }
        
        # Crear el widget de pestañas
        self.tabview = ctk.CTkTabview(self, width=WINDOW_WIDTH-40, 
                                      height=WINDOW_HEIGHT-40)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Crear las 3 pestañas
        self.tab_config = self.tabview.add("⚙️ Configuración")
        self.tab_answer_key = self.tabview.add("📝 Pauta de Respuestas")
        self.tab_grading = self.tabview.add("📷 Calificación")
        
        # Inicializar contenido de cada pestaña
        self.config_tab = ConfigurationTab(self.tab_config, self.app_data)
        self.answer_key_tab = AnswerKeyTab(self.tab_answer_key, self.app_data)
        self.grading_tab = GradingTab(self.tab_grading, self.app_data)
        
        # Configurar cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        # Cerrar el manejador de Excel si existe
        if self.app_data.get('excel_handler'):
            try:
                self.app_data['excel_handler'].close()
            except:
                pass

        self.destroy()