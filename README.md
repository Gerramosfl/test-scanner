# 🎓 Test Scanner

Sistema de calificación automática de pruebas de selección múltiple mediante reconocimiento óptico de marcas (OMR) usando marcadores ArUco.

## 📋 Descripción

Test Scanner es una aplicación de escritorio que permite calificar automáticamente hojas de respuestas de pruebas de selección múltiple. Utiliza procesamiento de imágenes para detectar las respuestas marcadas por los estudiantes y calcula automáticamente las notas según la escala chilena (1.0 - 7.0).

### Características principales

- ✅ Detección automática de hojas mediante marcadores ArUco
- ✅ Identificación de estudiantes por número de matrícula (10 dígitos)
- ✅ Soporte para hasta 100 preguntas con 5 alternativas (A, B, C, D, E)
- ✅ Calificación en tiempo real con vista previa en cámara
- ✅ Overlay visual: verde (correcta), rojo (incorrecta), amarillo (respuesta correcta)
- ✅ Corrección manual de respuestas ambiguas o múltiples marcas
- ✅ Integración con archivos Excel existentes
- ✅ Cálculo automático según escala de notas chilena
- ✅ Alertas de notas duplicadas con opción de sobrescritura
- ✅ Múltiples pruebas por curso (columnas independientes en Excel)

## 🚀 Instalación

### Requisitos previos

- Python 3.8 o superior
- Cámara web o cámara integrada en laptop
- Windows, macOS o Linux

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

### 1. Pestaña de Configuración

Configura los parámetros de tu prueba:

- **Cantidad de preguntas**: De 1 a 100
- **Porcentaje de exigencia**: Ejemplo: 60%
- **Nota mínima**: Ejemplo: 1.0
- **Nota máxima**: Ejemplo: 7.0
- **Nota de aprobación**: Ejemplo: 4.0
- **Archivo Excel**: Carga el archivo con la lista de estudiantes
- **Nombre de la prueba**: Ejemplo: "Test 1", "Examen Final"

### 2. Pestaña de Pauta

Construye la pauta de respuestas correctas:

- Selecciona la alternativa correcta (A, B, C, D, E) para cada pregunta
- Solo las preguntas indicadas en la configuración estarán habilitadas

### 3. Pestaña de Calificación

Califica las pruebas en tiempo real:

1. Acerca la hoja de respuestas a la cámara
2. La aplicación detectará automáticamente los marcadores ArUco
3. Presiona el botón "Calificar"
4. Verás el overlay con colores:
   - 🟢 Verde: Respuesta correcta
   - 🔴 Rojo: Respuesta incorrecta
   - 🟡 Amarillo: Alternativa correcta según pauta
5. Si hay respuestas ambiguas, podrás corregirlas manualmente
6. La nota se guardará automáticamente en el Excel

## 📁 Estructura del Proyecto

```
test-scanner/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
├── .gitignore             # Archivos ignorados por Git
├── src/
│   ├── ui/                # Interfaz de usuario
│   │   ├── main_window.py
│   │   ├── tab_configuration.py
│   │   ├── tab_answer_key.py
│   │   └── tab_grading.py
│   ├── core/              # Lógica principal
│   │   ├── image_processor.py
│   │   ├── omr_detector.py
│   │   ├── grade_calculator.py
│   │   └── excel_handler.py
│   └── utils/             # Utilidades
│       ├── constants.py
│       └── validators.py
├── examples/              # Archivos de ejemplo
│   ├── hoja_respuestas.pdf
│   └── lista_alumnos_ejemplo.xlsx
└── docs/                  # Documentación adicional
    ├── INSTALACION.md
    └── MANUAL_USO.md
```

## 📄 Formato de Archivos

### Hoja de Respuestas

- Tamaño: Carta (Letter)
- Marcadores ArUco de 15mm en las 4 esquinas
- Sección de identificación: 10 dígitos (matrícula)
- Sección de respuestas: 100 preguntas con 5 alternativas
- **Importante**: Los estudiantes deben rellenar completamente los círculos con lápiz pasta azul o negro

### Archivo Excel

Debe contener al menos dos columnas:

| Matrícula | Nombre Alumno |
|-----------|---------------|
| 2023456195 | Juan Pérez |
| 2023418927 | María González |

La aplicación agregará columnas automáticamente con el nombre de cada prueba.

## 🧮 Cálculo de Notas

Se utiliza la fórmula estándar chilena:

```
Puntaje mínimo aprobación = Puntaje máximo × % exigencia

Nota = (Puntaje obtenido - Puntaje mínimo aprobación) / 
       (Puntaje máximo - Puntaje mínimo aprobación) × 
       (Nota máxima - Nota aprobación) + Nota aprobación
```

Para más información: [Escala de Notas](https://escaladenotas.cl)

## 🔧 Tecnologías Utilizadas

- **CustomTkinter**: Interfaz gráfica moderna
- **OpenCV**: Procesamiento de imágenes y detección de marcadores ArUco
- **NumPy**: Cálculos matemáticos y manipulación de arrays
- **OpenPyXL**: Lectura y escritura de archivos Excel
- **Pillow**: Procesamiento adicional de imágenes

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

## 🎯 Roadmap

- [ ] Implementación de detección de marcadores ArUco
- [ ] Desarrollo de las 3 pestañas de la interfaz
- [ ] Integración del cálculo de notas chileno
- [ ] Sistema de corrección manual de respuestas ambiguas
- [ ] Exportación de reportes en PDF
- [ ] Soporte para cámara de celular (futura versión)
- [ ] Modo oscuro/claro
- [ ] Historial de calificaciones
- [ ] Estadísticas por pregunta y por estudiante

---

Hecho con ❤️ para facilitar la labor docente