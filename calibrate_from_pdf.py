"""
Script para calibrar el sistema usando un PDF escaneado de hoja en blanco.

Este script:
1. Convierte el PDF a imagen de alta resolución
2. Detecta marcadores ArUco y corrige perspectiva
3. Permite calibrar manualmente las posiciones de los círculos
4. Genera config/calibration_data.json

NOTA: Este archivo es temporal y será eliminado en la versión final.

Uso:
    python calibrate_from_pdf.py <ruta_al_pdf>

Example:
    python calibrate_from_pdf.py hoja_blanca_escaneada.pdf

Author: Gerson
Date: 2025
"""

import sys
import cv2
from pathlib import Path
from src.core.pdf_processor import PDFProcessor
from src.core.image_processor import ImageProcessor
from calibration_tool import CalibrationTool


def main():
    """Función principal del script."""
    print("=" * 80)
    print("CALIBRACIÓN DESDE PDF ESCANEADO")
    print("=" * 80)

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ Error: Debes proporcionar la ruta al PDF")
        print("\nUso:")
        print("  python calibrate_from_pdf.py <ruta_al_pdf>")
        print("\nEjemplo:")
        print("  python calibrate_from_pdf.py hoja_blanca_escaneada.pdf")
        return

    pdf_path = sys.argv[1]

    # Verificar que el archivo existe
    if not Path(pdf_path).exists():
        print(f"\n❌ Error: No se encontró el archivo: {pdf_path}")
        return

    print(f"\n📄 PDF de entrada: {pdf_path}")

    # Paso 1: Convertir PDF a imagen
    print("\n[1/4] Convirtiendo PDF a imagen...")
    pdf_processor = PDFProcessor(dpi=300)  # 300 DPI para escáneres

    # Validar PDF
    is_valid, message = pdf_processor.validate_pdf(pdf_path)
    if not is_valid:
        print(f"❌ {message}")
        return
    else:
        print(f"✓ {message}")

    # Convertir a imagen
    image = pdf_processor.pdf_to_image(pdf_path)
    if image is None:
        print("❌ Error al convertir PDF a imagen")
        return

    print(f"✓ PDF convertido: {image.shape[1]}x{image.shape[0]} píxeles")

    # Paso 2: Detectar ArUco y corregir perspectiva
    print("\n[2/4] Detectando marcadores ArUco y corrigiendo perspectiva...")
    image_processor = ImageProcessor()

    result = image_processor.process_answer_sheet(image)

    if not result['success']:
        print(f"❌ {result['message']}")
        print("\nPosibles causas:")
        print("  - Los marcadores ArUco no son visibles")
        print("  - El PDF está en baja resolución")
        print("  - La hoja está muy mal alineada")
        return

    print(f"✓ {result['message']}")
    print(f"  Marcadores detectados: {result['marker_ids']}")

    # Guardar imagen corregida para calibración
    calibration_image_path = "calibration_image_from_pdf.jpg"
    cv2.imwrite(calibration_image_path, result['warped_image'])
    print(f"✓ Imagen corregida guardada: {calibration_image_path}")

    # Paso 3: Calibración manual
    print("\n[3/4] Iniciando calibración manual...")
    print("=" * 80)
    print("INSTRUCCIONES:")
    print("  1. Haz click en el CENTRO de cada círculo cuando se te indique")
    print("  2. Debes marcar 16 puntos en total (4 matrícula + 12 respuestas)")
    print("  3. Presiona 'R' si te equivocas para reiniciar")
    print("  4. Presiona 'S' cuando termines para guardar")
    print("=" * 80)
    input("\nPresiona ENTER para comenzar la calibración...")

    try:
        tool = CalibrationTool(calibration_image_path)

        if tool.run():
            # Paso 4: Guardar calibración
            print("\n[4/4] Guardando calibración...")
            output_path = "config/calibration_data.json"
            tool.save_calibration(output_path)

            # Visualizar
            tool.visualize_calibration()

            print("\n" + "=" * 80)
            print("✅ ¡CALIBRACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 80)
            print(f"Archivo generado: {output_path}")
            print("\nArchivos generados:")
            print(f"  - {output_path} (datos de calibración)")
            print(f"  - calibration_visualization.jpg (visualización)")
            print(f"  - {calibration_image_path} (imagen procesada)")
            print("\nYa puedes:")
            print("  1. Usar el sistema para calificar hojas escaneadas")
            print("  2. Borrar archivos temporales: calibration_image_from_pdf.jpg")
            print("=" * 80)
        else:
            print("\n⚠️ Calibración cancelada")

    except Exception as e:
        print(f"\n❌ Error durante la calibración: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
