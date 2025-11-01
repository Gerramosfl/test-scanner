"""
Herramienta de calibración para detectar posiciones de círculos en la hoja de respuestas.

Este script permite marcar manualmente puntos clave en la hoja de respuestas
y genera automáticamente las coordenadas de todos los círculos mediante interpolación.

NOTA: Este archivo es temporal y será eliminado en la versión final.

Uso:
1. Ejecutar: python calibration_tool.py
2. Seguir las instrucciones en pantalla para marcar puntos clave
3. El script generará config/calibration_data.json

Author: Gerson
Date: 2025
"""

import cv2
import json
import numpy as np
from pathlib import Path

class CalibrationTool:
    """
    Herramienta interactiva para calibrar posiciones de círculos en la hoja de respuestas.
    """

    def __init__(self, image_path: str):
        """
        Inicializa la herramienta de calibración.

        Args:
            image_path: Ruta a la imagen de calibración (hoja en blanco corregida)
        """
        self.image_path = image_path
        self.image = cv2.imread(image_path)

        if self.image is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

        self.display_image = self.image.copy()
        self.points = {}
        self.current_step = 0

        # Pasos de calibración
        self.steps = [
            # Matrícula (4 puntos)
            {
                'name': 'matricula_top_left',
                'description': 'MATRÍCULA: Columna 1, Dígito 0 (esquina superior izquierda)',
                'color': (0, 255, 0)  # Verde
            },
            {
                'name': 'matricula_top_right',
                'description': 'MATRÍCULA: Columna 10, Dígito 0 (esquina superior derecha)',
                'color': (255, 0, 0)  # Azul
            },
            {
                'name': 'matricula_bottom_left',
                'description': 'MATRÍCULA: Columna 1, Dígito 9 (esquina inferior izquierda)',
                'color': (0, 165, 255)  # Naranja
            },
            {
                'name': 'matricula_bottom_right',
                'description': 'MATRÍCULA: Columna 10, Dígito 9 (esquina inferior derecha)',
                'color': (0, 255, 255)  # Amarillo
            },
            # Columna 1: Preguntas 1-25
            {
                'name': 'respuestas_p1_a',
                'description': 'COLUMNA 1: Pregunta 1, Alternativa A',
                'color': (255, 0, 255)  # Magenta
            },
            {
                'name': 'respuestas_p1_e',
                'description': 'COLUMNA 1: Pregunta 1, Alternativa E',
                'color': (255, 255, 0)  # Cyan
            },
            {
                'name': 'respuestas_p25_a',
                'description': 'COLUMNA 1: Pregunta 25, Alternativa A',
                'color': (128, 0, 128)  # Púrpura
            },
            # Columna 2: Preguntas 26-50
            {
                'name': 'respuestas_p26_a',
                'description': 'COLUMNA 2: Pregunta 26, Alternativa A',
                'color': (255, 128, 0)  # Naranja
            },
            {
                'name': 'respuestas_p26_e',
                'description': 'COLUMNA 2: Pregunta 26, Alternativa E',
                'color': (128, 255, 0)  # Verde lima
            },
            {
                'name': 'respuestas_p50_a',
                'description': 'COLUMNA 2: Pregunta 50, Alternativa A',
                'color': (0, 128, 128)  # Verde azulado
            },
            # Columna 3: Preguntas 51-75
            {
                'name': 'respuestas_p51_a',
                'description': 'COLUMNA 3: Pregunta 51, Alternativa A',
                'color': (128, 128, 255)  # Azul claro
            },
            {
                'name': 'respuestas_p51_e',
                'description': 'COLUMNA 3: Pregunta 51, Alternativa E',
                'color': (255, 128, 128)  # Rosa
            },
            {
                'name': 'respuestas_p75_a',
                'description': 'COLUMNA 3: Pregunta 75, Alternativa A',
                'color': (128, 255, 255)  # Cyan claro
            },
            # Columna 4: Preguntas 76-100
            {
                'name': 'respuestas_p76_a',
                'description': 'COLUMNA 4: Pregunta 76, Alternativa A',
                'color': (255, 255, 128)  # Amarillo claro
            },
            {
                'name': 'respuestas_p76_e',
                'description': 'COLUMNA 4: Pregunta 76, Alternativa E',
                'color': (128, 128, 128)  # Gris
            },
            {
                'name': 'respuestas_p100_a',
                'description': 'COLUMNA 4: Pregunta 100, Alternativa A',
                'color': (0, 128, 255)  # Naranja claro
            },
        ]

        # Radio aproximado de los círculos (lo calcularemos después)
        self.circle_radius = 12  # Valor inicial, ajustable

        # Configuración de la ventana
        self.window_name = 'Calibración - Test Scanner'
        self.scale_factor = 0.5  # Factor para escalar la imagen en pantalla

    def mouse_callback(self, event, x, y, flags, param):
        """
        Callback para manejar eventos del mouse.

        Args:
            event: Tipo de evento del mouse
            x, y: Coordenadas del click
            flags: Flags adicionales
            param: Parámetros adicionales
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            # Convertir coordenadas de pantalla a coordenadas de imagen original
            img_x = int(x / self.scale_factor)
            img_y = int(y / self.scale_factor)

            if self.current_step < len(self.steps):
                step = self.steps[self.current_step]

                # Guardar el punto
                self.points[step['name']] = (img_x, img_y)

                # Dibujar el punto en la imagen de display
                color = step['color']
                scaled_x = int(img_x * self.scale_factor)
                scaled_y = int(img_y * self.scale_factor)
                cv2.circle(self.display_image, (scaled_x, scaled_y), 5, color, -1)
                cv2.circle(self.display_image, (scaled_x, scaled_y), 8, color, 2)

                # Agregar etiqueta
                label = step['name'].replace('_', ' ').upper()
                cv2.putText(self.display_image, label,
                           (scaled_x + 10, scaled_y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                print(f"✓ Punto marcado: {step['description']}")
                print(f"  Coordenadas: ({img_x}, {img_y})")

                # Avanzar al siguiente paso
                self.current_step += 1

                if self.current_step < len(self.steps):
                    print(f"\n[{self.current_step + 1}/{len(self.steps)}] {self.steps[self.current_step]['description']}")
                else:
                    print("\n" + "="*60)
                    print("✓ ¡Calibración completada!")
                    print("Presiona 's' para GUARDAR o 'r' para REINICIAR")
                    print("="*60)

    def run(self):
        """
        Ejecuta la herramienta de calibración de forma interactiva.

        Returns:
            True si se guardó la calibración, False si se canceló
        """
        print("=" * 60)
        print("HERRAMIENTA DE CALIBRACIÓN - TEST SCANNER")
        print("=" * 60)
        print("\nInstrucciones:")
        print("1. Haz click en el CENTRO de cada círculo cuando se te indique")
        print("2. Los puntos se marcarán en diferentes colores")
        print("3. Si te equivocas, presiona 'r' para reiniciar")
        print("4. Al terminar, presiona 's' para guardar")
        print("5. Presiona 'ESC' para cancelar")
        print("\nNOTA: Haz click en el CENTRO exacto de cada círculo para")
        print("      mayor precisión en la detección automática.")
        print("=" * 60)

        # Escalar imagen para mostrar en pantalla
        self.display_image = cv2.resize(
            self.image,
            None,
            fx=self.scale_factor,
            fy=self.scale_factor,
            interpolation=cv2.INTER_LINEAR
        )

        # Crear ventana y configurar callback
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        # Mostrar primer paso
        print(f"\n[{self.current_step + 1}/{len(self.steps)}] {self.steps[self.current_step]['description']}")

        while True:
            # Mostrar imagen
            display = self.display_image.copy()

            # Agregar instrucciones en pantalla
            if self.current_step < len(self.steps):
                step_text = f"Paso {self.current_step + 1}/{len(self.steps)}"
                cv2.putText(display, step_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display, self.steps[self.current_step]['description'], (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            else:
                cv2.putText(display, "Calibracion completa - 's' para guardar, 'r' para reiniciar", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow(self.window_name, display)

            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("\n✗ Calibración cancelada")
                cv2.destroyAllWindows()
                return False

            elif key == ord('r') or key == ord('R'):  # Reiniciar
                print("\n⟲ Reiniciando calibración...")
                self.points = {}
                self.current_step = 0
                self.display_image = cv2.resize(
                    self.image,
                    None,
                    fx=self.scale_factor,
                    fy=self.scale_factor,
                    interpolation=cv2.INTER_LINEAR
                )
                print(f"\n[{self.current_step + 1}/{len(self.steps)}] {self.steps[self.current_step]['description']}")

            elif key == ord('s') or key == ord('S'):  # Guardar
                if self.current_step >= len(self.steps):
                    cv2.destroyAllWindows()
                    return True
                else:
                    print(f"✗ Debes completar todos los pasos antes de guardar ({self.current_step}/{len(self.steps)})")

    def calculate_all_positions(self):
        """
        Calcula las posiciones de todos los círculos mediante interpolación.

        Returns:
            Diccionario con las posiciones de todos los círculos
        """
        print("\nCalculando posiciones de todos los círculos...")

        calibration_data = {
            'image_dimensions': {
                'width': self.image.shape[1],
                'height': self.image.shape[0]
            },
            'circle_radius': self.circle_radius,
            'matricula': self.calculate_matricula_positions(),
            'respuestas': self.calculate_respuestas_positions()
        }

        return calibration_data

    def calculate_matricula_positions(self):
        """
        Calcula las posiciones de todos los círculos de matrícula (10x10).

        Returns:
            Lista de diccionarios con información de cada círculo de matrícula
        """
        # Obtener puntos de referencia
        top_left = self.points['matricula_top_left']
        top_right = self.points['matricula_top_right']
        bottom_left = self.points['matricula_bottom_left']
        bottom_right = self.points['matricula_bottom_right']

        matricula_circles = []

        # 10 columnas (dígitos de matrícula)
        for col in range(10):
            # 10 filas (dígitos 0-9)
            for row in range(10):
                # Interpolación bilineal
                # Calcular posición en X (interpolación horizontal)
                t_col = col / 9.0  # Normalizado 0-1

                # Interpolación en la fila superior
                top_x = top_left[0] + t_col * (top_right[0] - top_left[0])
                top_y = top_left[1] + t_col * (top_right[1] - top_left[1])

                # Interpolación en la fila inferior
                bottom_x = bottom_left[0] + t_col * (bottom_right[0] - bottom_left[0])
                bottom_y = bottom_left[1] + t_col * (bottom_right[1] - bottom_left[1])

                # Interpolación vertical
                t_row = row / 9.0  # Normalizado 0-1
                x = int(top_x + t_row * (bottom_x - top_x))
                y = int(top_y + t_row * (bottom_y - top_y))

                matricula_circles.append({
                    'columna': col + 1,  # 1-10
                    'digito': row,       # 0-9
                    'x': x,
                    'y': y,
                    'radius': self.circle_radius
                })

        print(f"  ✓ {len(matricula_circles)} círculos de matrícula calculados")
        return matricula_circles

    def calculate_respuestas_positions(self):
        """
        Calcula las posiciones de todos los círculos de respuestas (100 preguntas × 5 alternativas).

        Usa puntos de referencia de cada columna para mayor precisión.

        Returns:
            Lista de diccionarios con información de cada círculo de respuesta
        """
        # Obtener todos los puntos de referencia
        # Columna 1: preguntas 1-25
        col1_refs = {
            'p1_a': self.points['respuestas_p1_a'],
            'p1_e': self.points['respuestas_p1_e'],
            'p25_a': self.points['respuestas_p25_a']
        }

        # Columna 2: preguntas 26-50
        col2_refs = {
            'p26_a': self.points['respuestas_p26_a'],
            'p26_e': self.points['respuestas_p26_e'],
            'p50_a': self.points['respuestas_p50_a']
        }

        # Columna 3: preguntas 51-75
        col3_refs = {
            'p51_a': self.points['respuestas_p51_a'],
            'p51_e': self.points['respuestas_p51_e'],
            'p75_a': self.points['respuestas_p75_a']
        }

        # Columna 4: preguntas 76-100
        col4_refs = {
            'p76_a': self.points['respuestas_p76_a'],
            'p76_e': self.points['respuestas_p76_e'],
            'p100_a': self.points['respuestas_p100_a']
        }

        respuestas_circles = []
        alternatives = ['A', 'B', 'C', 'D', 'E']

        # Calcular para cada pregunta (1-100)
        for pregunta in range(1, 101):
            # Determinar en qué columna está la pregunta
            col_index = (pregunta - 1) // 25  # 0, 1, 2, 3
            row_in_col = (pregunta - 1) % 25   # 0-24

            # Seleccionar referencias según la columna
            if col_index == 0:
                # Columna 1: preguntas 1-25
                top_a = col1_refs['p1_a']
                top_e = col1_refs['p1_e']
                bottom_a = col1_refs['p25_a']
            elif col_index == 1:
                # Columna 2: preguntas 26-50
                top_a = col2_refs['p26_a']
                top_e = col2_refs['p26_e']
                bottom_a = col2_refs['p50_a']
            elif col_index == 2:
                # Columna 3: preguntas 51-75
                top_a = col3_refs['p51_a']
                top_e = col3_refs['p51_e']
                bottom_a = col3_refs['p75_a']
            else:
                # Columna 4: preguntas 76-100
                top_a = col4_refs['p76_a']
                top_e = col4_refs['p76_e']
                bottom_a = col4_refs['p100_a']

            # Interpolar verticalmente para obtener la posición de la pregunta actual
            # t = 0 para primera pregunta, t = 1 para última pregunta de la columna
            t = row_in_col / 24.0 if row_in_col < 24 else 1.0

            # Calcular posición de alternativa A para esta pregunta
            pregunta_a_x = int(top_a[0] + t * (bottom_a[0] - top_a[0]))
            pregunta_a_y = int(top_a[1] + t * (bottom_a[1] - top_a[1]))

            # Calcular el espaciado entre alternativas para esta pregunta
            # Interpolamos también el espaciado porque puede variar ligeramente entre filas
            top_alt_spacing_x = (top_e[0] - top_a[0]) / 4.0
            top_alt_spacing_y = (top_e[1] - top_a[1]) / 4.0

            # Calcular espaciado en la fila inferior
            # Estimamos la posición de E en la última pregunta
            bottom_e_x = bottom_a[0] + 4 * top_alt_spacing_x  # Aproximación
            bottom_e_y = bottom_a[1] + 4 * top_alt_spacing_y

            bottom_alt_spacing_x = (bottom_e_x - bottom_a[0]) / 4.0
            bottom_alt_spacing_y = (bottom_e_y - bottom_a[1]) / 4.0

            # Interpolar el espaciado para esta fila específica
            alt_spacing_x = top_alt_spacing_x + t * (bottom_alt_spacing_x - top_alt_spacing_x)
            alt_spacing_y = top_alt_spacing_y + t * (bottom_alt_spacing_y - top_alt_spacing_y)

            # Calcular las 5 alternativas para esta pregunta
            for alt_index, alt in enumerate(alternatives):
                x = int(pregunta_a_x + alt_index * alt_spacing_x)
                y = int(pregunta_a_y + alt_index * alt_spacing_y)

                respuestas_circles.append({
                    'pregunta': pregunta,
                    'alternativa': alt,
                    'x': x,
                    'y': y,
                    'radius': self.circle_radius
                })

        print(f"  ✓ {len(respuestas_circles)} círculos de respuestas calculados")
        return respuestas_circles

    def save_calibration(self, output_path: str):
        """
        Guarda los datos de calibración en un archivo JSON.

        Args:
            output_path: Ruta donde guardar el archivo JSON
        """
        calibration_data = self.calculate_all_positions()

        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Guardar JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(calibration_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Calibración guardada en: {output_path}")
        print(f"  - {len(calibration_data['matricula'])} círculos de matrícula")
        print(f"  - {len(calibration_data['respuestas'])} círculos de respuestas")
        print(f"  - Total: {len(calibration_data['matricula']) + len(calibration_data['respuestas'])} círculos")

    def visualize_calibration(self):
        """
        Visualiza la calibración calculada sobre la imagen.

        Dibuja todos los círculos calculados para verificar visualmente.
        """
        print("\nGenerando visualización de calibración...")

        calibration_data = self.calculate_all_positions()
        vis_image = self.image.copy()

        # Dibujar círculos de matrícula (verde)
        for circle in calibration_data['matricula']:
            cv2.circle(vis_image, (circle['x'], circle['y']),
                      circle['radius'], (0, 255, 0), 1)

        # Dibujar círculos de respuestas (azul)
        for circle in calibration_data['respuestas']:
            cv2.circle(vis_image, (circle['x'], circle['y']),
                      circle['radius'], (255, 0, 0), 1)

        # Guardar imagen de visualización
        vis_path = "calibration_visualization.jpg"
        cv2.imwrite(vis_path, vis_image)
        print(f"✓ Visualización guardada en: {vis_path}")

        # Mostrar en pantalla (escalada)
        display = cv2.resize(vis_image, None, fx=0.5, fy=0.5)
        cv2.imshow('Visualización de Calibración', display)
        print("\nPresiona cualquier tecla para cerrar la visualización...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    """Función principal de la herramienta de calibración."""
    calibration_image_path = "calibration_image.jpg"
    output_json_path = "config/calibration_data.json"

    # Verificar que existe la imagen de calibración
    if not Path(calibration_image_path).exists():
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(f"No se encontró la imagen: {calibration_image_path}")
        print("\nPrimero debes ejecutar:")
        print("  1. python test_aruco_detection.py")
        print("  2. Mostrar la hoja en blanco a la cámara")
        print("  3. Presionar 'c' para guardar calibration_image.jpg")
        print("=" * 60)
        return

    try:
        # Crear herramienta de calibración
        tool = CalibrationTool(calibration_image_path)

        # Ejecutar calibración interactiva
        if tool.run():
            # Guardar calibración
            tool.save_calibration(output_json_path)

            # Visualizar resultado
            tool.visualize_calibration()

            print("\n" + "=" * 60)
            print("¡CALIBRACIÓN COMPLETADA EXITOSAMENTE!")
            print("=" * 60)
            print(f"Archivo generado: {output_json_path}")
            print("\nYa puedes usar este archivo en el sistema de calificación.")
            print("El usuario final NO necesitará calibrar, este archivo")
            print("se incluirá con el programa.")
            print("=" * 60)
        else:
            print("\nCalibración cancelada. No se guardaron cambios.")

    except Exception as e:
        print(f"\n✗ Error durante la calibración: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
