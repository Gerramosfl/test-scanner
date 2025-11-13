"""
Módulo para detección OMR (Optical Mark Recognition) en hojas de respuesta.

Este módulo analiza círculos en la imagen procesada para determinar
cuáles están marcados y extraer la matrícula y respuestas del alumno.

Author: Gerson
Date: 2025
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..utils.constants import (
    MIN_FILL_PERCENTAGE,
    MAX_FILL_PERCENTAGE,
    MATRICULA_DIGITS,
    NUM_ALTERNATIVES
)


class OMRDetector:
    """
    Clase para detectar marcas en círculos de hojas de respuesta.

    Utiliza análisis de píxeles oscuros dentro de cada círculo para
    determinar si está marcado con bolígrafo.
    """

    def __init__(self, calibration_file: str = "config/calibration_data.json"):
        """
        Inicializa el detector OMR con los datos de calibración.

        Args:
            calibration_file: Ruta al archivo JSON con las coordenadas de los círculos
        """
        self.calibration_file = calibration_file
        self.calibration_data = self._load_calibration()

        # Umbrales de detección
        self.min_fill = MIN_FILL_PERCENTAGE
        self.max_fill = MAX_FILL_PERCENTAGE

    def _load_calibration(self) -> Dict:
        """
        Carga los datos de calibración desde el archivo JSON.

        Returns:
            Diccionario con los datos de calibración

        Raises:
            FileNotFoundError: Si no existe el archivo de calibración
            json.JSONDecodeError: Si el archivo JSON está mal formado
        """
        calibration_path = Path(self.calibration_file)

        if not calibration_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de calibración: {self.calibration_file}\n"
                "Ejecuta primero la herramienta de calibración."
            )

        with open(calibration_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def calculate_fill_percentage(self, image: np.ndarray, x: int, y: int, radius: int) -> float:
        """
        Calcula el porcentaje de píxeles oscuros dentro de un círculo.

        Args:
            image: Imagen en escala de grises
            x, y: Coordenadas del centro del círculo
            radius: Radio del círculo en píxeles

        Returns:
            Porcentaje de píxeles oscuros (0-100)
        """
        # Con escáner de alta resolución (300 DPI), podemos usar un radio mayor
        # 0.7 = 70% del radio para buena precisión sin interferencia de círculos vecinos
        effective_radius = int(radius * 0.7)

        # Crear máscara circular
        height, width = image.shape
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, (x, y), effective_radius, 255, -1)

        # Extraer píxeles dentro del círculo
        circle_pixels = image[mask == 255]

        if len(circle_pixels) == 0:
            return 0.0

        # Calcular umbral adaptativo basado en la mediana de la imagen
        # Esto ayuda a manejar diferentes condiciones de iluminación
        threshold = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]

        # Contar píxeles oscuros (por debajo del umbral)
        dark_pixels = np.sum(circle_pixels < threshold)
        total_pixels = len(circle_pixels)

        percentage = (dark_pixels / total_pixels) * 100

        return percentage

    def is_circle_marked(self, image: np.ndarray, x: int, y: int, radius: int) -> Tuple[bool, float, str]:
        """
        Determina si un círculo está marcado.

        Args:
            image: Imagen en escala de grises
            x, y: Coordenadas del centro del círculo
            radius: Radio del círculo

        Returns:
            Tupla de (está_marcado, porcentaje_relleno, estado):
            - está_marcado: True si el círculo está marcado correctamente
            - porcentaje_relleno: Porcentaje de píxeles oscuros
            - estado: 'marked', 'empty', 'ambiguous', 'overfilled'
        """
        fill_percentage = self.calculate_fill_percentage(image, x, y, radius)

        if fill_percentage >= self.min_fill and fill_percentage <= self.max_fill:
            return True, fill_percentage, 'marked'
        elif fill_percentage < self.min_fill:
            return False, fill_percentage, 'empty'
        elif fill_percentage > self.max_fill:
            return False, fill_percentage, 'overfilled'
        else:
            return False, fill_percentage, 'ambiguous'

    def detect_matricula(self, image: np.ndarray) -> Dict:
        """
        Detecta el número de matrícula marcado en la hoja usando comparación relativa.

        En lugar de usar umbral absoluto, compara todos los círculos de cada columna
        y selecciona el más oscuro (el marcado con bolígrafo).

        Args:
            image: Imagen preprocesada en escala de grises

        Returns:
            Diccionario con:
            - 'success': bool - True si se detectó correctamente
            - 'matricula': str - Número de matrícula (10 dígitos)
            - 'confidence': float - Nivel de confianza (0-100)
            - 'details': dict - Información detallada por columna
            - 'errors': list - Lista de errores encontrados
        """
        result = {
            'success': False,
            'matricula': '',
            'confidence': 0.0,
            'details': {},
            'errors': []
        }

        matricula_circles = self.calibration_data['matricula']
        detected_digits = []

        # Umbral de diferencia mínima (15%) para considerar que un círculo está marcado
        # Si un círculo es 15% más oscuro que los demás, es el marcado
        MIN_DIFFERENCE_PERCENTAGE = 15.0

        # Umbral mínimo para considerar que hay intención de marcar (75%)
        # El texto impreso dentro de los círculos oscurece entre 45-70%, por eso usamos 75%
        MIN_FILL_THRESHOLD = 75.0

        # Procesar cada columna (10 columnas para 10 dígitos)
        for col in range(1, MATRICULA_DIGITS + 1):
            # Obtener círculos de esta columna
            col_circles = [c for c in matricula_circles if c['columna'] == col]

            if not col_circles:
                result['errors'].append(f"No se encontraron círculos para columna {col}")
                continue

            # Medir el porcentaje de relleno de TODOS los círculos de esta columna
            fill_percentages = []
            for circle in col_circles:
                fill_pct = self.calculate_fill_percentage(
                    image,
                    circle['x'],
                    circle['y'],
                    circle['radius']
                )
                fill_percentages.append({
                    'digito': circle['digito'],
                    'fill_percentage': fill_pct
                })

            # Ordenar por porcentaje de relleno (mayor a menor)
            fill_percentages.sort(key=lambda x: x['fill_percentage'], reverse=True)

            # El círculo más oscuro es el candidato
            darkest = fill_percentages[0]
            second_darkest = fill_percentages[1] if len(fill_percentages) > 1 else {'fill_percentage': 0}

            # Verificar que el más oscuro sea SIGNIFICATIVAMENTE más oscuro que el segundo
            difference = darkest['fill_percentage'] - second_darkest['fill_percentage']

            if difference >= MIN_DIFFERENCE_PERCENTAGE and darkest['fill_percentage'] >= MIN_FILL_THRESHOLD:
                # Hay una marca clara Y supera el umbral mínimo de relleno
                detected_digits.append(str(darkest['digito']))
                result['details'][f'col_{col}'] = {
                    'digito': darkest['digito'],
                    'fill_percentage': darkest['fill_percentage'],
                    'difference': difference
                }
            else:
                # No hay diferencia suficiente o no supera el umbral mínimo (sin marcar o marca ambigua)
                if darkest['fill_percentage'] < MIN_FILL_THRESHOLD:
                    result['errors'].append(f"Columna {col}: Sin marca (relleno máximo: {darkest['fill_percentage']:.1f}%)")
                else:
                    result['errors'].append(f"Columna {col}: Marca ambigua (diferencia: {difference:.1f}%)")
                detected_digits.append('?')

        # Construir matrícula
        result['matricula'] = ''.join(detected_digits)

        # Calcular confianza
        valid_digits = sum(1 for d in detected_digits if d != '?')
        result['confidence'] = (valid_digits / MATRICULA_DIGITS) * 100

        # Determinar éxito
        result['success'] = valid_digits == MATRICULA_DIGITS and len(result['errors']) == 0

        return result

    def detect_respuestas(self, image: np.ndarray) -> Dict:
        """
        Detecta las respuestas marcadas en la hoja usando comparación relativa.

        En lugar de usar umbral absoluto, compara todos los círculos de cada pregunta
        y selecciona el más oscuro (el marcado con bolígrafo).

        Args:
            image: Imagen preprocesada en escala de grises

        Returns:
            Diccionario con:
            - 'success': bool - True si se detectaron todas las respuestas
            - 'respuestas': dict - Diccionario {pregunta: alternativa}
            - 'confidence': float - Nivel de confianza (0-100)
            - 'details': dict - Información detallada por pregunta
            - 'errors': list - Lista de errores encontrados
        """
        result = {
            'success': False,
            'respuestas': {},
            'confidence': 0.0,
            'details': {},
            'errors': []
        }

        respuestas_circles = self.calibration_data['respuestas']

        # Umbral de diferencia mínima (15%) para considerar que un círculo está marcado
        # Si un círculo es 15% más oscuro que los demás, es el marcado
        MIN_DIFFERENCE_PERCENTAGE = 15.0

        # Procesar cada pregunta (1-100)
        for pregunta in range(1, 101):
            # Obtener círculos de esta pregunta
            pregunta_circles = [c for c in respuestas_circles if c['pregunta'] == pregunta]

            if not pregunta_circles:
                result['errors'].append(f"No se encontraron círculos para pregunta {pregunta}")
                continue

            # Medir el porcentaje de relleno de TODAS las alternativas de esta pregunta
            fill_percentages = []
            for circle in pregunta_circles:
                fill_pct = self.calculate_fill_percentage(
                    image,
                    circle['x'],
                    circle['y'],
                    circle['radius']
                )
                fill_percentages.append({
                    'alternativa': circle['alternativa'],
                    'fill_percentage': fill_pct
                })

            # Ordenar por porcentaje de relleno (mayor a menor)
            fill_percentages.sort(key=lambda x: x['fill_percentage'], reverse=True)

            # El círculo más oscuro es el candidato
            darkest = fill_percentages[0]
            second_darkest = fill_percentages[1] if len(fill_percentages) > 1 else {'fill_percentage': 0}

            # Verificar que el más oscuro sea SIGNIFICATIVAMENTE más oscuro que el segundo
            difference = darkest['fill_percentage'] - second_darkest['fill_percentage']

            # Umbral mínimo para considerar que hay intención de marcar (75%)
            # Esto evita falsos positivos cuando ninguna alternativa está realmente marcada
            # El texto impreso dentro de los círculos oscurece entre 45-70%, por eso usamos 75%
            MIN_FILL_THRESHOLD = 75.0

            if difference >= MIN_DIFFERENCE_PERCENTAGE and darkest['fill_percentage'] >= MIN_FILL_THRESHOLD:
                # Hay una marca clara Y supera el umbral mínimo de relleno
                result['respuestas'][pregunta] = darkest['alternativa']
                result['details'][pregunta] = {
                    'status': 'ok',
                    'alternativa': darkest['alternativa'],
                    'fill_percentage': darkest['fill_percentage'],
                    'difference': difference
                }
            else:
                # Diferencia < 15%: puede ser múltiple marca o sin marca
                # Verificar si el más oscuro supera el umbral mínimo
                if darkest['fill_percentage'] >= MIN_FILL_THRESHOLD:
                    # MÚLTIPLE MARCA: Hay al menos una marca real y poca diferencia
                    # Identificar las alternativas que están MUY CERCANAS en intensidad a la más oscura
                    # (dentro del 15% de diferencia respecto a la más oscura)
                    MAX_RANGE_FROM_DARKEST = 15.0
                    marked_alternatives = [
                        fp['alternativa']
                        for fp in fill_percentages
                        if (darkest['fill_percentage'] - fp['fill_percentage']) <= MAX_RANGE_FROM_DARKEST
                        and fp['fill_percentage'] >= MIN_FILL_THRESHOLD
                    ]

                    # Solo considerar múltiple marca si hay al menos 2 alternativas cercanas
                    if len(marked_alternatives) >= 2:
                        result['respuestas'][pregunta] = None  # Respuesta inválida
                        result['details'][pregunta] = {
                            'status': 'multiple',
                            'marked_alternatives': marked_alternatives,
                            'difference': difference,
                            'fill_percentages': {fp['alternativa']: fp['fill_percentage'] for fp in fill_percentages}
                        }
                        result['errors'].append(
                            f"Pregunta {pregunta}: Múltiple marca detectada ({', '.join(marked_alternatives)}, "
                            f"diferencia: {difference:.1f}%)"
                        )
                    else:
                        # Solo hay 1 marca clara (caso edge, tratar como respuesta única)
                        result['respuestas'][pregunta] = darkest['alternativa']
                        result['details'][pregunta] = {
                            'status': 'ok',
                            'alternativa': darkest['alternativa'],
                            'fill_percentage': darkest['fill_percentage'],
                            'difference': difference
                        }
                else:
                    # SIN MARCA: Ninguna alternativa supera el umbral mínimo
                    result['respuestas'][pregunta] = None
                    result['details'][pregunta] = {
                        'status': 'empty',
                        'difference': difference
                    }

        # Calcular confianza
        answered = sum(1 for r in result['respuestas'].values() if r is not None)
        result['confidence'] = (answered / 100) * 100

        # Determinar éxito
        result['success'] = answered >= 90  # Aceptamos si al menos 90% están respondidas

        return result

    def detect_answer_sheet(self, preprocessed_image: np.ndarray) -> Dict:
        """
        Detecta toda la información de la hoja de respuestas.

        Esta es la función principal que combina detección de matrícula y respuestas.

        Args:
            preprocessed_image: Imagen preprocesada en escala de grises

        Returns:
            Diccionario con:
            - 'success': bool - True si se detectó todo correctamente
            - 'matricula': dict - Resultado de detección de matrícula
            - 'respuestas': dict - Resultado de detección de respuestas
            - 'overall_confidence': float - Confianza general (0-100)
        """
        result = {
            'success': False,
            'matricula': {},
            'respuestas': {},
            'overall_confidence': 0.0
        }

        try:
            # Detectar matrícula
            matricula_result = self.detect_matricula(preprocessed_image)
            result['matricula'] = matricula_result

            # Detectar respuestas
            respuestas_result = self.detect_respuestas(preprocessed_image)
            result['respuestas'] = respuestas_result

            # Calcular confianza general
            result['overall_confidence'] = (
                matricula_result['confidence'] * 0.3 +  # Matrícula vale 30%
                respuestas_result['confidence'] * 0.7    # Respuestas valen 70%
            )

            # Determinar éxito general
            result['success'] = (
                matricula_result['success'] and
                respuestas_result['success']
            )

        except Exception as e:
            result['error'] = str(e)
            result['success'] = False

        return result

    def create_visual_overlay(
        self,
        image: np.ndarray,
        detection_result: Dict,
        answer_key: Optional[Dict[int, str]] = None
    ) -> np.ndarray:
        """
        Crea una imagen con overlay visual de los resultados de detección.

        Args:
            image: Imagen BGR original (corregida por perspectiva)
            detection_result: Resultado de detect_answer_sheet()
            answer_key: Diccionario opcional con pauta de respuestas {pregunta: alternativa}

        Returns:
            Imagen con overlay visual (círculos de colores)
        """
        overlay = image.copy()

        # Colores (BGR)
        COLOR_CORRECT = (0, 255, 0)      # Verde
        COLOR_INCORRECT = (0, 0, 255)    # Rojo
        COLOR_CORRECT_ANSWER = (0, 255, 255)  # Amarillo
        COLOR_EMPTY = (128, 128, 128)    # Gris
        COLOR_MULTIPLE = (0, 165, 255)   # Naranja

        # Dibujar círculos de matrícula
        matricula_circles = self.calibration_data['matricula']
        matricula_detected = detection_result['matricula'].get('details', {})

        for circle in matricula_circles:
            col = circle['columna']
            digit = circle['digito']
            col_key = f'col_{col}'

            # Verificar si este círculo fue detectado
            if col_key in matricula_detected:
                detected = matricula_detected[col_key]
                if isinstance(detected, dict) and 'selected' in detected:
                    # Múltiples marcas
                    if detected['selected']['digito'] == digit:
                        color = COLOR_MULTIPLE
                        cv2.circle(overlay, (circle['x'], circle['y']), circle['radius'], color, 2)
                elif detected['digito'] == digit:
                    # Marca correcta
                    color = COLOR_CORRECT
                    cv2.circle(overlay, (circle['x'], circle['y']), circle['radius'], color, 2)

        # Dibujar círculos de respuestas
        respuestas_circles = self.calibration_data['respuestas']
        respuestas_detected = detection_result['respuestas'].get('respuestas', {})
        respuestas_details = detection_result['respuestas'].get('details', {})

        for circle in respuestas_circles:
            pregunta = circle['pregunta']
            alternativa = circle['alternativa']

            if pregunta in respuestas_detected:
                detected_alt = respuestas_detected[pregunta]
                detail = respuestas_details.get(pregunta, {})

                # Determinar color según el estado
                if detail.get('status') == 'empty':
                    # Sin respuesta - no dibujar nada o dibujar gris muy tenue
                    continue
                elif detail.get('status') == 'multiple':
                    # Múltiples marcas - marcar TODAS las alternativas marcadas en rojo
                    marked_alternatives = detail.get('marked_alternatives', [])
                    if alternativa in marked_alternatives:
                        color = COLOR_INCORRECT
                        cv2.circle(overlay, (circle['x'], circle['y']), circle['radius'], color, 2)
                    # NO dibujar círculo amarillo para la respuesta correcta
                elif alternativa == detected_alt:
                    # Respuesta marcada
                    if answer_key and pregunta in answer_key:
                        # Comparar con pauta
                        correct_alt = answer_key[pregunta]
                        if detected_alt == correct_alt:
                            color = COLOR_CORRECT
                        else:
                            color = COLOR_INCORRECT
                            # Marcar también la respuesta correcta en amarillo
                            correct_circle = next(
                                (c for c in respuestas_circles
                                 if c['pregunta'] == pregunta and c['alternativa'] == correct_alt),
                                None
                            )
                            if correct_circle:
                                cv2.circle(
                                    overlay,
                                    (correct_circle['x'], correct_circle['y']),
                                    correct_circle['radius'],
                                    COLOR_CORRECT_ANSWER,
                                    2
                                )
                    else:
                        # Sin pauta, solo marcar como detectado
                        color = (255, 0, 255)  # Magenta

                    cv2.circle(overlay, (circle['x'], circle['y']), circle['radius'], color, 2)

        return overlay


# Función de conveniencia para usar sin instanciar la clase
_detector_instance = None

def get_omr_detector(calibration_file: str = "config/calibration_data.json") -> OMRDetector:
    """
    Obtiene una instancia singleton del OMRDetector.

    Args:
        calibration_file: Ruta al archivo de calibración

    Returns:
        Instancia de OMRDetector
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = OMRDetector(calibration_file)
    return _detector_instance
