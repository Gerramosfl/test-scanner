"""
Módulo para procesar PDFs de hojas de respuesta escaneadas.

Este módulo convierte páginas PDF a imágenes de alta resolución
para su posterior procesamiento con ArUco y OMR.

Author: Gerson
Date: 2025
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import fitz  # PyMuPDF


class PDFProcessor:
    """
    Clase para convertir PDFs escaneados a imágenes procesables.

    Maneja la conversión de PDFs a imágenes de alta resolución,
    optimizadas para detección ArUco y OMR.
    """

    # Resolución de conversión (DPI)
    # Los escáneres típicamente usan 300 DPI
    DEFAULT_DPI = 300

    def __init__(self, dpi: int = DEFAULT_DPI):
        """
        Inicializa el procesador de PDFs.

        Args:
            dpi: Resolución en DPI para la conversión (default: 300)
        """
        self.dpi = dpi

    def pdf_to_image(self, pdf_path: str, page_number: int = 0) -> Optional[np.ndarray]:
        """
        Convierte una página de PDF a imagen OpenCV.

        Args:
            pdf_path: Ruta al archivo PDF
            page_number: Número de página a convertir (0-indexed)

        Returns:
            Imagen BGR de OpenCV o None si hay error
        """
        try:
            # Abrir el PDF
            doc = fitz.open(pdf_path)

            # Verificar que la página existe
            if page_number >= doc.page_count:
                print(f"Error: El PDF solo tiene {doc.page_count} página(s)")
                doc.close()
                return None

            # Obtener la página
            page = doc.load_page(page_number)

            # Calcular factor de zoom para obtener el DPI deseado
            # PyMuPDF usa 72 DPI por default
            zoom = self.dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)

            # Renderizar página a imagen
            pix = page.get_pixmap(matrix=matrix)

            # Convertir a array numpy
            img_data = np.frombuffer(pix.samples, dtype=np.uint8)
            img_data = img_data.reshape(pix.height, pix.width, pix.n)

            # Convertir de RGB a BGR (OpenCV usa BGR)
            if pix.n == 3:  # RGB
                image = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            elif pix.n == 4:  # RGBA
                image = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
            else:
                image = img_data

            doc.close()

            return image

        except Exception as e:
            print(f"Error al procesar PDF: {str(e)}")
            return None

    def pdf_to_images_batch(self, pdf_paths: List[str]) -> List[Tuple[str, np.ndarray]]:
        """
        Convierte múltiples PDFs a imágenes.

        Args:
            pdf_paths: Lista de rutas a archivos PDF

        Returns:
            Lista de tuplas (nombre_archivo, imagen)
        """
        results = []

        for pdf_path in pdf_paths:
            image = self.pdf_to_image(pdf_path)
            if image is not None:
                filename = Path(pdf_path).stem
                results.append((filename, image))
            else:
                print(f"Advertencia: No se pudo procesar {pdf_path}")

        return results

    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Obtiene información de un archivo PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con información del PDF
        """
        info = {
            'exists': False,
            'page_count': 0,
            'size_bytes': 0,
            'dimensions': None,
            'error': None
        }

        try:
            path = Path(pdf_path)
            if not path.exists():
                info['error'] = "Archivo no encontrado"
                return info

            info['exists'] = True
            info['size_bytes'] = path.stat().st_size

            doc = fitz.open(pdf_path)
            info['page_count'] = doc.page_count

            if doc.page_count > 0:
                page = doc.load_page(0)
                rect = page.rect
                info['dimensions'] = (int(rect.width), int(rect.height))

            doc.close()

        except Exception as e:
            info['error'] = str(e)

        return info

    def validate_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Valida que un PDF sea procesable.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (es_válido, mensaje)
        """
        info = self.get_pdf_info(pdf_path)

        if not info['exists']:
            return False, f"Archivo no encontrado: {pdf_path}"

        if info['error']:
            return False, f"Error al leer PDF: {info['error']}"

        if info['page_count'] == 0:
            return False, "El PDF no contiene páginas"

        if info['page_count'] > 1:
            return True, f"Advertencia: PDF tiene {info['page_count']} páginas, se usará solo la primera"

        return True, "PDF válido"

    def save_image_from_pdf(self, pdf_path: str, output_path: str, page_number: int = 0) -> bool:
        """
        Convierte un PDF a imagen y la guarda.

        Args:
            pdf_path: Ruta al archivo PDF de entrada
            output_path: Ruta donde guardar la imagen
            page_number: Número de página (0-indexed)

        Returns:
            True si se guardó correctamente, False si hubo error
        """
        image = self.pdf_to_image(pdf_path, page_number)

        if image is None:
            return False

        try:
            cv2.imwrite(output_path, image)
            return True
        except Exception as e:
            print(f"Error al guardar imagen: {str(e)}")
            return False


def process_scanned_pdf(pdf_path: str) -> Optional[np.ndarray]:
    """
    Función de conveniencia para procesar un PDF escaneado.

    Args:
        pdf_path: Ruta al PDF escaneado

    Returns:
        Imagen BGR lista para procesamiento ArUco/OMR
    """
    processor = PDFProcessor()
    return processor.pdf_to_image(pdf_path)


# Instancia singleton
_processor_instance = None

def get_pdf_processor(dpi: int = 300) -> PDFProcessor:
    """
    Obtiene una instancia singleton del PDFProcessor.

    Args:
        dpi: Resolución en DPI (default: 300)

    Returns:
        Instancia de PDFProcessor
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = PDFProcessor(dpi)
    return _processor_instance
