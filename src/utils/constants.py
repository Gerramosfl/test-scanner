"""
Constantes utilizadas en toda la aplicación
"""

# Configuración de la hoja de respuestas
MAX_QUESTIONS = 100
NUM_ALTERNATIVES = 5
ALTERNATIVES = ['A', 'B', 'C', 'D', 'E']
MATRICULA_DIGITS = 10

# Configuración de marcadores ArUco
ARUCO_DICT = "DICT_4X4_50"  # Diccionario de marcadores ArUco
ARUCO_MARKER_SIZE_MM = 15  # Tamaño del marcador en mm
PAPER_SIZE = "LETTER"  # Tamaño de papel (Carta)

# Dimensiones de papel carta en mm
PAPER_WIDTH_MM = 215.9
PAPER_HEIGHT_MM = 279.4

# Configuración de detección OMR
MIN_FILL_PERCENTAGE = 40  # Porcentaje mínimo de relleno para considerar marcado
MAX_FILL_PERCENTAGE = 90  # Porcentaje máximo (para detectar sobre-marcado)

# Colores para overlay visual (BGR para OpenCV)
COLOR_CORRECT = (0, 255, 0)      # Verde
COLOR_INCORRECT = (0, 0, 255)    # Rojo
COLOR_CORRECT_ANSWER = (0, 255, 255)  # Amarillo
COLOR_AMBIGUOUS = (0, 165, 255)  # Naranja

# Escala de notas chilena
DEFAULT_MIN_GRADE = 1.0
DEFAULT_MAX_GRADE = 7.0
DEFAULT_PASSING_GRADE = 4.0
DEFAULT_PASSING_PERCENTAGE = 60.0

# Configuración de la cámara
DEFAULT_CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Configuración de la interfaz
WINDOW_TITLE = "Test Scanner - Sistema de Calificación Automática"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Mensajes de la aplicación
MSG_NO_SHEET_DETECTED = "No se detectó ninguna hoja de respuestas"
MSG_MULTIPLE_MARKS = "Se detectaron múltiples marcas en la pregunta"
MSG_NO_MARK = "No se detectó ninguna marca en la pregunta"
MSG_GRADE_SAVED = "Nota guardada exitosamente"
MSG_DUPLICATE_GRADE = "Este alumno ya tiene una nota registrada para esta prueba"
MSG_STUDENT_NOT_FOUND = "No se encontró el alumno con la matrícula detectada"
MSG_INVALID_CONFIG = "La configuración de la prueba no es válida"
MSG_NO_ANSWER_KEY = "Debe configurar la pauta de respuestas"
MSG_NO_EXCEL_LOADED = "Debe cargar un archivo Excel"

# Extensiones de archivo permitidas
EXCEL_EXTENSIONS = [".xlsx", ".xls"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]

# Configuración de archivos de ejemplo
EXAMPLE_ANSWER_SHEET = "examples/hoja_respuestas.pdf"
EXAMPLE_STUDENT_LIST = "examples/lista_alumnos_ejemplo.xlsx"