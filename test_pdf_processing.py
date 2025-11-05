"""
Script temporal para probar el procesamiento completo de PDFs escaneados.

Este script:
1. Convierte PDF a imagen de alta resolución
2. Detecta marcadores ArUco y corrige perspectiva
3. Aplica detección OMR para leer matrícula y respuestas
4. Muestra resultados detallados
5. Guarda imagen con overlay visual

NOTA: Este archivo es temporal y será eliminado en la versión final.

Uso:
    python test_pdf_processing.py <ruta_al_pdf>

Example:
    python test_pdf_processing.py hoja_alumno_001.pdf

Author: Gerson
Date: 2025
"""

import sys
import cv2
from pathlib import Path
from src.core.pdf_processor import PDFProcessor
from src.core.image_processor import ImageProcessor
from src.core.omr_detector import OMRDetector


def print_detection_results(detection_result: dict, pdf_name: str):
    """Imprime los resultados de detección en formato legible."""
    print("\n" + "=" * 80)
    print(f"RESULTADOS - {pdf_name}")
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

    # Mostrar primeras 20 respuestas
    respuestas = respuestas_data.get('respuestas', {})
    if respuestas:
        print(f"\n  Primeras 20 respuestas:")
        for i in range(1, min(21, len(respuestas) + 1)):
            if i in respuestas:
                resp = respuestas[i] if respuestas[i] else '(vacía)'
                print(f"    P{i:3d}: {resp}", end="    ")
                if i % 5 == 0:
                    print()  # Nueva línea cada 5 respuestas

    # Errores
    if respuestas_data.get('errors'):
        error_count = len(respuestas_data['errors'])
        print(f"\n  Errores encontrados: {error_count}")
        if error_count <= 10:
            for error in respuestas_data['errors']:
                print(f"    - {error}")
        else:
            print(f"    (Mostrando primeros 10 de {error_count})")
            for error in respuestas_data['errors'][:10]:
                print(f"    - {error}")

    # Confianza general
    print(f"\n🎯 CONFIANZA GENERAL: {detection_result.get('overall_confidence', 0):.1f}%")
    print("=" * 80 + "\n")


def main():
    """Función principal del script de prueba."""
    print("=" * 80)
    print("SCRIPT DE PRUEBA - PROCESAMIENTO DE PDFs ESCANEADOS")
    print("=" * 80)

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ Error: Debes proporcionar la ruta al PDF")
        print("\nUso:")
        print("  python test_pdf_processing.py <ruta_al_pdf>")
        print("\nEjemplo:")
        print("  python test_pdf_processing.py hoja_alumno_001.pdf")
        print("\nTambién puedes procesar múltiples PDFs:")
        print("  python test_pdf_processing.py hoja1.pdf hoja2.pdf hoja3.pdf")
        return

    pdf_paths = sys.argv[1:]
    print(f"\n📄 PDFs a procesar: {len(pdf_paths)}")

    try:
        # Inicializar procesadores
        print("\nInicializando módulos...")
        pdf_processor = PDFProcessor(dpi=300)
        image_processor = ImageProcessor()
        omr_detector = OMRDetector()
        print("✓ Módulos inicializados")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de haber ejecutado:")
        print("  python calibrate_from_pdf.py <hoja_blanca_escaneada.pdf>")
        return
    except Exception as e:
        print(f"\n❌ Error al inicializar: {e}")
        return

    # Procesar cada PDF
    results = []
    for idx, pdf_path in enumerate(pdf_paths, 1):
        print(f"\n{'='*80}")
        print(f"PROCESANDO PDF {idx}/{len(pdf_paths)}: {pdf_path}")
        print(f"{'='*80}")

        if not Path(pdf_path).exists():
            print(f"❌ Archivo no encontrado: {pdf_path}")
            continue

        # Paso 1: Convertir PDF a imagen
        print("\n[1/4] Convirtiendo PDF a imagen...")
        image = pdf_processor.pdf_to_image(pdf_path)
        if image is None:
            print("❌ Error al convertir PDF")
            continue
        print(f"✓ PDF convertido: {image.shape[1]}x{image.shape[0]} píxeles")

        # Paso 2: Procesar con ArUco
        print("\n[2/4] Detectando ArUco y corrigiendo perspectiva...")
        process_result = image_processor.process_answer_sheet(image)
        if not process_result['success']:
            print(f"❌ {process_result['message']}")
            continue
        print(f"✓ {process_result['message']}")

        # Paso 3: Detección OMR
        print("\n[3/4] Aplicando detección OMR...")
        detection_result = omr_detector.detect_answer_sheet(process_result['preprocessed'])

        # Paso 4: Crear overlay visual y guardar
        print("\n[4/4] Generando visualización...")
        overlay = omr_detector.create_visual_overlay(
            process_result['warped_image'],
            detection_result
        )

        # Guardar imagen con overlay
        pdf_name = Path(pdf_path).stem
        output_path = f"result_{pdf_name}.jpg"
        cv2.imwrite(output_path, overlay)
        print(f"✓ Visualización guardada: {output_path}")

        # Guardar resultados
        results.append({
            'pdf_name': pdf_name,
            'detection': detection_result,
            'success': detection_result['success'],
            'output_image': output_path
        })

        # Mostrar resultados
        print_detection_results(detection_result, pdf_name)

    # Resumen final
    if results:
        print("\n" + "=" * 80)
        print("RESUMEN FINAL")
        print("=" * 80)
        print(f"\nPDFs procesados: {len(results)}")
        successful = sum(1 for r in results if r['success'])
        print(f"Exitosos: {successful}/{len(results)}")
        print(f"Con errores: {len(results) - successful}/{len(results)}")

        print("\nDetalles:")
        for r in results:
            status = "✓" if r['success'] else "✗"
            matricula = r['detection']['matricula'].get('matricula', 'N/A')
            conf = r['detection'].get('overall_confidence', 0)
            print(f"  {status} {r['pdf_name']:30s} | Matrícula: {matricula:12s} | Confianza: {conf:5.1f}%")

        print("\nArchivos generados:")
        for r in results:
            print(f"  - {r['output_image']}")

        print("\n" + "=" * 80)
    else:
        print("\n❌ No se procesó ningún PDF exitosamente")


if __name__ == "__main__":
    main()
