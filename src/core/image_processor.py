"""
Procesador de imágenes para detección de hojas de respuestas
Incluye detección de marcadores ArUco y corrección de perspectiva
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict


class ImageProcessor:
    """
    Procesa imágenes de hojas de respuestas usando marcadores ArUco
    """
    
    def __init__(self, aruco_dict_type=cv2.aruco.DICT_4X4_50):
        """
        Inicializa el procesador de imágenes
        
        Args:
            aruco_dict_type: Tipo de diccionario ArUco a usar
        """
        # Inicializar detector ArUco
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        # Dimensiones esperadas de la hoja después de corrección (en píxeles)
        # Carta: 8.5" x 11" a 300 DPI = 2550 x 3300 píxeles
        self.output_width = 2550
        self.output_height = 3300
    
    def detect_aruco_markers(self, image: np.ndarray) -> Tuple[bool, Optional[Dict], np.ndarray]:
        """
        Detecta marcadores ArUco en la imagen
        
        Args:
            image: Imagen de entrada (BGR)
        
        Returns:
            Tuple con:
            - success: True si se detectaron exactamente 4 marcadores
            - markers_dict: Diccionario con {id: corners}
            - image_with_markers: Imagen con marcadores dibujados
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar marcadores
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        # Crear copia de imagen para dibujar
        image_copy = image.copy()
        
        # Verificar que se detectaron exactamente 4 marcadores
        if ids is None or len(ids) != 4:
            return False, None, image_copy
        
        # Dibujar marcadores detectados
        cv2.aruco.drawDetectedMarkers(image_copy, corners, ids)
        
        # Crear diccionario de marcadores {id: corners}
        markers_dict = {}
        for i, marker_id in enumerate(ids.flatten()):
            markers_dict[marker_id] = corners[i][0]
        
        return True, markers_dict, image_copy
    
    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Ordena 4 puntos en orden: top-left, top-right, bottom-right, bottom-left
        
        Args:
            pts: Array de 4 puntos [(x,y), (x,y), (x,y), (x,y)]
        
        Returns:
            Puntos ordenados
        """
        # Inicializar array de puntos ordenados
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left: suma mínima, bottom-right: suma máxima
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right: diferencia mínima, bottom-left: diferencia máxima
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def get_marker_centers(self, markers_dict: Dict) -> Dict:
        """
        Calcula el centro de cada marcador ArUco
        
        Args:
            markers_dict: Diccionario con {id: corners}
        
        Returns:
            Diccionario con {id: (center_x, center_y)}
        """
        centers = {}
        for marker_id, corners in markers_dict.items():
            # Calcular centro como promedio de las 4 esquinas
            center_x = np.mean(corners[:, 0])
            center_y = np.mean(corners[:, 1])
            centers[marker_id] = (center_x, center_y)
        
        return centers
    
    def correct_perspective(self, image: np.ndarray, markers_dict: Dict) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Corrige la perspectiva de la hoja usando los 4 marcadores ArUco
        
        Args:
            image: Imagen original
            markers_dict: Diccionario con marcadores detectados
        
        Returns:
            Tuple con:
            - success: True si se pudo corregir la perspectiva
            - warped_image: Imagen con perspectiva corregida
        """
        # Verificar que tenemos exactamente 4 marcadores
        if len(markers_dict) != 4:
            return False, None
        
        # Obtener centros de los marcadores
        centers = self.get_marker_centers(markers_dict)
        
        # Convertir a array de puntos
        points = np.array(list(centers.values()), dtype="float32")
        
        # Ordenar puntos: TL, TR, BR, BL
        ordered_points = self.order_points(points)
        
        # Definir puntos de destino (esquinas de la hoja)
        dst_points = np.array([
            [0, 0],
            [self.output_width - 1, 0],
            [self.output_width - 1, self.output_height - 1],
            [0, self.output_height - 1]
        ], dtype="float32")
        
        # Calcular matriz de transformación de perspectiva
        matrix = cv2.getPerspectiveTransform(ordered_points, dst_points)
        
        # Aplicar transformación
        warped = cv2.warpPerspective(image, matrix, (self.output_width, self.output_height))
        
        return True, warped
    
    def preprocess_for_omr(self, image: np.ndarray) -> np.ndarray:
        """
        Pre-procesa la imagen para detección OMR
        
        Args:
            image: Imagen con perspectiva corregida
        
        Returns:
            Imagen procesada (binaria)
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro Gaussiano para reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Binarización usando umbral de Otsu
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        return binary
    
    def process_sheet(self, image: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray], str]:
        """
        Proceso completo: detecta marcadores, corrige perspectiva y pre-procesa
        
        Args:
            image: Imagen de entrada
        
        Returns:
            Tuple con:
            - success: True si el proceso fue exitoso
            - warped_image: Imagen con perspectiva corregida (color)
            - binary_image: Imagen binaria para OMR
            - message: Mensaje de error o éxito
        """
        # Paso 1: Detectar marcadores ArUco
        success, markers_dict, image_with_markers = self.detect_aruco_markers(image)
        
        if not success:
            return False, None, None, "No se detectaron 4 marcadores ArUco. Asegúrese de que todos los marcadores sean visibles."
        
        # Paso 2: Corregir perspectiva
        success, warped = self.correct_perspective(image, markers_dict)
        
        if not success:
            return False, None, None, "Error al corregir la perspectiva de la hoja."
        
        # Paso 3: Pre-procesar para OMR
        binary = self.preprocess_for_omr(warped)
        
        return True, warped, binary, "Hoja procesada correctamente"
    
    def draw_detection_info(self, image: np.ndarray, markers_dict: Dict) -> np.ndarray:
        """
        Dibuja información de detección sobre la imagen
        
        Args:
            image: Imagen original
            markers_dict: Marcadores detectados
        
        Returns:
            Imagen con información dibujada
        """
        image_copy = image.copy()
        
        # Dibujar marcadores
        for marker_id, corners in markers_dict.items():
            # Dibujar contorno del marcador
            corners_int = corners.astype(int)
            cv2.polylines(image_copy, [corners_int], True, (0, 255, 0), 3)
            
            # Calcular centro
            center = corners.mean(axis=0).astype(int)
            
            # Dibujar ID del marcador
            cv2.circle(image_copy, tuple(center), 5, (0, 0, 255), -1)
            cv2.putText(image_copy, f"ID: {marker_id}", 
                       tuple(center + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.8, (255, 0, 0), 2)
        
        return image_copy