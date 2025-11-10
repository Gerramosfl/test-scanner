# 🎓 Test Scanner

Sistema de calificación automática de pruebas de selección múltiple mediante reconocimiento óptico de marcas (OMR) usando marcadores ArUco. Procesa PDFs escaneados de hojas de respuestas y genera automáticamente las calificaciones.

## 📋 Descripción

Test Scanner es una aplicación de escritorio que permite calificar automáticamente hojas de respuestas de pruebas de selección múltiple. Utiliza procesamiento de imágenes para detectar las respuestas marcadas por los estudiantes, permite revisión manual de casos ambiguos, y calcula automáticamente las notas según la escala chilena (1.0 - 7.0) con redondeo matemático tradicional.

### Características principales

- ✅ **Procesamiento por lotes**: Carga múltiples PDFs escaneados y procesa todos de una vez
- ✅ **Soporte multi-página**: Un PDF puede contener múltiples hojas (1 estudiante por página)
- ✅ **Detección automática**: Marcadores ArUco para corrección de perspectiva
- ✅ **Identificación de estudiantes**: Número de matrícula de 10 dígitos
- ✅ **100 preguntas**: Soporta hasta 100 preguntas con 5 alternativas (A, B, C, D, E)
- ✅ **Overlay visual con colores**:
  - 🟢 Verde: Respuesta correcta del estudiante
  - 🔴 Rojo: Respuesta incorrecta del estudiante
  - 🟡 Amarillo: Respuesta correcta según pauta (cuando el estudiante no marcó o marcó incorrectamente)
- ✅ **Detección inteligente de múltiples marcas**: Identifica cuando un estudiante marca 2+ alternativas en una pregunta y las marca todas como incorrectas
- ✅ **Imágenes con correcciones**: Genera automáticamente imágenes JPG con overlay visual, guardadas como `{matricula}_{nombre_prueba}.jpg`
- ✅ **Revisión manual inteligente**: Para hojas con confianza < 99%, permite corrección manual interactiva antes de guardar
- ✅ **Click para corregir**: Interfaz intuitiva donde puedes hacer click en los círculos para corregir matrícula y respuestas
- ✅ **Integración con Excel**: Se integra con archivos Excel existentes (agrega columnas automáticamente)
- ✅ **Cálculo según norma chilena**: Escala 1.0 - 7.0 con redondeo "half up" (centésima ≥ 5 redondea hacia arriba)
- ✅ **Alertas de duplicados**: Detecta notas duplicadas con opción de sobrescritura
- ✅ **Múltiples pruebas por curso**: Columnas independientes en Excel para cada evaluación
- ✅ **Sistema calibrable**: Herramienta incluida para calibrar posiciones de círculos según tu hoja oficial

## 🚀 Instalación

### Requisitos previos

- Python 3.8 o superior
- Windows, macOS o Linux
- Escáner o sistema de escaneo de documentos (300 DPI recomendado)

### Pasos de instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tu-usuario/test-scanner.git
cd test-scanner
```

2. Crea un entorno virtual (recomendado):
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación:
```bash
python main.py
```

## 📖 Uso

### Flujo de trabajo completo

#### 1. Calibración (solo una vez)

Antes de usar el sistema por primera vez, debes calibrar las posiciones de los círculos usando tu hoja oficial:

```bash
python calibrate_from_pdf.py examples/hoja_de_respuestas_con_aruco_V4.pdf
```

Este proceso:
1. Convierte el PDF a imagen de alta resolución
2. Detecta marcadores ArUco y corrige perspectiva
3. Te pide marcar 16 puntos de referencia (4 matrícula + 12 respuestas)
4. Genera `config/calibration_data.json` con las posiciones de todos los círculos

**Nota**: Solo necesitas hacer esto una vez. El archivo de calibración se usará para todas las futuras correcciones.

#### 2. Configuración de la prueba

En la pestaña **Configuración**:

- **Cantidad de preguntas**: De 1 a 100
- **Porcentaje de exigencia**: Ejemplo: 60% (para aprobar con nota 4.0)
- **Nota mínima**: 1.0 (estándar chileno)
- **Nota máxima**: 7.0 (estándar chileno)
- **Nota de aprobación**: 4.0 (estándar chileno)
- **Archivo Excel**: Carga el archivo con la lista de estudiantes (columnas: Matrícula, Nombre)
- **Nombre de la prueba**: Ejemplo: "Prueba 1", "Examen Final"

#### 3. Construcción de la pauta

En la pestaña **Pauta**:

- Selecciona la alternativa correcta (A, B, C, D, E) para cada pregunta
- Solo las preguntas indicadas en la configuración estarán habilitadas
- Guarda la pauta cuando termines

#### 4. Procesamiento de pruebas

En la pestaña **Calificación**:

1. **Carga los PDFs**:
   - Haz click en "📄 Agregar PDF" para archivos individuales
   - O "📁 Agregar Carpeta" para procesar todos los PDFs de una carpeta

2. **Procesa todos**:
   - Haz click en "▶️ Procesar Todos"
   - El sistema procesará cada PDF automáticamente

3. **Revisión automática**:
   - Hojas con confianza ≥ 99%: Se guardan automáticamente en Excel
   - Hojas con confianza < 99%: Se marcan para revisión manual

4. **Revisión manual** (si es necesario):
   - Al terminar el procesamiento, se te preguntará si deseas revisar hojas ambiguas
   - Ventana de revisión muestra:
     - Imagen completa de la hoja con overlay visual
     - Click en círculos para corregir matrícula o respuestas
     - Panel lateral muestra correcciones en tiempo real
     - Navegación entre múltiples hojas (Anterior/Siguiente)
   - Opciones:
     - **Guardar y Continuar**: Guarda en Excel y pasa a la siguiente hoja
     - **Omitir**: Salta esta hoja sin guardar
     - **Cerrar**: Sale de la revisión manual

5. **Resultados**:
   - Cada resultado muestra: matrícula, puntaje, nota, estado
   - Emoji ✅ para hojas correctas, ⚠️ para las que necesitaron revisión
   - Se genera imagen JPG con overlay: `{matricula}_{nombre_prueba}.jpg`

## 📁 Estructura del Proyecto

```
test-scanner/
├── main.py                          # Punto de entrada de la aplicación
├── requirements.txt                 # Dependencias del proyecto
├── README.md                        # Este archivo
├── calibrate_from_pdf.py           # Herramienta de calibración desde PDF
├── calibration_tool.py             # Herramienta de calibración (legacy)
├── test_grade_calculation.py       # Script de verificación de cálculo de notas
├── .gitignore                      # Archivos ignorados por Git
├── config/
│   └── calibration_data.json       # Datos de calibración (generado)
├── src/
│   ├── ui/                         # Interfaz de usuario
│   │   ├── main_window.py          # Ventana principal
│   │   ├── tab_configuration.py    # Pestaña de configuración
│   │   ├── tab_answer_key.py       # Pestaña de pauta
│   │   ├── tab_grading.py          # Pestaña de calificación (procesamiento por lotes)
│   │   └── manual_review_window.py # Ventana de revisión manual
│   ├── core/                       # Lógica principal
│   │   ├── pdf_processor.py        # Conversión de PDF a imagen
│   │   ├── image_processor.py      # Detección ArUco y corrección de perspectiva
│   │   ├── omr_detector.py         # Detección OMR y generación de overlay visual
│   │   ├── grade_calculator.py     # Cálculo de notas (con redondeo chileno)
│   │   └── excel_handler.py        # Lectura/escritura de Excel
│   └── utils/                      # Utilidades
│       ├── constants.py            # Constantes del sistema
│       └── validators.py           # Validadores
├── examples/                       # Archivos de ejemplo
│   ├── hoja_de_respuestas_con_aruco_V4.pdf  # Hoja oficial (usar para calibración)
│   └── lista_alumnos_ejemplo.xlsx  # Plantilla de Excel
└── PROXIMOS_PASOS.md              # Roadmap de mejoras futuras
```

## 📄 Formato de Archivos

### Hoja de Respuestas

- **Tamaño**: Carta (Letter) - 215.9mm × 279.4mm
- **Marcadores ArUco**: 4 marcadores de 15mm en las esquinas (diccionario DICT_4X4_50)
- **Sección de identificación**: 10 columnas × 10 dígitos (0-9) para matrícula
- **Sección de respuestas**: 100 preguntas organizadas en 4 columnas de 25 preguntas
  - Columna 1: Preguntas 1-25
  - Columna 2: Preguntas 26-50
  - Columna 3: Preguntas 51-75
  - Columna 4: Preguntas 76-100
- **Importante**: Los estudiantes deben rellenar completamente los círculos con lápiz pasta azul o negro

### Archivo Excel

Debe contener al menos dos columnas:

| Matrícula  | Nombre Alumno     |
|------------|-------------------|
| 2023456195 | Juan Pérez        |
| 2023418927 | María González    |
| 2023567834 | Pedro Rodríguez   |

La aplicación agregará columnas automáticamente con el nombre de cada prueba. Si un estudiante tiene múltiples pruebas, aparecerán en columnas separadas.

## 🧮 Cálculo de Notas

### Fórmula según norma chilena

El sistema utiliza dos tramos lineales que se conectan en el punto de exigencia:

```
Puntaje mínimo aprobación = Puntaje máximo × (% exigencia / 100)

Si puntaje < puntaje mínimo aprobación:
    Nota = Nota mínima + (puntaje / puntaje mínimo aprobación) × (Nota aprobación - Nota mínima)

Si puntaje ≥ puntaje mínimo aprobación:
    Nota = Nota aprobación + ((puntaje - puntaje mínimo aprobación) /
           (Puntaje máximo - puntaje mínimo aprobación)) ×
           (Nota máxima - Nota aprobación)
```

### Redondeo según tradición chilena

El sistema utiliza redondeo "half up" (no el estándar IEEE 754):

- Si centésima ≥ 5 → redondea hacia arriba
- Si centésima < 5 → mantiene la décima

**Ejemplos**:
- 21 puntos de 100 (60% exigencia) → 2.05 → **2.1** (no 2.0)
- 45 puntos de 100 (60% exigencia) → 3.25 → **3.3** (no 3.2)
- 90 puntos de 100 (60% exigencia) → 6.25 → **6.3** (no 6.2)

Para más información: [Escala de Notas](https://escaladenotas.cl/?nmin=1.0&nmax=7.0&napr=4.0&exig=60.0&pmax=100.0&explicacion=1)

## 🔧 Tecnologías Utilizadas

- **CustomTkinter**: Interfaz gráfica moderna y personalizable
- **OpenCV**: Procesamiento de imágenes, detección de marcadores ArUco y análisis OMR
- **NumPy**: Cálculos matemáticos y manipulación de arrays
- **PyMuPDF (fitz)**: Conversión de PDFs escaneados a imágenes de alta resolución
- **OpenPyXL**: Lectura y escritura de archivos Excel (.xlsx)
- **Pillow**: Procesamiento adicional de imágenes
- **Pandas**: Manipulación de datos tabulares

## 🎨 Características Técnicas

### Soporte multi-página (NUEVO)

El sistema ahora soporta PDFs con múltiples páginas, donde cada página contiene la hoja de respuestas de un estudiante diferente:

- **Detección automática**: Al cargar un PDF, el sistema detecta cuántas páginas tiene
- **Display intuitivo**: Los PDFs multi-página muestran "(X páginas)" en la lista
- **Procesamiento individual**: Cada página se procesa independientemente
- **Progreso detallado**:
  - PDF único: `"documento.pdf (5/20)"`
  - Multi-página: `"pruebas.pdf - Página 3/30 (Total: 15/47)"`
- **Imágenes con sufijo**: Para evitar sobrescritura, las imágenes de PDFs multi-página incluyen número de página:
  - Página única: `2023456789_Prueba1.jpg`
  - Multi-página: `2023456789_Prueba1_p3.jpg`
- **Mezcla de formatos**: Soporta mezclar PDFs de 1 página con PDFs multi-página en la misma sesión
- **Manejo de errores**: Si una página falla, las demás continúan procesándose normalmente

**Caso de uso típico**:
- Escanear 30 hojas de prueba → 1 PDF de 30 páginas
- El sistema procesa automáticamente las 30 hojas
- Genera 30 resultados + 30 imágenes independientes
- Guarda 30 notas en Excel

### Detección OMR optimizada

- **DPI**: 300 DPI para PDFs escaneados
- **Umbral de relleno**: 65% - 98% (excluye texto impreso en círculos, detecta solo marcas de bolígrafo)
- **Confianza**: Sistema de confianza por círculo, pregunta y hoja completa
- **Detección ambigua**: Identifica respuestas múltiples, marcas débiles o ausencia de marca
- **Detección inteligente de múltiples marcas**:
  - **Umbral mínimo**: 50% de relleno para confirmar intención de marcar
  - **Diferencia mínima**: 15% para distinguir marcas únicas de múltiples
  - **Rango máximo**: 20% desde la alternativa más oscura para identificar marcas similares
  - **Prevención de falsos positivos**: Evita marcar alternativas que solo tienen texto impreso
  - **Visualización**: Cuando se detectan múltiples marcas (2+), todas se marcan en rojo y se considera respuesta incorrecta

### Sistema de overlay visual

- Círculos con borde de 2 píxeles de grosor (visual sutil pero claro)
- Colores según estado:
  - Verde (0, 255, 0): Respuesta correcta del estudiante
  - Rojo (0, 0, 255): Respuesta incorrecta del estudiante
  - Amarillo (0, 255, 255): Respuesta correcta según pauta (referencia visual)
- Imágenes guardadas en formato JPG en la misma carpeta que el Excel

### Revisión manual inteligente

- Umbral de confianza: 99%
- Interfaz modal con zoom automático
- Click interactivo en círculos (radio de detección: 1.5× radio del círculo)
- Regeneración de overlay en tiempo real
- Navegación entre múltiples hojas pendientes
- Guardado automático en Excel y actualización de imagen

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz un fork del proyecto
2. Crea una rama para tu función (`git checkout -b feature/nueva-funcion`)
3. Haz commit de tus cambios (`git commit -m 'Agrega nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📧 Contacto

Si tienes preguntas o sugerencias, por favor abre un issue en el repositorio.

## 🎯 Estado del Proyecto

### ✅ Implementado

- [x] Detección de marcadores ArUco y corrección de perspectiva
- [x] Desarrollo de las 3 pestañas de la interfaz (Configuración, Pauta, Calificación)
- [x] Integración del cálculo de notas chileno con redondeo correcto
- [x] Procesamiento por lotes de PDFs escaneados
- [x] **Soporte multi-página** (PDFs con múltiples hojas, 1 estudiante por página)
- [x] Sistema de revisión manual de respuestas ambiguas (confianza < 99%)
- [x] Generación automática de imágenes con overlay visual
- [x] Click interactivo para corrección manual de matrícula y respuestas
- [x] Integración completa con Excel (lectura/escritura, múltiples pruebas)
- [x] Sistema de calibración desde PDF
- [x] Detección de notas duplicadas con opción de sobrescritura
- [x] Prevención de saltos de columna en Excel

### 🚧 Mejoras futuras (ver PROXIMOS_PASOS.md)

- [ ] Exportación de reportes en PDF
- [ ] Estadísticas por pregunta (análisis de dificultad)
- [ ] Estadísticas por estudiante (historial de rendimiento)
- [ ] Modo oscuro/claro
- [ ] Soporte para diferentes tamaños de papel
- [ ] Exportación de gráficos de rendimiento

---

**Hecho con ❤️ para facilitar la labor docente en Chile**

*By Gerson - 2025*
