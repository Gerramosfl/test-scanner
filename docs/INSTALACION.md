# 📦 Guía de Instalación - Test Scanner

Esta guía te ayudará a instalar y configurar Test Scanner en tu computadora.

## Requisitos del Sistema

### Hardware
- Procesador: Intel Core i3 o equivalente (recomendado i5 o superior)
- RAM: 4 GB mínimo (recomendado 8 GB)
- Cámara web o cámara integrada en laptop
- Espacio en disco: 500 MB libres

### Software
- Sistema Operativo: Windows 10/11, macOS 10.14+, o Linux (Ubuntu 20.04+)
- Python 3.8 o superior

## Instalación Paso a Paso

### 1. Instalar Python

#### Windows
1. Descarga Python desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, **marca la opción "Add Python to PATH"**
3. Completa la instalación

#### macOS
```bash
# Usando Homebrew
brew install python3
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
# o
python3 --version
```

Deberías ver algo como: `Python 3.8.x` o superior

### 3. Clonar o Descargar el Repositorio

#### Opción A: Usando Git
```bash
git clone https://github.com/tu-usuario/test-scanner.git
cd test-scanner
```

#### Opción B: Descarga Manual
1. Ve a https://github.com/tu-usuario/test-scanner
2. Click en "Code" → "Download ZIP"
3. Extrae el archivo ZIP
4. Abre una terminal en la carpeta extraída

### 4. Crear Entorno Virtual (Recomendado)

Un entorno virtual mantiene las dependencias aisladas.

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

Verás `(venv)` al inicio de tu línea de comandos cuando el entorno esté activo.

### 5. Instalar Dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Este proceso puede tomar varios minutos. Se instalarán:
- CustomTkinter (interfaz)
- OpenCV (procesamiento de imágenes)
- NumPy (cálculos)
- OpenPyXL (Excel)
- Pillow (imágenes)

### 6. Verificar Instalación

Ejecuta la aplicación:

```bash
python main.py
```

Si todo está correcto, deberías ver la ventana principal de Test Scanner.

## Solución de Problemas Comunes

### Error: "python: command not found"

**Solución**: Intenta usar `python3` en lugar de `python`:
```bash
python3 main.py
```

### Error: "No module named 'cv2'"

**Solución**: Reinstala OpenCV:
```bash
pip install --upgrade opencv-python opencv-contrib-python
```

### Error al abrir la cámara

**Solución**:
1. Verifica que tu cámara funciona en otras aplicaciones
2. Cierra otras aplicaciones que usen la cámara (Zoom, Teams, etc.)
3. En Linux, verifica permisos:
```bash
sudo usermod -a -G video $USER
# Luego reinicia sesión
```

### Error: "Permission denied" al guardar Excel

**Solución**: Cierra el archivo Excel si está abierto en otra aplicación.

### La aplicación se ve borrosa en Windows

**Solución**: Desactiva el escalado de DPI:
1. Click derecho en `python.exe`
2. Propiedades → Compatibilidad
3. Marca "Invalidar comportamiento de escalado de PPP alto"
4. Selecciona "Aplicación"

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

## Configuración de la Cámara

### Cambiar cámara predeterminada

Edita `src/utils/constants.py`:

```python
DEFAULT_CAMERA_INDEX = 1  # Cambia 0 por 1, 2, etc.
```

### Ajustar resolución

En el mismo archivo:

```python
CAMERA_WIDTH = 1920  # Cambiar según necesidad
CAMERA_HEIGHT = 1080
```

## Próximos Pasos

Una vez instalado, consulta:
- [MANUAL_USO.md](MANUAL_USO.md) - Guía de uso completa
- [README.md](../README.md) - Descripción general del proyecto

## Soporte

Si encuentras problemas:
1. Revisa esta guía completamente
2. Busca en los [Issues del repositorio](https://github.com/tu-usuario/test-scanner/issues)
3. Crea un nuevo issue con:
   - Tu sistema operativo
   - Versión de Python
   - Mensaje de error completo
   - Pasos para reproducir el problema