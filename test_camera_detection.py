#!/usr/bin/env python3
"""
Script de prueba para verificar la detección de cámaras
"""

import cv2


def detect_available_cameras():
    """Detecta todas las cámaras disponibles en el sistema"""
    available_cameras = []
    print("🔍 Buscando cámaras disponibles...")
    print("-" * 50)

    # Probar hasta 10 índices de cámara
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Intentar leer un frame para confirmar que funciona
            ret, frame = cap.read()
            if ret:
                # Obtener información de la cámara
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))

                available_cameras.append(i)
                print(f"✅ Cámara {i} detectada:")
                print(f"   Resolución: {width}x{height}")
                print(f"   FPS: {fps}")
                print(f"   Frame leído correctamente: {ret}")
                print()
            cap.release()
        else:
            # Si no se puede abrir, probablemente no hay más cámaras
            if i == 0:
                print(f"⚠️  Índice {i}: No se pudo abrir")
            break

    print("-" * 50)

    # Si no se encontraron cámaras, agregar índice 0 por defecto
    if not available_cameras:
        available_cameras = [0]
        print("⚠️  Advertencia: No se detectaron cámaras funcionando")
        print("   Usando índice 0 por defecto")
    else:
        print(f"✅ Total de cámaras detectadas: {len(available_cameras)}")
        print(f"   Índices disponibles: {available_cameras}")

    return available_cameras


if __name__ == "__main__":
    print("=" * 50)
    print("TEST DE DETECCIÓN DE CÁMARAS")
    print("=" * 50)
    print()

    cameras = detect_available_cameras()

    print()
    print("=" * 50)
    print("RESULTADO:")
    print(f"Cámaras disponibles: {cameras}")
    print("=" * 50)
