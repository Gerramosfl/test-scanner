"""
Script para diagnosticar los porcentajes de relleno detectados
"""

import sys
from pathlib import Path
from src.core.pdf_processor import PDFProcessor
from src.core.image_processor import ImageProcessor
from src.core.omr_detector import OMRDetector


def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_fill_percentages.py <pdf_path>")
        return

    pdf_path = sys.argv[1]

    # Procesar PDF
    pdf_processor = PDFProcessor(dpi=300)
    image_processor = ImageProcessor()
    omr_detector = OMRDetector()

    # Convertir y procesar
    image = pdf_processor.pdf_to_image(pdf_path)
    if image is None:
        print("Error al convertir PDF")
        return

    process_result = image_processor.process_answer_sheet(image)
    if not process_result['success']:
        print(f"Error: {process_result['message']}")
        return

    # Detectar respuestas
    detection_result = omr_detector.detect_answer_sheet(process_result['preprocessed'])

    # Mostrar detalles de preguntas específicas
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE PORCENTAJES DE RELLENO")
    print("="*80)

    # Preguntas problemáticas: 20 y 68
    problematic_questions = [20, 68]

    for pregunta in problematic_questions:
        print(f"\n{'='*80}")
        print(f"PREGUNTA {pregunta}")
        print(f"{'='*80}")

        detail = detection_result['respuestas']['details'].get(pregunta, {})

        if 'fill_percentages' in detail:
            print("\nPorcentajes de relleno de TODAS las alternativas:")
            fill_percs = detail['fill_percentages']
            for alt in ['A', 'B', 'C', 'D', 'E']:
                pct = fill_percs.get(alt, 0)
                print(f"  {alt}: {pct:.2f}%")

            print(f"\nEstado detectado: {detail.get('status', 'N/A')}")

            if detail.get('status') == 'multiple':
                print(f"Alternativas marcadas: {detail.get('marked_alternatives', [])}")
                print(f"Diferencia entre más oscura y segunda: {detail.get('difference', 0):.2f}%")
        else:
            # Solo tiene info básica
            print(f"Alternativa detectada: {detection_result['respuestas']['respuestas'].get(pregunta, 'None')}")
            print(f"Estado: {detail.get('status', 'N/A')}")

    # Mostrar todas las preguntas con porcentajes bajos (posibles falsos positivos)
    print(f"\n{'='*80}")
    print("TODAS LAS PREGUNTAS CON DETECCIÓN SOSPECHOSA")
    print(f"{'='*80}")

    for pregunta in range(1, 101):
        detail = detection_result['respuestas']['details'].get(pregunta, {})
        respuesta = detection_result['respuestas']['respuestas'].get(pregunta)

        if 'fill_percentages' in detail:
            fill_percs = detail['fill_percentages']
            max_pct = max(fill_percs.values())

            # Mostrar si el máximo está entre 50% y 70% (zona sospechosa)
            if 50 <= max_pct <= 70 and respuesta is not None:
                print(f"\nPregunta {pregunta}: Respuesta={respuesta}, Max fill={max_pct:.1f}%")
                for alt in ['A', 'B', 'C', 'D', 'E']:
                    print(f"  {alt}: {fill_percs.get(alt, 0):.1f}%")


if __name__ == "__main__":
    main()
