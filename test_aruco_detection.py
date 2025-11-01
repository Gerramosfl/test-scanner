"""
Script temporal para probar la detección de marcadores ArUco.

Este script:
1. Abre la cámara
2. Muestra el feed en tiempo real
3. Detecta marcadores ArUco
4. Muestra la imagen corregida por perspectiva
5. Permite guardar imágenes para calibración

NOTA: Este archivo es temporal y será eliminado en la versión final.

Controles:
- ESC: Salir
- ESPACIO: Capturar y guardar imagen corregida
- 'c': Capturar imagen corregida para calibración
- 'd': Activar/desactivar modo debug (muestra marcadores)

Author: Gerson
Date: 2025
"""

import cv2
import numpy as np
from datetime import datetime
from src.core.image_processor import ImageProcessor

def detect_available_cameras():
    """
    Detecta todas las cámaras disponibles en el sistema.

    Returns:
        Lista de índices de cámaras disponibles
    """
    available_cameras = []
    print("\nDetectando cámaras disponibles...")

    for camera_index in range(10):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            # Intentar leer un frame para verificar que funciona
            ret, _ = cap.read()
            if ret:
                # Obtener información de la cámara
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available_cameras.append({
                    'index': camera_index,
                    'resolution': f"{width}x{height}"
                })
                print(f"  [{camera_index}] Cámara detectada - Resolución: {width}x{height}")
            cap.release()

    return available_cameras

def select_camera(available_cameras):
    """
    Permite al usuario seleccionar una cámara.

    Args:
        available_cameras: Lista de diccionarios con información de cámaras

    Returns:
        Índice de la cámara seleccionada o None si se cancela
    """
    if not available_cameras:
        print("✗ No se detectaron cámaras disponibles")
        return None

    print("\n" + "=" * 60)
    print("CÁMARAS DISPONIBLES:")
    print("=" * 60)

    for cam in available_cameras:
        print(f"  [{cam['index']}] Resolución: {cam['resolution']}")

    print("=" * 60)

    while True:
        try:
            selection = input(f"\nSeleccione el índice de la cámara a usar (0-{len(available_cameras)-1}): ")
            camera_index = int(selection)

            # Verificar que el índice seleccionado está en la lista
            if any(cam['index'] == camera_index for cam in available_cameras):
                print(f"✓ Cámara {camera_index} seleccionada")
                return camera_index
            else:
                print(f"✗ Índice inválido. Por favor seleccione uno de los índices mostrados.")
        except ValueError:
            print("✗ Por favor ingrese un número válido")
        except KeyboardInterrupt:
            print("\n✗ Selección cancelada")
            return None

def main():
    """Función principal del script de prueba."""
    print("=" * 60)
    print("SCRIPT DE PRUEBA - DETECCIÓN ARUCO")
    print("=" * 60)
    print("\nControles:")
    print("  ESC       - Salir del programa")
    print("  ESPACIO   - Capturar y guardar imagen corregida")
    print("  'c'       - Guardar para calibración (guarda en 'calibration_image.jpg')")
    print("  'd'       - Activar/desactivar modo debug")

    # Detectar cámaras disponibles
    available_cameras = detect_available_cameras()

    if not available_cameras:
        print("\n✗ Error: No se detectaron cámaras")
        return

    # Permitir al usuario seleccionar la cámara
    camera_index = select_camera(available_cameras)

    if camera_index is None:
        return

    # Inicializar procesador de imágenes
    processor = ImageProcessor()

    # Abrir la cámara seleccionada
    print(f"\nAbriendo cámara {camera_index}...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"✗ Error: No se pudo abrir la cámara {camera_index}")
        return

    # Configurar resolución de cámara
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    debug_mode = True
    print("\nModo debug activado (presiona 'd' para desactivar)")
    print("\n¡Muestra la hoja de respuestas a la cámara!")
    print("Los 4 marcadores ArUco deben ser visibles.\n")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error al capturar frame")
            break

        # Procesar la imagen
        result = processor.process_answer_sheet(frame)

        # Crear ventana para mostrar el feed original
        display_frame = frame.copy()

        if result['success']:
            # Dibujar marcadores en modo debug
            if debug_mode and result['corners'] is not None:
                # Dibujar las esquinas ordenadas
                corners = result['corners'].astype(int)

                # Dibujar líneas entre los marcadores
                cv2.polylines(display_frame, [corners], True, (0, 255, 0), 2)

                # Dibujar círculos en cada esquina con etiquetas
                labels = ['TL (0)', 'TR (1)', 'BR (3)', 'BL (2)']
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

                for i, (corner, label, color) in enumerate(zip(corners, labels, colors)):
                    cv2.circle(display_frame, tuple(corner), 10, color, -1)
                    cv2.putText(display_frame, label,
                               (corner[0] + 15, corner[1]),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Mostrar mensaje de éxito
            cv2.putText(display_frame, "HOJA DETECTADA", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, "Presiona ESPACIO para capturar", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Mostrar la imagen corregida en una ventana separada
            if result['warped_image'] is not None:
                # Redimensionar para mostrar (la imagen corregida es muy grande)
                display_warped = cv2.resize(result['warped_image'], (600, 780))
                cv2.imshow('Imagen Corregida', display_warped)

        else:
            # Mostrar mensaje de error
            cv2.putText(display_frame, result['message'], (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Mostrar instrucciones en pantalla
        cv2.putText(display_frame, "ESC: Salir | ESPACIO: Guardar | C: Calibracion | D: Debug",
                   (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Mostrar el frame
        cv2.imshow('Feed de Camara', display_frame)

        # Manejar teclas
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            print("\nSaliendo...")
            break

        elif key == ord(' '):  # ESPACIO
            if result['success']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"captured_sheet_{timestamp}.jpg"
                cv2.imwrite(filename, result['warped_image'])
                print(f"✓ Imagen guardada: {filename}")
            else:
                print("✗ No se puede guardar: hoja no detectada correctamente")

        elif key == ord('c') or key == ord('C'):  # Guardar para calibración
            if result['success']:
                filename = "calibration_image.jpg"
                cv2.imwrite(filename, result['warped_image'])
                print(f"✓ Imagen de calibración guardada: {filename}")
                print("  Usa esta imagen con la herramienta de calibración")
            else:
                print("✗ No se puede guardar: hoja no detectada correctamente")

        elif key == ord('d') or key == ord('D'):  # Toggle debug
            debug_mode = not debug_mode
            print(f"Modo debug: {'ACTIVADO' if debug_mode else 'DESACTIVADO'}")

    # Limpiar
    cap.release()
    cv2.destroyAllWindows()
    print("\n¡Script finalizado!")

if __name__ == "__main__":
    main()
