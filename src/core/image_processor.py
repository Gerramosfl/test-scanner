"""
Módulo para procesamiento de imágenes y detección de marcadores ArUco.

Este módulo maneja:
- Detección de marcadores ArUco en las esquinas de la hoja de respuestas
- Corrección de perspectiva para obtener una vista "plana" de la hoja
- Preprocesamiento de imágenes para mejorar la detección OMR

Author: Gerson
Date: 2025
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, List
from ..utils.constants import (
    ARUCO_DICT,
    PAPER_WIDTH_MM,
    PAPER_HEIGHT_MM
)


class ImageProcessor:
    """
    Clase para procesar imágenes de hojas de respuesta.

    Maneja la detección de marcadores ArUco y la corrección de perspectiva
    para convertir la imagen capturada en una vista normalizada de la hoja.
    """

    # Resolución de salida (equivalente a ~200 DPI para papel carta)
    OUTPUT_WIDTH = 1700
    OUTPUT_HEIGHT = 2200

    def __init__(self):
        """Inicializa el procesador de imágenes con el diccionario ArUco."""
        # Cargar el diccionario ArUco especificado en constants
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(
            getattr(cv2.aruco, ARUCO_DICT)
        )
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

    def detect_aruco_markers(self, image: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[List[int]]]:
        """
        Detecta marcadores ArUco en la imagen.

        Args:
            image: Imagen BGR de OpenCV

        Returns:
            Tupla de (éxito, esquinas, ids):
            - éxito: True si se detectaron exactamente 4 marcadores
            - esquinas: Array con las coordenadas de las esquinas de los marcadores
            - ids: Lista con los IDs de los marcadores detectados
        """
        # Convertir a escala de grises para mejor detección
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detectar marcadores ArUco
        corners, ids, rejected = self.aruco_detector.detectMarkers(gray)

        # Verificar que se detectaron exactamente 4 marcadores
        if ids is None or len(ids) != 4:
            return False, None, None

        return True, corners, ids.flatten().tolist()

    def order_marker_corners(self, corners: np.ndarray, ids: List[int]) -> Optional[np.ndarray]:
        """
        Ordena las esquinas de los marcadores ArUco en el orden correcto.

        Los marcadores deben estar ordenados como:
        - ID 0: Esquina superior izquierda (top-left)
        - ID 1: Esquina superior derecha (top-right)
        - ID 2: Esquina inferior izquierda (bottom-left)
        - ID 3: Esquina inferior derecha (bottom-right)

        Args:
            corners: Lista de esquinas detectadas por cv2.aruco.detectMarkers
            ids: Lista de IDs correspondientes a cada marcador

        Returns:
            Array numpy con 4 puntos ordenados [top-left, top-right, bottom-right, bottom-left]
            o None si no se pueden ordenar correctamente
        """
        # Crear diccionario para mapear ID a esquinas
        marker_dict = {}
        for i, marker_id in enumerate(ids):
            # Para cada marcador, tomamos el centro de sus 4 esquinas
            marker_corners = corners[i][0]  # corners[i] tiene shape (1, 4, 2)
            center = marker_corners.mean(axis=0)
            marker_dict[marker_id] = center

        # Verificar que tenemos los 4 IDs esperados
        expected_ids = [0, 1, 2, 3]
        if not all(marker_id in marker_dict for marker_id in expected_ids):
            return None

        # Ordenar según el esquema definido
        ordered_points = np.array([
            marker_dict[0],  # top-left
            marker_dict[1],  # top-right
            marker_dict[3],  # bottom-right (nota: ID 3, no 2)
            marker_dict[2],  # bottom-left
        ], dtype=np.float32)

        return ordered_points

    def apply_perspective_transform(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """
        Aplica transformación de perspectiva para obtener una vista "plana" de la hoja.

        Args:
            image: Imagen BGR de OpenCV
            corners: Array con 4 puntos ordenados [top-left, top-right, bottom-right, bottom-left]

        Returns:
            Imagen transformada con dimensiones OUTPUT_WIDTH x OUTPUT_HEIGHT
        """
        # Definir los puntos de destino (rectángulo perfecto)
        dst_points = np.array([
            [0, 0],                                          # top-left
            [self.OUTPUT_WIDTH - 1, 0],                     # top-right
            [self.OUTPUT_WIDTH - 1, self.OUTPUT_HEIGHT - 1], # bottom-right
            [0, self.OUTPUT_HEIGHT - 1]                     # bottom-left
        ], dtype=np.float32)

        # Calcular la matriz de transformación de perspectiva
        matrix = cv2.getPerspectiveTransform(corners, dst_points)

        # Aplicar la transformación
        warped = cv2.warpPerspective(
            image,
            matrix,
            (self.OUTPUT_WIDTH, self.OUTPUT_HEIGHT),
            flags=cv2.INTER_LINEAR
        )

        return warped

    def preprocess_for_omr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para mejorar la detección OMR.

        Aplica:
        - Conversión a escala de grises
        - Ecualización de histograma adaptativa (CLAHE)
        - Filtro gaussiano para reducir ruido
        - Binarización adaptativa

        Args:
            image: Imagen BGR ya corregida por perspectiva

        Returns:
            Imagen preprocesada en escala de grises, lista para detección OMR
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Mejora el contraste localmente, útil para diferentes condiciones de iluminación
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Aplicar filtro gaussiano para reducir ruido
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

        return blurred

    def process_answer_sheet(self, image: np.ndarray) -> Dict:
        """
        Procesa una imagen de hoja de respuesta completa.

        Esta es la función principal que:
        1. Detecta los marcadores ArUco
        2. Ordena las esquinas
        3. Aplica corrección de perspectiva
        4. Preprocesa la imagen para OMR

        Args:
            image: Imagen BGR de OpenCV (frame de cámara)

        Returns:
            Diccionario con:
            - 'success': bool - True si el procesamiento fue exitoso
            - 'message': str - Mensaje descriptivo del resultado
            - 'warped_image': np.ndarray - Imagen corregida (BGR)
            - 'preprocessed': np.ndarray - Imagen preprocesada para OMR (escala de grises)
            - 'corners': np.ndarray - Esquinas ordenadas de los marcadores
            - 'marker_ids': List[int] - IDs de los marcadores detectados
        """
        result = {
            'success': False,
            'message': '',
            'warped_image': None,
            'preprocessed': None,
            'corners': None,
            'marker_ids': None
        }

        # Paso 1: Detectar marcadores ArUco
        success, corners, ids = self.detect_aruco_markers(image)

        if not success:
            if ids is None:
                result['message'] = "No se detectaron marcadores ArUco. Asegúrese de que la hoja esté visible."
            else:
                result['message'] = f"Se detectaron {len(ids)} marcadores. Se requieren exactamente 4."
            return result

        result['marker_ids'] = ids

        # Paso 2: Ordenar las esquinas de los marcadores
        ordered_corners = self.order_marker_corners(corners, ids)

        if ordered_corners is None:
            result['message'] = "No se pudieron ordenar los marcadores. Verifique que los IDs sean 0, 1, 2, 3."
            return result

        result['corners'] = ordered_corners

        # Paso 3: Aplicar transformación de perspectiva
        try:
            warped = self.apply_perspective_transform(image, ordered_corners)
            result['warped_image'] = warped
        except Exception as e:
            result['message'] = f"Error al aplicar transformación de perspectiva: {str(e)}"
            return result

        # Paso 4: Preprocesar para OMR
        try:
            preprocessed = self.preprocess_for_omr(warped)
            result['preprocessed'] = preprocessed
        except Exception as e:
            result['message'] = f"Error al preprocesar imagen: {str(e)}"
            return result

        # Todo exitoso
        result['success'] = True
        result['message'] = "Hoja detectada y procesada correctamente"

        return result

    def draw_markers_debug(self, image: np.ndarray, corners: np.ndarray, ids: List[int]) -> np.ndarray:
        """
        Dibuja los marcadores detectados en la imagen para debugging.

        Args:
            image: Imagen BGR de OpenCV
            corners: Esquinas de los marcadores detectados
            ids: IDs de los marcadores

        Returns:
            Imagen con los marcadores dibujados
        """
        output = image.copy()

        # Dibujar los marcadores detectados
        if corners is not None and ids is not None:
            cv2.aruco.drawDetectedMarkers(output, corners, np.array(ids))

        return output


# Función de conveniencia para usar sin instanciar la clase
_processor_instance = None

def get_image_processor() -> ImageProcessor:
    """
    Obtiene una instancia singleton del ImageProcessor.

    Returns:
        Instancia de ImageProcessor
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = ImageProcessor()
    return _processor_instance
