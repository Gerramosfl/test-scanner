# src/__init__.py
"""
Test Scanner - Sistema de Calificación Automática
"""

__version__ = "1.0.0"
__author__ = "Tu Nombre"


# src/ui/__init__.py
"""
Módulo de interfaz de usuario
"""

from .main_window import MainWindow
from .tab_configuration import ConfigurationTab
from .tab_answer_key import AnswerKeyTab
from .tab_grading import GradingTab

__all__ = ['MainWindow', 'ConfigurationTab', 'AnswerKeyTab', 'GradingTab']


# src/core/__init__.py
"""
Módulo de lógica central
"""

from .grade_calculator import GradeCalculator
from .excel_handler import ExcelHandler

__all__ = ['GradeCalculator', 'ExcelHandler']


# src/utils/__init__.py
"""
Módulo de utilidades
"""

from .constants import *

__all__ = ['constants']