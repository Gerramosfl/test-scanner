# 🎯 Próximos Pasos - Test Scanner

## 📍 Situación Actual

Has completado exitosamente la **Fase 1** del proyecto:
- ✅ Estructura del repositorio
- ✅ Interfaz gráfica funcionando
- ✅ Sistema de configuración y pauta
- ✅ Calculadora de notas y Excel handler

## 🚀 Siguiente Fase: Implementar Detección

### Objetivo Inmediato

Implementar la detección de marcadores ArUco y la lectura óptica de marcas (OMR) para poder calificar hojas reales.

## 📋 Lista de Tareas

### 1. Preparación de la Hoja de Respuestas

**¿Qué necesitas hacer?**

- [ ] Verificar que tu PDF tiene marcadores ArUco válidos
- [ ] Identificar los IDs de los marcadores ArUco (0, 1, 2, 3 generalmente)
- [ ] Imprimir varias copias de prueba en tamaño Carta
- [ ] Medir las posiciones exactas de:
  - Sección de matrícula (coordenadas x, y)
  - Sección de respuestas (coordenadas x, y)
  - Tamaño de cada círculo

**Herramienta útil**: Crear un script para detectar los marcadores:

```python
import cv2
import cv2.aruco as aruco

# Detectar marcadores en tu PDF
image = cv2.imread('hoja_respuestas.pdf')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

corners, ids, rejected = detector.detectMarkers(gray)
print(f"Marcadores detectados: {ids}")
```

### 2. Implementar `image_processor.py`

**Funciones a crear:**

```python
class ImageProcessor:
    def detect_aruco_markers(image) -> dict
        # Detecta los 4 marcadores ArUco
        # Retorna: {id: corners}
    
    def correct_perspective(image, corners) -> image
        # Corrige la perspectiva usando los 4 puntos
        # Retorna: imagen con vista cenital
    
    def preprocess_for_omr(image) -> image
        # Convierte a escala de grises
        # Aplica umbral adaptativo
        # Reduce ruido
        # Retorna: imagen binaria lista para OMR
```

**Pasos sugeridos:**

1. Crear archivo `src/core/image_processor.py`
2. Implementar detección básica de ArUco
3. Probar con una imagen estática primero
4. Implementar corrección de perspectiva
5. Agregar pre-procesamiento de imagen

**Código base para empezar:**

```python
import cv2
import cv2.aruco as aruco
import numpy as np

class ImageProcessor:
    def __init__(self):
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.parameters)
    
    def detect_sheet(self, frame):
        """
        Detecta la hoja en el frame
        Retorna: (success, processed_image, markers_info)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar marcadores
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        if ids is None or len(ids) != 4:
            return False, None, None
        
        # Ordenar marcadores (top-left, top-right, bottom-right, bottom-left)
        markers_dict = self._order_markers(corners, ids)
        
        # Corregir perspectiva
        warped = self._correct_perspective(frame, markers_dict)
        
        return True, warped, markers_dict
```

### 3. Implementar `omr_detector.py`

**Funciones a crear:**

```python
class OMRDetector:
    def detect_matricula(image, region) -> str
        # Detecta los 10 dígitos de la matrícula
        # Retorna: string de 10 dígitos
    
    def detect_answers(image, regions) -> dict
        # Detecta respuestas marcadas
        # Retorna: {pregunta: alternativa} o {pregunta: 'MULTIPLE'/'BLANK'}
    
    def is_circle_filled(circle_region) -> bool
        # Determina si un círculo está rellenado
        # Retorna: True/False
```

**Consideraciones importantes:**

- **Umbral de relleno**: Experimentar con porcentajes (40-60%)
- **Manejo de ruido**: Aplicar filtros morfológicos
- **Múltiples marcas**: Detectar cuando hay 2+ círculos rellenados
- **Calibración**: Permitir ajustar umbrales manualmente

**Estructura sugerida:**

```python
class OMRDetector:
    def __init__(self, min_fill_percentage=40):
        self.min_fill_percentage = min_fill_percentage
    
    def extract_region(self, image, x, y, width, height):
        """Extrae una región de interés"""
        return image[y:y+height, x:x+width]
    
    def count_filled_pixels(self, region):
        """Cuenta píxeles negros en una región"""
        # Convertir a binario
        _, binary = cv2.threshold(region, 127, 255, cv2.THRESH_BINARY_INV)
        # Contar píxeles negros
        filled = cv2.countNonZero(binary)
        total = region.shape[0] * region.shape[1]
        percentage = (filled / total) * 100
        return percentage
```

### 4. Calibrar Posiciones

**Necesitas determinar:**

1. **Posiciones de matrícula**: 
   - 10 filas (una por dígito)
   - 10 columnas (0-9)
   - Coordenadas (x, y) de cada círculo

2. **Posiciones de respuestas**:
   - 100 preguntas
   - 5 alternativas por pregunta
   - Coordenadas (x, y) de cada círculo

**Herramienta de calibración** (crear esto primero):

```python
# calibrate_positions.py
import cv2

def onclick(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Posición: x={x}, y={y}")

image = cv2.imread('hoja_warped.jpg')  # Hoja con perspectiva corregida
cv2.namedWindow('Calibración')
cv2.setMouseCallback('Calibración', onclick)
cv2.imshow('Calibración', image)
cv2.waitKey(0)
```

Guarda las posiciones en `src/utils/constants.py`:

```python
# Posiciones de matrícula (después de corrección de perspectiva)
MATRICULA_START_X = 100
MATRICULA_START_Y = 200
MATRICULA_CIRCLE_DIAMETER = 20
MATRICULA_SPACING_X = 30
MATRICULA_SPACING_Y = 35

# Posiciones de respuestas
ANSWERS_START_X = 500
ANSWERS_START_Y = 200
ANSWER_CIRCLE_DIAMETER = 15
ANSWER_SPACING_X = 25
ANSWER_SPACING_Y = 30
```

### 5. Integrar en `tab_grading.py`

Modificar el método `grade_current_sheet()`:

```python
def grade_current_sheet(self):
    # 1. Detectar hoja con ArUco
    processor = ImageProcessor()
    success, warped, markers = processor.detect_sheet(self.current_frame)
    
    if not success:
        messagebox.showerror("Error", "No se detectó la hoja")
        return
    
    # 2. Detectar matrícula
    omr = OMRDetector()
    matricula = omr.detect_matricula(warped, MATRICULA_REGIONS)
    
    # 3. Verificar estudiante en Excel
    student = self.app_data['excel_handler'].get_student_by_matricula(matricula)
    if not student:
        messagebox.showerror("Error", f"Estudiante {matricula} no encontrado")
        return
    
    # 4. Detectar respuestas
    answers = omr.detect_answers(warped, ANSWER_REGIONS)
    
    # 5. Comparar con pauta
    correct = 0
    answer_key = self.app_data['answer_key']
    
    for q_num, student_answer in answers.items():
        if student_answer == answer_key[q_num]:
            correct += 1
    
    # 6. Calcular nota
    calculator = GradeCalculator(
        self.app_data['num_questions'],
        self.app_data['passing_percentage'],
        self.app_data['min_grade'],
        self.app_data['max_grade'],
        self.app_data['passing_grade']
    )
    
    grade = calculator.calculate_grade(correct)
    
    # 7. Mostrar resultado y guardar
    result = self.app_data['excel_handler'].save_grade(
        matricula,
        self.app_data['test_name'],
        grade
    )
    
    # 8. Mostrar overlay en imagen
    self.draw_overlay(warped, answers, answer_key)
```

### 6. Crear Overlay Visual

```python
def draw_overlay(self, image, detected_answers, answer_key):
    """Dibuja círculos de colores sobre las respuestas"""
    overlay = image.copy()
    
    for q_num, detected in detected_answers.items():
        correct_answer = answer_key[q_num]
        
        # Obtener posición del círculo
        x, y = self.get_answer_position(q_num, detected)
        
        # Elegir color
        if detected == correct_answer:
            color = (0, 255, 0)  # Verde
        else:
            color = (0, 0, 255)  # Rojo
        
        # Dibujar círculo
        cv2.circle(overlay, (x, y), 15, color, 3)
        
        # Marcar respuesta correcta en amarillo
        x_correct, y_correct = self.get_answer_position(q_num, correct_answer)
        cv2.circle(overlay, (x_correct, y_correct), 12, (0, 255, 255), 2)
    
    # Mostrar imagen con overlay
    self.display_result(overlay)
```

## 🧪 Plan de Pruebas

### Pruebas Unitarias

1. **Test de detección ArUco**
   - Imagen con 4 marcadores → debe detectar 4
   - Imagen sin marcadores → debe retornar False
   - Imagen con 3 marcadores → debe retornar False

2. **Test de corrección de perspectiva**
   - Hoja rotada → debe quedar recta
   - Verificar dimensiones finales

3. **Test de detección OMR**
   - Círculo 100% rellenado → True
   - Círculo vacío → False
   - Círculo 50% rellenado → según umbral

### Pruebas de Integración

1. Escanear hoja real con matrícula conocida
2. Verificar que detecta correctamente todas las respuestas
3. Comparar nota calculada con cálculo manual
4. Verificar guardado en Excel

### Pruebas de Casos Extremos

- Hoja con sombras o mala iluminación
- Hoja ligeramente doblada
- Estudiante que marca fuera del círculo
- Múltiples marcas en una pregunta
- Preguntas dejadas en blanco

## 📚 Recursos Recomendados

### Tutoriales de OpenCV
- [ArUco Detection](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- [Perspective Transform](https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html)
- [Thresholding](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html)

### Ejemplos de OMR
- [OMR Scanner GitHub](https://github.com/topics/omr-scanner)
- [Bubble Sheet Tutorial](https://pyimagesearch.com/2016/10/03/bubble-sheet-multiple-choice-scanner-and-test-grader-using-omr-python-and-opencv/)

## 🔧 Herramientas de Desarrollo Útiles

### 1. Script para Testing Rápido

Crea `test_detection.py`:

```python
"""
Script para probar detección sin abrir la app completa
"""
import cv2
from src.core.image_processor import ImageProcessor
from src.core.omr_detector import OMRDetector

# Cargar imagen de prueba
image = cv2.imread('test_sheet.jpg')

# Probar detección ArUco
processor = ImageProcessor()
success, warped, markers = processor.detect_sheet(image)

if success:
    print("✅ Hoja detectada correctamente")
    cv2.imshow('Hoja Corregida', warped)
    
    # Probar detección OMR
    omr = OMRDetector()
    matricula = omr.detect_matricula(warped)
    print(f"Matrícula detectada: {matricula}")
    
    cv2.waitKey(0)
else:
    print("❌ No se pudo detectar la hoja")
```

### 2. Visualizador de Regiones

Crea `visualize_regions.py`:

```python
"""
Visualiza las regiones de detección sobre la hoja
"""
import cv2
from src.utils.constants import *

image = cv2.imread('hoja_warped.jpg')

# Dibujar regiones de matrícula
for row in range(10):  # 10 dígitos
    for col in range(10):  # 0-9
        x = MATRICULA_START_X + (col * MATRICULA_SPACING_X)
        y = MATRICULA_START_Y + (row * MATRICULA_SPACING_Y)
        cv2.circle(image, (x, y), MATRICULA_CIRCLE_DIAMETER, (255, 0, 0), 2)

# Dibujar regiones de respuestas
for q in range(20):  # Primeras 20 preguntas
    for alt in range(5):  # A, B, C, D, E
        x = ANSWERS_START_X + (alt * ANSWER_SPACING_X)
        y = ANSWERS_START_Y + (q * ANSWER_SPACING_Y)
        cv2.circle(image, (x, y), ANSWER_CIRCLE_DIAMETER, (0, 255, 0), 2)

cv2.imshow('Regiones', image)
cv2.waitKey(0)
```

### 3. Ajustador de Umbrales

Crea `adjust_threshold.py`:

```python
"""
Permite ajustar el umbral de detección en tiempo real
"""
import cv2
import numpy as np

def nothing(x):
    pass

image = cv2.imread('circle_sample.jpg', 0)

cv2.namedWindow('Threshold Adjuster')
cv2.createTrackbar('Threshold', 'Threshold Adjuster', 127, 255, nothing)
cv2.createTrackbar('Fill %', 'Threshold Adjuster', 40, 100, nothing)

while True:
    thresh_val = cv2.getTrackbarPos('Threshold', 'Threshold Adjuster')
    fill_threshold = cv2.getTrackbarPos('Fill %', 'Threshold Adjuster')
    
    _, binary = cv2.threshold(image, thresh_val, 255, cv2.THRESH_BINARY_INV)
    
    filled_pixels = cv2.countNonZero(binary)
    total_pixels = binary.shape[0] * binary.shape[1]
    fill_percentage = (filled_pixels / total_pixels) * 100
    
    # Mostrar información
    result = binary.copy()
    text = f"Fill: {fill_percentage:.1f}% | Thresh: {fill_threshold}%"
    cv2.putText(result, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (255, 255, 255), 2)
    
    if fill_percentage >= fill_threshold:
        cv2.putText(result, "MARCADO", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2)
    
    cv2.imshow('Threshold Adjuster', result)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

## 📅 Timeline Sugerido

### Semana 1: Preparación y ArUco
- [ ] Día 1-2: Imprimir hojas, identificar marcadores ArUco
- [ ] Día 3-4: Implementar `ImageProcessor` básico
- [ ] Día 5-7: Perfeccionar corrección de perspectiva

### Semana 2: Calibración
- [ ] Día 1-3: Calibrar todas las posiciones de círculos
- [ ] Día 4-5: Crear herramientas de visualización
- [ ] Día 6-7: Validar posiciones con hojas impresas

### Semana 3: Detección OMR
- [ ] Día 1-3: Implementar detección de matrícula
- [ ] Día 4-5: Implementar detección de respuestas
- [ ] Día 6-7: Ajustar umbrales y mejorar precisión

### Semana 4: Integración
- [ ] Día 1-3: Integrar todo en `tab_grading.py`
- [ ] Día 4-5: Implementar overlay visual
- [ ] Día 6-7: Pruebas completas con hojas reales

## ✅ Checklist de Validación

Antes de considerar completa esta fase, verifica:

### Funcionalidad Básica
- [ ] La cámara detecta los 4 marcadores ArUco
- [ ] La perspectiva se corrige correctamente
- [ ] Se lee la matrícula de 10 dígitos con >95% precisión
- [ ] Se detectan respuestas marcadas con >90% precisión
- [ ] El overlay se muestra correctamente (verde/rojo/amarillo)
- [ ] Las notas se calculan correctamente
- [ ] Las notas se guardan en Excel sin errores

### Manejo de Errores
- [ ] Alerta cuando no se detecta hoja
- [ ] Alerta cuando matrícula no está en Excel
- [ ] Maneja respuestas múltiples correctamente
- [ ] Maneja preguntas en blanco
- [ ] Alerta de notas duplicadas funciona

### Usabilidad
- [ ] La interfaz responde fluidamente
- [ ] Los mensajes de error son claros
- [ ] El proceso completo toma <15 segundos por hoja
- [ ] El usuario puede corregir manualmente respuestas ambiguas

### Documentación
- [ ] Código comentado adecuadamente
- [ ] README actualizado con nuevas funcionalidades
- [ ] Manual de usuario con capturas de pantalla
- [ ] Ejemplos de uso documentados

## 🎯 Métricas de Éxito

### Precisión
- **Meta mínima**: 90% de precisión en detección de respuestas
- **Meta ideal**: 95%+ de precisión

### Velocidad
- **Detección de hoja**: <1 segundo
- **Corrección de perspectiva**: <0.5 segundos
- **Lectura completa**: <5 segundos
- **Guardado en Excel**: <0.5 segundos
- **Total por hoja**: <10 segundos

### Robustez
- Funciona con diferentes condiciones de iluminación
- Tolera hojas ligeramente dobladas
- Maneja diferentes tipos de bolígrafo (azul/negro)
- Detecta correctamente hojas rotadas (cualquier orientación)

## 🚨 Problemas Comunes y Soluciones

### Problema: Marcadores ArUco no detectados

**Causas posibles:**
- Iluminación insuficiente
- Marcadores muy pequeños en la imagen
- Marcadores parcialmente ocultos
- Calidad de impresión baja

**Soluciones:**
- Mejorar iluminación del área de trabajo
- Acercar más la hoja a la cámara
- Asegurar que los 4 marcadores son visibles
- Reimprimir con mejor calidad

### Problema: Perspectiva incorrecta

**Causas posibles:**
- Orden incorrecto de marcadores
- Cálculo de transformación erróneo

**Soluciones:**
- Verificar orden de marcadores (TL, TR, BR, BL)
- Usar función `cv2.getPerspectiveTransform()` correctamente
- Validar dimensiones de salida

### Problema: Círculos no detectados correctamente

**Causas posibles:**
- Umbral de relleno mal configurado
- Posiciones de círculos descalibradas
- Ruido en la imagen

**Soluciones:**
- Ajustar `MIN_FILL_PERCENTAGE` en constants.py
- Recalibrar posiciones de círculos
- Aplicar filtros de suavizado (GaussianBlur)
- Usar umbral adaptativo en vez de fijo

### Problema: Matrícula leída incorrectamente

**Causas posibles:**
- Estudiante marcó mal los dígitos
- Múltiples marcas en un dígito
- Posiciones descalibradas

**Soluciones:**
- Implementar verificación de múltiples marcas
- Mostrar warning al usuario para corrección manual
- Permitir ingreso manual de matrícula

## 📞 Cuándo Pedir Ayuda

Contacta si:
- Llevas >2 horas atascado en un problema
- La precisión de detección es <80%
- Hay errores que no entiendes
- Necesitas revisar la lógica de alguna función
- Quieres validar tu enfoque antes de continuar

## 🎉 Hitos a Celebrar

- ✨ Primera detección exitosa de ArUco
- ✨ Primera hoja con perspectiva corregida
- ✨ Primera matrícula leída correctamente
- ✨ Primera calificación completa automática
- ✨ Primera nota guardada en Excel
- ✨ Primer lote de 10 hojas calificadas sin errores

## 🔄 Ciclo de Desarrollo Recomendado

```
1. Implementar función básica
2. Probar con imagen estática
3. Ajustar y depurar
4. Probar con cámara en vivo
5. Optimizar rendimiento
6. Documentar
7. Siguiente función
```

## 📖 Recursos Adicionales

### Libros Recomendados
- "Learning OpenCV 4" - Gary Bradski
- "Practical Python and OpenCV" - Adrian Rosebrock

### Videos Tutorial
- Canal de PyImageSearch en YouTube
- OpenCV Official Tutorials

### Comunidad
- Stack Overflow (tag: opencv, python)
- Reddit: r/computervision
- Discord de OpenCV en español

## 💡 Tips Finales

1. **Itera rápido**: No busques perfección en el primer intento
2. **Prueba frecuentemente**: Cada cambio debe probarse de inmediato
3. **Guarda versiones**: Usa commits frecuentes en Git
4. **Documenta decisiones**: Anota por qué elegiste ciertos valores
5. **Pide feedback**: Muestra avances aunque no estén completos
6. **Mantén backup**: De las hojas físicas y archivos Excel

---

**¿Listo para empezar?** 

El primer paso es imprimir algunas hojas y empezar a jugar con la detección de ArUco. ¡Mucha suerte! 🚀

**Siguiente reunión**: Revisar avances en detección ArUco y calibración de posiciones.