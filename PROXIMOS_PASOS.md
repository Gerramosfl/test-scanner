# 🎯 Test Scanner - Sistema de Calificación Automática

## ✅ Estado Actual del Proyecto

El sistema está **casi finalizado (~98% completado)** y listo para uso en producción. Se ha completado exitosamente la implementación de todas las funcionalidades core, incluyendo un sistema avanzado de revisión manual optimizado.

### 🎉 Funcionalidades Implementadas

#### ✅ Fase 1: Interfaz y Configuración (Completado)
- Interfaz gráfica moderna con CustomTkinter
- Sistema de configuración de pruebas
- Calculadora de notas (escala chilena 1.0-7.0)
- Manejador de Excel para lista de estudiantes
- Configuración de pauta de respuestas

#### ✅ Fase 2: Procesamiento de PDFs (Completado)
- **PDFProcessor**: Conversión de PDF a imagen de alta resolución (300 DPI)
- **ImageProcessor**: Detección de marcadores ArUco y corrección de perspectiva
- **OMRDetector**: Detección óptica de marcas con algoritmo comparativo
- Sistema de calibración interactivo desde PDFs
- Scripts de prueba y validación

#### ✅ Fase 3: Interfaz de Calificación (Completado)
- Carga de PDFs individual o por carpeta
- Drag & drop de archivos y carpetas (opcional)
- Procesamiento por lotes con barra de progreso
- Calificación automática con pauta configurada
- Guardado automático en Excel
- Resultados detallados por cada hoja procesada

---

## 🚀 Flujo de Trabajo Actual

### 1️⃣ Preparación Inicial (Una sola vez)

#### A. Calibración del Sistema

El sistema necesita ser calibrado **una vez** usando una hoja escaneada en blanco:

```bash
python calibrate_from_pdf.py hoja_blanca_escaneada.pdf
```

**¿Qué hace este script?**
1. Convierte el PDF a imagen de alta resolución (300 DPI)
2. Detecta los 4 marcadores ArUco y corrige la perspectiva
3. Te pide marcar manualmente 16 puntos de referencia:
   - 4 puntos de matrícula (esquinas)
   - 12 puntos de respuestas (3 puntos por cada una de las 4 columnas)
4. Calcula automáticamente las posiciones de los 600 círculos restantes mediante interpolación bilineal
5. Guarda todo en `config/calibration_data.json`

**Controles durante calibración:**
- Click en el centro de cada círculo cuando se te indique
- `R` = Reiniciar si te equivocas
- `S` = Guardar cuando termines

#### B. Archivos Necesarios

Asegúrate de tener:
- ✅ `config/calibration_data.json` (generado por calibración)
- ✅ `examples/hoja_respuestas.pdf` (hoja oficial del colegio)
- ✅ Un archivo Excel con la lista de estudiantes (columnas: Nombre, Apellido, Matrícula)

---

### 2️⃣ Uso del Sistema

#### Paso 1: Iniciar la Aplicación

```bash
python main.py
```

#### Paso 2: Configuración (Pestaña ⚙️)

1. **Cargar Excel** con la lista de estudiantes
2. **Configurar prueba:**
   - Nombre de la prueba
   - Número de preguntas (máximo 100)
   - Porcentaje de exigencia (default: 60%)
   - Escala de notas (default: 1.0-7.0)

#### Paso 3: Pauta de Respuestas (Pestaña 📝)

1. Configurar respuestas correctas para cada pregunta
2. Puedes usar:
   - Entrada manual
   - Importar desde archivo de texto
3. Guardar pauta

#### Paso 4: Calificación (Pestaña 📄)

1. **Cargar PDFs de hojas escaneadas:**
   - Botón "📁 Cargar PDFs" para archivos individuales
   - Botón "📂 Cargar Carpeta" para procesar todos los PDFs de una carpeta
   - O arrastra archivos/carpetas al área de drop

2. **Revisar lista de PDFs cargados:**
   - Aparecen con emoji ⏳ (pendiente)
   - Puedes eliminar individuales antes de procesar

3. **Presionar "▶️ Procesar Todos":**
   - Se procesa cada PDF automáticamente
   - Barra de progreso muestra avance en tiempo real
   - Estado cambia a ⚙️ (procesando) → ✅ (éxito) o ❌ (error)

4. **Ver resultados:**
   - Matrícula detectada
   - Confianza de detección (%)
   - Respuestas correctas/incorrectas
   - Nota calculada
   - Estado de guardado en Excel

---

## 🔧 Arquitectura Técnica

### Módulos Principales

#### 1. `src/core/pdf_processor.py`
**Responsabilidad**: Convertir PDFs escaneados a imágenes

```python
pdf_processor = PDFProcessor(dpi=300)
image = pdf_processor.pdf_to_image("hoja_alumno.pdf")
# Retorna: imagen OpenCV BGR de 2550x3300 píxeles
```

**Características:**
- Resolución fija 300 DPI (estándar de escáneres de oficina)
- Conversión RGB → BGR para compatibilidad con OpenCV
- Validación de PDF antes de procesar

#### 2. `src/core/image_processor.py`
**Responsabilidad**: Detectar marcadores ArUco y corregir perspectiva

```python
image_processor = ImageProcessor()
result = image_processor.process_answer_sheet(image)

if result['success']:
    # result['warped_image'] = imagen con perspectiva corregida (1700x2200)
    # result['preprocessed'] = imagen en escala de grises lista para OMR
    # result['marker_ids'] = IDs de los 4 marcadores detectados
```

**Proceso:**
1. Detecta los 4 marcadores ArUco (DICT_4X4_50)
2. Ordena los marcadores (top-left, top-right, bottom-right, bottom-left)
3. Aplica transformación de perspectiva para vista cenital
4. Normaliza a tamaño fijo 1700x2200 píxeles
5. Convierte a escala de grises

#### 3. `src/core/omr_detector.py`
**Responsabilidad**: Detectar marcas en círculos usando algoritmo comparativo

**Algoritmo comparativo innovador:**

En lugar de usar un umbral absoluto (ej. "si el círculo está 65% oscuro, está marcado"), el sistema compara **todos los círculos de un grupo** y selecciona el más oscuro:

```python
# Para cada columna de matrícula (o pregunta):
1. Medir oscuridad de TODOS los círculos
2. Ordenar de más oscuro a menos oscuro
3. Calcular diferencia: darkest - second_darkest
4. Si diferencia >= 15% → Es el marcado
5. Si diferencia < 15% → Marca ambigua
```

**Ventajas:**
- ✅ Ignora automáticamente el texto impreso dentro de los círculos
- ✅ Robusto a diferentes tipos de iluminación
- ✅ Funciona con diferentes densidades de tinta
- ✅ No requiere calibración de umbrales por escáner

**Parámetros clave:**
- `MIN_DIFFERENCE_PERCENTAGE = 15.0` (tanto para matrícula como respuestas)
- Radio efectivo: 70% del radio del círculo
- Umbral adaptativo basado en la mediana de la imagen

#### 4. `src/ui/tab_grading.py`
**Responsabilidad**: Interfaz de usuario para procesamiento por lotes

**Características:**
- Procesamiento en thread separado (no bloquea UI)
- Manejo de errores robusto
- Integración automática con Excel
- Resultados detallados en tiempo real

---

## 📊 Flujo de Procesamiento Detallado

```
PDF Escaneado (alumno_001.pdf)
    ↓
[PDFProcessor] Conversión a imagen 300 DPI
    ↓
Imagen 2550x3300 píxeles
    ↓
[ImageProcessor] Detección ArUco (4 marcadores)
    ↓
¿Se detectaron 4 marcadores? → NO → Error: "No se detectó la hoja"
    ↓ SÍ
Transformación de perspectiva
    ↓
Imagen normalizada 1700x2200 píxeles
    ↓
[OMRDetector] Detección de matrícula (10 columnas)
    ↓
Matrícula: "2023456195" (confianza: 98.6%)
    ↓
[OMRDetector] Detección de respuestas (100 preguntas)
    ↓
Respuestas: {1: 'D', 2: 'A', 3: 'B', ...}
    ↓
[GradeCalculator] Comparación con pauta
    ↓
Correctas: 22 | Incorrectas: 76
    ↓
[GradeCalculator] Cálculo de nota
    ↓
Nota: 2.1 (escala chilena)
    ↓
[ExcelHandler] Guardar en Excel
    ↓
✅ Guardado exitosamente
```

---

## 🧪 Scripts de Desarrollo

### 1. Calibración desde PDF
```bash
python calibrate_from_pdf.py hoja_blanca.pdf
```
Genera `config/calibration_data.json` con posiciones de 600 círculos.

### 2. Prueba con PDFs reales
```bash
python test_pdf_processing.py hoja1.pdf hoja2.pdf hoja3.pdf
```

**Salida esperada:**
```
================================================================================
RESULTADOS - hoja_alumno_001
================================================================================

📋 MATRÍCULA:
  Detectada: 2023456195
  Confianza: 100.0%
  Éxito: ✓

📝 RESPUESTAS:
  Total detectadas: 100/100
  Confianza: 98.0%
  Éxito: ✓

🎯 CONFIANZA GENERAL: 98.6%
================================================================================
```

También genera `result_hoja_alumno_001.jpg` con overlay visual:
- 🟢 Verde: Respuesta correcta
- 🔴 Rojo: Respuesta incorrecta
- 🟡 Amarillo: Respuesta correcta esperada

---

## 🎯 Métricas de Rendimiento

### Precisión (Probado con hojas reales)
- ✅ **Detección de matrícula**: 98-100% de confianza
- ✅ **Detección de respuestas**: 95-100% de confianza
- ✅ **Confianza general**: >98%

### Velocidad
- Conversión PDF → Imagen: ~0.5s
- Detección ArUco: ~0.3s
- Detección OMR completa: ~1.5s
- Cálculo y guardado: ~0.2s
- **Total por hoja: ~2.5 segundos**

### Procesamiento por Lotes
- 10 hojas: ~25 segundos
- 30 hojas: ~75 segundos (1.25 minutos)
- 100 hojas: ~4 minutos

---

## ⚠️ Requisitos del Sistema

### Hardware
- **Escáner**: Cualquier escáner que genere PDFs a 300 DPI
- **CPU**: Procesador multi-core recomendado para procesamiento por lotes
- **RAM**: 4GB mínimo, 8GB recomendado

### Software
- Python 3.8+
- Dependencias (instalar con `pip install -r requirements.txt`):
  ```
  customtkinter==5.2.1
  pillow==10.1.0
  tkinterdnd2==0.3.0
  opencv-python==4.8.1.78
  opencv-contrib-python==4.8.1.78
  numpy==1.24.3
  PyMuPDF==1.23.8
  openpyxl==3.1.2
  pandas==2.1.3
  python-dateutil==2.8.2
  ```

### Hojas de Respuestas
- **Formato**: Papel Carta (215.9 x 279.4 mm)
- **Marcadores ArUco**: DICT_4X4_50, 15mm
- **Escaneado**: 300 DPI mínimo
- **Color**: Blanco y negro o escala de grises
- **Instrumento**: Bolígrafo azul o negro (sin lápiz mina)

---

## 🔍 Resolución de Problemas

### Error: "No se pudo inicializar el sistema"

**Causa**: Falta el archivo de calibración

**Solución**:
```bash
python calibrate_from_pdf.py hoja_blanca_escaneada.pdf
```

### Error: "No se detectó la hoja"

**Causas posibles:**
- Marcadores ArUco no visibles en el escaneo
- PDF de muy baja resolución (<300 DPI)
- Hoja escaneada en orientación incorrecta

**Soluciones:**
- Verificar que el PDF muestre claramente los 4 marcadores ArUco
- Reescanear a 300 DPI
- Rotar el PDF antes de procesar

### Detección incorrecta de matrícula

**Causas posibles:**
- Estudiante marcó múltiples círculos en una columna
- Marcas muy tenues (menor al 15% de diferencia)
- Posiciones de calibración desalineadas

**Soluciones:**
- Instruir a estudiantes a marcar un solo círculo por columna
- Usar bolígrafo de tinta oscura
- Recalibrar el sistema si el problema persiste

### Nota no guardada en Excel

**Causas posibles:**
- Matrícula del estudiante no existe en el Excel
- Ya existe una nota para ese estudiante en esa prueba
- Excel abierto en otro programa

**Soluciones:**
- Verificar que la matrícula esté en el Excel
- Usar la opción de sobrescribir notas duplicadas
- Cerrar el Excel antes de procesar

---

## 📈 Próximos Pasos Opcionales

### Mejoras Sugeridas

#### 1. Sistema de Revisión Manual Avanzado ✅ COMPLETAMENTE IMPLEMENTADO
- ✅ Interfaz modal optimizada para revisar respuestas con confianza < 99%
- ✅ **Sistema de toggle**: Click para marcar/desmarcar respuestas y matrícula
- ✅ Soporte para múltiples alternativas por pregunta
- ✅ Scroll vertical (rueda del mouse) y horizontal (Shift + rueda)
- ✅ Círculos verde brillante (#00FF00) para máxima visibilidad
- ✅ Regeneración de overlay en tiempo real
- ✅ Navegación simplificada (botón "◄ Anterior", "Guardar y Continuar")
- ✅ Interfaz limpia (sin corrección rápida, sin zoom, sin botón "Siguiente")
- ✅ Guardado automático en Excel tras correcciones

#### 2. Modo de Revisión Visual Mejorado ✅ IMPLEMENTADO
- ✅ Generación automática de imágenes con overlay visual
- ✅ Colores: verde brillante (correcta), rojo (incorrecta), amarillo (pauta)
- ✅ **Organización en carpetas por prueba:** `carpeta_excel/nombre_prueba/matricula_prueba.jpg`
- ✅ Se guarda después de revisión manual si es necesario
- ✅ Excel sin colores de fondo (formato limpio y profesional)

#### 3. Soporte Multi-página ✅ IMPLEMENTADO (Noviembre 2025)
- ✅ Permite PDFs con múltiples hojas (1 estudiante por página)
- ✅ Detección automática del número de páginas
- ✅ Display: "documento.pdf (5 páginas)"
- ✅ Procesamiento independiente de cada página
- ✅ Progreso detallado: "Página 3/30 (Total: 15/47)"
- ✅ **Imágenes organizadas en carpetas:** `carpeta_excel/test1/2023456789_test1_p3.jpg`
- ✅ Mezcla de PDFs de 1 página con PDFs multi-página
- ✅ Manejo de errores por página

#### 4. Exportación de Reportes 🔵 PENDIENTE
- [ ] Generar reportes PDF con estadísticas de la prueba
- [ ] Gráficos de distribución de notas
- [ ] Análisis de preguntas más difíciles
- [ ] Estadísticas por pregunta y por estudiante

#### 5. Historial de Calificaciones 🔵 PENDIENTE
- [ ] Base de datos para consultar historial completo de calificaciones por estudiante
- [ ] Seguimiento del progreso a lo largo del tiempo

#### 6. Integración con Otros Formatos 🔵 PENDIENTE
- [ ] Exportar a Google Sheets
- [ ] Integración con sistemas de gestión escolar

---

## 📚 Documentación Adicional

### Estructura del Proyecto

```
test-scanner/
├── config/
│   └── calibration_data.json      # Posiciones de 600 círculos
├── examples/
│   ├── hoja_respuestas.pdf        # Hoja oficial del colegio
│   └── lista_alumnos_ejemplo.xlsx
├── src/
│   ├── core/
│   │   ├── pdf_processor.py       # PDF → Imagen
│   │   ├── image_processor.py     # ArUco + Perspectiva
│   │   ├── omr_detector.py        # Detección de marcas
│   │   ├── excel_handler.py       # Manejo de Excel
│   │   └── grade_calculator.py    # Cálculo de notas
│   ├── ui/
│   │   ├── main_window.py         # Ventana principal
│   │   ├── tab_configuration.py   # Pestaña de config
│   │   ├── tab_answer_key.py      # Pauta de respuestas
│   │   └── tab_grading.py         # Calificación (PDFs)
│   └── utils/
│       └── constants.py           # Constantes del sistema
├── calibrate_from_pdf.py          # Script de calibración
├── test_pdf_processing.py         # Script de prueba
├── main.py                        # Punto de entrada
└── requirements.txt               # Dependencias

Archivos obsoletos eliminados:
✗ test_camera_detection.py        # (Eliminado - enfoque anterior)
✗ test_aruco_detection.py         # (Eliminado - enfoque anterior)
✗ test_omr_detection.py           # (Eliminado - enfoque anterior)
```

### Archivos de Configuración

#### `config/calibration_data.json`

Estructura:
```json
{
  "version": "1.0",
  "image_size": {"width": 1700, "height": 2200},
  "matricula": [
    {"columna": 1, "digito": 0, "x": 245, "y": 523, "radius": 12},
    ...
    // 100 círculos total (10 columnas × 10 dígitos)
  ],
  "respuestas": [
    {"pregunta": 1, "alternativa": "A", "x": 678, "y": 523, "radius": 12},
    ...
    // 500 círculos total (100 preguntas × 5 alternativas)
  ]
}
```

---

## 🎓 Guía de Uso para Profesores

### Preparación de Pruebas

1. **Imprimir hojas**: Usar `examples/hoja_respuestas.pdf` (nunca cambiar este formato)
2. **Preparar lista**: Asegurar que todos los estudiantes estén en el Excel con su matrícula
3. **Configurar pauta**: Ingresar respuestas correctas en el sistema

### Día de la Prueba

1. Distribuir hojas impresas
2. Instruir a estudiantes:
   - Marcar con bolígrafo (no lápiz)
   - Rellenar completamente los círculos
   - Solo una marca por pregunta
   - Matrícula completa y correcta

### Después de la Prueba

1. **Escanear todas las hojas** a 300 DPI en formato PDF
2. **Abrir Test Scanner** y cargar:
   - Excel con lista de estudiantes
   - Pauta de respuestas
3. **Cargar carpeta** con todos los PDFs escaneados
4. **Presionar "Procesar Todos"**
5. **Esperar** (~2.5 segundos por hoja)
6. **Revisar resultados** y verificar que todas las notas se guardaron
7. **Cerrar aplicación** para guardar cambios en Excel

---

## ✅ Checklist de Calidad

Antes de procesar hojas de una prueba real:

### Sistema
- [ ] `config/calibration_data.json` existe y está actualizado
- [ ] Todas las dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Script de prueba funciona: `python test_pdf_processing.py`

### Configuración
- [ ] Excel con lista de estudiantes cargado
- [ ] Matrícula de todos los estudiantes verificada
- [ ] Pauta de respuestas ingresada y guardada
- [ ] Configuración de prueba correcta (nombre, preguntas, exigencia)

### Escaneo
- [ ] Todas las hojas escaneadas a 300 DPI
- [ ] PDFs en formato adecuado (Carta, blanco y negro)
- [ ] Marcadores ArUco visibles en todos los escaneos
- [ ] Un PDF por estudiante

### Procesamiento
- [ ] Prueba con 2-3 hojas primero
- [ ] Verificar confianza >95% en pruebas
- [ ] Confirmar que notas se guardan en Excel
- [ ] Procesar lote completo

---

## 🎉 Conclusión

El **Test Scanner** está **casi finalizado (~98% completado)** y listo para uso en producción. El sistema ha sido optimizado para trabajar con escáneres de documentos (300 DPI) y puede procesar lotes completos de pruebas de manera automática y confiable.

**Características destacadas:**
- ✅ Procesamiento por lotes rápido (~2.5s por hoja)
- ✅ Alta precisión (>98% de confianza)
- ✅ **Sistema de revisión manual avanzado con toggle**
- ✅ **Overlays organizados en carpetas por prueba**
- ✅ **Excel sin colores de fondo (formato limpio)**
- ✅ Interfaz intuitiva optimizada y fácil de usar
- ✅ Integración transparente con Excel
- ✅ Algoritmo robusto que ignora texto impreso
- ✅ Soporte para múltiples alternativas por pregunta

**Últimas optimizaciones (Noviembre 10, 2025):**
- ✅ Interfaz de revisión manual simplificada
- ✅ Sistema de toggle para marcar/desmarcar
- ✅ Círculos verde brillante para mejor visibilidad
- ✅ Organización automática de archivos en carpetas

**Soporte y Mejoras:**
- Para reportar problemas o sugerir mejoras, crear un issue en el repositorio
- Para preguntas sobre uso, consultar esta documentación primero

---

**Última actualización**: 10 de noviembre de 2025
**Versión del sistema**: 2.1 (Optimizado y casi finalizado)
**Estado**: ✅ Listo para producción (~98% completado)
