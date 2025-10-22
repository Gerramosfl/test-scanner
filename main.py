"""
Test Scanner - Sistema de Calificación Automática de Pruebas OMR
Punto de entrada principal de la aplicación
"""

import sys
import customtkinter as ctk
from src.ui.main_window import MainWindow


def main():
    """Función principal que inicia la aplicación"""
    # Configurar apariencia de CustomTkinter
    ctk.set_appearance_mode("dark")  # Opciones: "dark", "light", "system"
    ctk.set_default_color_theme("blue")  # Opciones: "blue", "dark-blue", "green"
    
    # Crear y ejecutar la ventana principal
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAplicación cerrada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError crítico: {e}")
        sys.exit(1)