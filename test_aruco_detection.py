"""
Script de prueba para verificar la detección de marcadores ArUco
Ejecutar: python test_aruco_detection.py
"""

import cv2
import sys
from src.core.image_processor import ImageProcessor


def test_with_camera():
    """Prueba la detección con cámara en tiempo real"""
    print("=== Test de Detección ArUco con Cámara ===")
    print("Instrucciones:")
    print("1. Coloca tu hoja de respuestas frente a la cámara")
    print("2. Asegúrate de que los 4 marcadores ArUco sean visibles")
    print("3. Presiona 'q' para salir")
    print("4. Presiona 's' para guardar imagen cuando detecte los 4 marcadores")
    print("\n")
    
    # Inicializar procesador
    processor = ImageProcessor()
    
    # Abrir cámara
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        return
    
    print("✓ Cámara iniciada correctamente")
    
    detection_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Error al capturar frame")
            break
        
        # Intentar detectar marcadores
        success, markers_dict, image_with_markers = processor.detect_aruco_markers(frame)
        
        # Mostrar estado en la imagen
        if success:
            detection_count += 1
            status_text = f"✓ {len(markers_dict)} marcadores detectados"
            color = (0, 255, 0)  # Verde
            
            # Mostrar IDs de marcadores
            ids_text = f"IDs: {sorted(markers_dict.keys())}"
            cv2.putText(image_with_markers, ids_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Dibujar información adicional
            display_image = processor.draw_detection_info(frame, markers_dict)
        else:
            status_text = "✗ Esperando 4 marcadores..."
            color = (0, 0, 255)  # Rojo
            display_image = frame
        
        # Mostrar estado
        cv2.putText(display_image, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Mostrar frame
        cv2.imshow('Test ArUco Detection - Presiona Q para salir, S para guardar', display_image)
        
        # Manejar teclas
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s') and success:
            # Guardar imagen
            cv2.imwrite('aruco_detected.jpg', display_image)
            print(f"✓ Imagen guardada como 'aruco_detected.jpg'")
            
            # Probar corrección de perspectiva
            success_warp, warped = processor.correct_perspective(frame, markers_dict)
            if success_warp:
                cv2.imwrite('sheet_warped.jpg', warped)
                print(f"✓ Hoja con perspectiva corregida guardada como 'sheet_warped.jpg'")
                
                # Probar pre-procesamiento
                binary = processor.preprocess_for_omr(warped)
                cv2.imwrite('sheet_binary.jpg', binary)
                print(f"✓ Imagen binaria guardada como 'sheet_binary.jpg'")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n📊 Estadísticas:")
    print(f"   Detecciones exitosas: {detection_count}")


def test_with_image(image_path):
    """Prueba la detección con una imagen estática"""
    print(f"=== Test de Detección ArUco con Imagen ===")
    print(f"Imagen: {image_path}\n")
    
    # Inicializar procesador
    processor = ImageProcessor()
    
    # Cargar imagen
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"❌ Error: No se pudo cargar la imagen '{image_path}'")
        return
    
    print(f"✓ Imagen cargada: {image.shape[1]}x{image.shape[0]} píxeles")
    
    # Procesar hoja completa
    success, warped, binary, message = processor.process_sheet(image)
    
    print(f"\n📋 Resultado: {message}")
    
    if success:
        print("✓ Procesamiento exitoso!")
        print(f"   - Dimensiones hoja corregida: {warped.shape[1]}x{warped.shape[0]} px")
        
        # Guardar resultados
        cv2.imwrite('test_warped.jpg', warped)
        cv2.imwrite('test_binary.jpg', binary)
        
        print(f"\n💾 Archivos guardados:")
        print(f"   - test_warped.jpg (hoja con perspectiva corregida)")
        print(f"   - test_binary.jpg (imagen binaria para OMR)")
        
        # Mostrar imágenes
        cv2.imshow('Original', image)
        cv2.imshow('Perspectiva Corregida', warped)
        cv2.imshow('Binaria para OMR', binary)
        
        print(f"\nPresiona cualquier tecla para cerrar las ventanas...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("❌ No se pudo procesar la hoja")
        
        # Mostrar imagen original
        cv2.imshow('Imagen Original', image)
        print("\nPresiona cualquier tecla para cerrar...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    """Función principal"""
    print("╔════════════════════════════════════════════════════╗")
    print("║   TEST DE DETECCIÓN ARUCO - Test Scanner          ║")
    print("╚════════════════════════════════════════════════════╝\n")
    
    # Mostrar opciones
    print("Opciones:")
    print("1. Probar con cámara en tiempo real")
    print("2. Probar con imagen estática")
    print("3. Salir")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    if choice == '1':
        test_with_camera()
    elif choice == '2':
        image_path = input("Ingresa la ruta de la imagen: ").strip()
        test_with_image(image_path)
    elif choice == '3':
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción inválida")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)