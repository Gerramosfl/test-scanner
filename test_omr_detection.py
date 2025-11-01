"""
Script temporal para probar la detección OMR con hojas reales.

Este script:
1. Abre la cámara
2. Detecta marcadores ArUco y corrige perspectiva
3. Aplica detección OMR para leer matrícula y respuestas
4. Muestra resultados en tiempo real

NOTA: Este archivo es temporal y será eliminado en la versión final.

Controles:
- ESC: Salir
- ESPACIO: Mostrar resultados detallados en consola
- 'd': Activar/desactivar overlay visual

Author: Gerson
Date: 2025
"""

import cv2
import sys
from src.core.image_processor import ImageProcessor
from src.core.omr_detector import OMRDetector


def print_detection_results(detection_result: dict):
    """Imprime los resultados de detección en formato legible."""
    print("\n" + "=" * 80)
    print("RESULTADOS DE DETECCIÓN")
    print("=" * 80)

    # Matrícula
    matricula_data = detection_result['matricula']
    print(f"\n📋 MATRÍCULA:")
    print(f"  Detectada: {matricula_data.get('matricula', 'N/A')}")
    print(f"  Confianza: {matricula_data.get('confidence', 0):.1f}%")
    print(f"  Éxito: {'✓' if matricula_data.get('success') else '✗'}")

    if matricula_data.get('errors'):
        print(f"  Errores:")
        for error in matricula_data['errors']:
            print(f"    - {error}")

    # Respuestas
    respuestas_data = detection_result['respuestas']
    print(f"\n📝 RESPUESTAS:")
    print(f"  Total detectadas: {len(respuestas_data.get('respuestas', {}))}/100")
    print(f"  Confianza: {respuestas_data.get('confidence', 0):.1f}%")
    print(f"  Éxito: {'✓' if respuestas_data.get('success') else '✗'}")

    # Mostrar algunas respuestas detectadas
    respuestas = respuestas_data.get('respuestas', {})
    if respuestas:
        print(f"\n  Primeras 10 respuestas:")
        for i in range(1, min(11, len(respuestas) + 1)):
            if i in respuestas:
                resp = respuestas[i]
                print(f"    P{i:2d}: {resp if resp else 'Sin respuesta'}")

    # Errores
    if respuestas_data.get('errors'):
        error_count = len(respuestas_data['errors'])
        print(f"\n  Errores encontrados: {error_count}")
        if error_count <= 10:
            for error in respuestas_data['errors']:
                print(f"    - {error}")
        else:
            print(f"    (Mostrando primeros 10)")
            for error in respuestas_data['errors'][:10]:
                print(f"    - {error}")

    # Confianza general
    print(f"\n🎯 CONFIANZA GENERAL: {detection_result.get('overall_confidence', 0):.1f}%")
    print("=" * 80 + "\n")


def main():
    """Función principal del script de prueba."""
    print("=" * 80)
    print("SCRIPT DE PRUEBA - DETECCIÓN OMR")
    print("=" * 80)
    print("\nControles:")
    print("  ESC       - Salir del programa")
    print("  ESPACIO   - Mostrar resultados detallados")
    print("  'd'       - Activar/desactivar overlay visual")
    print("\nIniciando...")

    try:
        # Inicializar procesador de imágenes y detector OMR
        processor = ImageProcessor()
        detector = OMRDetector()
        print("✓ Módulos inicializados correctamente")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nAsegúrate de haber ejecutado:")
        print("  1. python test_aruco_detection.py  (para generar calibration_image.jpg)")
        print("  2. python calibration_tool.py      (para generar config/calibration_data.json)")
        return
    except Exception as e:
        print(f"\n✗ Error al inicializar: {e}")
        return

    # Detectar cámaras disponibles
    print("\nDetectando cámaras...")
    available_cameras = []
    for camera_index in range(10):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available_cameras.append({
                    'index': camera_index,
                    'resolution': f"{width}x{height}"
                })
                print(f"  [{camera_index}] Cámara detectada - Resolución: {width}x{height}")
            cap.release()

    if not available_cameras:
        print("✗ No se detectaron cámaras")
        return

    # Seleccionar cámara
    print("\nCÁMARAS DISPONIBLES:")
    for cam in available_cameras:
        print(f"  [{cam['index']}] Resolución: {cam['resolution']}")

    while True:
        try:
            selection = input(f"\nSeleccione el índice de la cámara a usar: ")
            camera_index = int(selection)
            if any(cam['index'] == camera_index for cam in available_cameras):
                print(f"✓ Cámara {camera_index} seleccionada")
                break
            else:
                print("✗ Índice inválido")
        except ValueError:
            print("✗ Por favor ingrese un número válido")
        except KeyboardInterrupt:
            print("\n✗ Cancelado")
            return

    # Abrir cámara
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"✗ Error al abrir la cámara {camera_index}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\n¡Cámara lista! Muestra una hoja de respuestas marcada.")
    print("Los 4 marcadores ArUco deben ser visibles.\n")

    show_overlay = True
    last_detection = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar frame")
            break

        # Procesar imagen (ArUco + perspectiva)
        process_result = processor.process_answer_sheet(frame)

        display_frame = frame.copy()

        if process_result['success']:
            # Aplicar detección OMR
            try:
                detection_result = detector.detect_answer_sheet(process_result['preprocessed'])
                last_detection = detection_result

                # Crear overlay visual si está activado
                if show_overlay:
                    overlay = detector.create_visual_overlay(
                        process_result['warped_image'],
                        detection_result
                    )
                    # Redimensionar para mostrar
                    display_overlay = cv2.resize(overlay, (600, 780))
                    cv2.imshow('Detección OMR', display_overlay)

                # Mostrar información básica en el frame original
                matricula = detection_result['matricula'].get('matricula', 'N/A')
                confidence = detection_result.get('overall_confidence', 0)

                cv2.putText(display_frame, f"Matricula: {matricula}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Confianza: {confidence:.1f}%", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                respuestas_count = len(detection_result['respuestas'].get('respuestas', {}))
                cv2.putText(display_frame, f"Respuestas: {respuestas_count}/100", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            except Exception as e:
                cv2.putText(display_frame, f"Error OMR: {str(e)[:50]}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        else:
            cv2.putText(display_frame, process_result['message'], (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Instrucciones
        cv2.putText(display_frame, "ESC: Salir | ESPACIO: Detalles | D: Toggle overlay",
                   (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('Feed de Camara', display_frame)

        # Manejar teclas
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            print("\nSaliendo...")
            break

        elif key == ord(' '):  # ESPACIO
            if last_detection:
                print_detection_results(last_detection)
            else:
                print("\n✗ No hay detección disponible. Muestra una hoja a la cámara.")

        elif key == ord('d') or key == ord('D'):
            show_overlay = not show_overlay
            if not show_overlay:
                cv2.destroyWindow('Detección OMR')
            print(f"Overlay visual: {'ACTIVADO' if show_overlay else 'DESACTIVADO'}")

    # Limpiar
    cap.release()
    cv2.destroyAllWindows()
    print("\n¡Script finalizado!")


if __name__ == "__main__":
    main()
