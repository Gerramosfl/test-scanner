# 📦 Guía de Instalación - Test Scanner

Esta guía te ayudará a instalar y configurar Test Scanner en tu computadora.

## Requisitos del Sistema

### Hardware
- **Procesador**: Intel Core i3 o equivalente (recomendado i5 o superior)
- **RAM**: 4 GB mínimo (recomendado 8 GB para procesamiento por lotes)
- **Escáner**: Cualquier escáner que genere PDFs a 300 DPI (recomendado)
- **Espacio en disco**: 1 GB libre (para programa y archivos temporales)

### Software
- **Sistema Operativo**:
  - ✅ Windows 10/11 (completamente probado)
  - ✅ macOS 10.14+ (compatible)
  - ✅ Linux (Ubuntu 20.04+, compatible)
- **Python**: 3.8 o superior

## Instalación Paso a Paso

### 1. Instalar Python

#### Windows
1. Descarga Python desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, **marca la opción "Add Python to PATH"** ⚠️ (muy importante)
3. Completa la instalación
4. Reinicia la terminal si estaba abierta

#### macOS
```bash
# Opción 1: Usando Homebrew (recomendado)
brew install python3

# Opción 2: Descarga desde python.org
# Si instalas opencv-contrib-python, necesitarás Xcode Command Line Tools:
xcode-select --install
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Verificar Instalación de Python

Abre una terminal o símbolo del sistema y ejecuta:

```bash
python --version
# o en macOS/Linux:
python3 --version
```

Deberías ver: `Python 3.8.x` o superior

### 3. Clonar o Descargar el Repositorio

#### Opción A: Usando Git
```bash
git clone https://github.com/Gerramosfl/test-scanner.git
cd test-scanner
```

#### Opción B: Descarga Manual
1. Ve a https://github.com/Gerramosfl/test-scanner
2. Click en "Code" → "Download ZIP"
3. Extrae el archivo ZIP
4. Abre una terminal en la carpeta extraída

### 4. Crear Entorno Virtual (Recomendado)

Un entorno virtual mantiene las dependencias aisladas y evita conflictos.

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ Verás `(venv)` al inicio de tu línea de comandos cuando el entorno esté activo.

### 5. Instalar Dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Este proceso puede tomar varios minutos. Se instalarán:
- **CustomTkinter** (5.2.1) - Interfaz gráfica moderna
- **OpenCV-Python** (4.8.1.78) - Procesamiento de imágenes
- **OpenCV-Contrib-Python** (4.8.1.78) - Marcadores ArUco
- **NumPy** (1.24.3) - Cálculos matemáticos
- **PyMuPDF** (1.23.8) - Procesamiento de PDFs
- **OpenPyXL** (3.1.2) - Manejo de Excel
- **Pillow** (10.1.0) - Procesamiento de imágenes
- **Pandas** (2.1.3) - Manipulación de datos

**✅ Nota importante**: El sistema ya viene pre-calibrado para la hoja oficial del colegio. El archivo `config/calibration_data.json` está incluido en el repositorio, por lo que no necesitas realizar ninguna calibración. Puedes comenzar a usar el sistema inmediatamente.

### 6. Verificar Instalación

Ejecuta la aplicación:

```bash
python main.py
```

Si todo está correcto, deberías ver la ventana principal de Test Scanner con 3 pestañas: Configuración, Pauta y Calificación.

## Solución de Problemas Comunes

### Error: "python: command not found" (macOS/Linux)

**Solución**: Intenta usar `python3` en lugar de `python`:
```bash
python3 main.py
```

### Error: "No module named 'cv2'"

**Solución**: Reinstala OpenCV:
```bash
pip install --upgrade opencv-python opencv-contrib-python
```

### Error: "No module named 'fitz'" o "No module named 'PyMuPDF'"

**Solución**: Instala PyMuPDF:
```bash
pip install PyMuPDF
```

### Error en macOS: "opencv-contrib-python" no se instala

**Solución**: Instala Xcode Command Line Tools primero:
```bash
xcode-select --install
# Luego intenta de nuevo:
pip install -r requirements.txt
```

### Error: "Permission denied" al guardar Excel

**Solución**: Cierra el archivo Excel si está abierto en otra aplicación (Excel, LibreOffice, etc.)

### Error: "No se pudo inicializar el sistema" al ejecutar

**Causa**: El archivo `config/calibration_data.json` no se encuentra o está dañado.

**Solución**: Verifica que el archivo exista en la carpeta `config/`. Este archivo debería estar incluido en el repositorio. Si falta, descarga nuevamente el repositorio o contacta al desarrollador.

### La aplicación se ve borrosa en Windows (pantallas HiDPI)

**Solución**: Desactiva el escalado de DPI:
1. Click derecho en `python.exe` (en la carpeta de Python)
2. Propiedades → Compatibilidad
3. Marca "Invalidar comportamiento de escalado de PPP alto"
4. Selecciona "Aplicación"

### Scroll no funciona bien en macOS

Si el scroll con la rueda del mouse no funciona correctamente en la ventana de revisión manual, contáctanos para aplicar un ajuste menor.

### Error: "No se detectó la hoja" al procesar PDF

**Causas posibles:**
- Marcadores ArUco no visibles en el escaneo
- PDF de muy baja resolución (<300 DPI)
- Hoja escaneada en orientación incorrecta

**Soluciones:**
1. Verifica que el PDF muestre claramente los 4 marcadores ArUco en las esquinas
2. Reescanea a 300 DPI mínimo
3. Rota el PDF antes de procesar

## Compatibilidad entre Sistemas Operativos

### Windows ✅ (Completamente Probado)
- Totalmente funcional
- Todas las características probadas
- Recomendado para producción

### macOS ✅ (Compatible)
- Todas las dependencias son cross-platform
- Funcionalidad completa esperada
- El scroll podría requerir ajuste menor (según pruebas)
- Requiere Xcode Command Line Tools para OpenCV

### Linux ✅ (Compatible)
- Todas las dependencias funcionan en Linux
- Similar comportamiento a macOS
- Puede requerir permisos adicionales para archivos

## Actualización

Para actualizar a una nueva versión:

```bash
# Si usaste git
git pull

# Actualizar dependencias
pip install -r requirements.txt --upgrade
```

## Desinstalación

### Eliminar el entorno virtual

#### Windows
```bash
deactivate  # Si está activado
rmdir /s venv
```

#### macOS/Linux
```bash
deactivate  # Si está activado
rm -rf venv
```

### Eliminar el proyecto

Simplemente elimina la carpeta del proyecto.

## Archivos de Configuración

### `config/calibration_data.json`
Contiene las posiciones de los 600 círculos (matrícula + respuestas). Se genera con `calibrate_from_pdf.py`.

**Importante**: No elimines este archivo después de calibrar. Si lo pierdes, deberás calibrar de nuevo.

### Archivos de ejemplo
- `examples/hoja_de_respuestas_con_aruco_V4.pdf` - Hoja oficial para calibración
- `examples/lista_alumnos_ejemplo.xlsx` - Plantilla de Excel

## Requisitos de los Archivos

### PDFs escaneados
- **Resolución**: 300 DPI mínimo
- **Formato**: Papel Carta (Letter)
- **Color**: Blanco y negro o escala de grises
- **Marcadores**: 4 marcadores ArUco visibles en las esquinas
- **Multi-página**: Soportado (1 estudiante por página)

### Archivo Excel
- **Formato**: .xlsx (Excel 2007 o superior)
- **Columnas mínimas**:
  - Columna A: Matrícula (10 dígitos)
  - Columna B: Nombre del estudiante
- El programa agregará columnas automáticamente para cada prueba

## Avanzado (Solo para Desarrolladores)

### Calibración Manual (Opcional)

El sistema ya viene pre-calibrado para la hoja oficial del colegio incluida en `examples/hoja_de_respuestas_con_aruco_V4.pdf`. Sin embargo, si eres desarrollador o deseas usar una hoja de respuestas diferente, puedes realizar una calibración manual:

```bash
python calibrate_from_pdf.py tu_hoja_personalizada.pdf
```

**Este proceso:**
1. Te mostrará la hoja escaneada
2. Te pedirá hacer click en 16 puntos de referencia
3. Generará/actualizará `config/calibration_data.json` con las posiciones de 600 círculos

**Controles durante calibración:**
- Click en el centro de cada círculo cuando se te indique
- `R` = Reiniciar si te equivocas
- `S` = Guardar cuando termines

**⚠️ Advertencia**: Esto sobrescribirá el archivo de calibración oficial. Solo realiza esto si sabes lo que estás haciendo.

## Próximos Pasos

Una vez instalado:
1. Consulta [README.md](../README.md) - Descripción general del proyecto
2. Lee la sección "Uso" en el README para el flujo de trabajo completo
3. Prueba con 2-3 hojas de muestra antes de procesar lotes grandes

## Soporte

Si encuentras problemas:
1. ✅ Revisa esta guía completamente
2. ✅ Revisa la sección "Solución de Problemas" arriba
3. ✅ Busca en los [Issues del repositorio](https://github.com/Gerramosfl/test-scanner/issues)
4. ✅ Crea un nuevo issue con:
   - Tu sistema operativo y versión
   - Versión de Python (`python --version`)
   - Mensaje de error completo
   - Pasos para reproducir el problema

---

**Última actualización**: 10 de noviembre de 2025
**Versión del sistema**: 2.1
**Estado**: ✅ Listo para producción
