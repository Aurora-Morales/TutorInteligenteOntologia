# TutorInteligenteOntologia
Este proyecto representa a un tutor virtual basado en una ontología desarrollada en Protégé. El agente es capaz de responder consultas de los estudiantes, ofrecer orientación personalizada y guiar su trayectoria académica. Para más información, leer la documentación adjunta.

---
## Requisitos de ejecución
1. Tener instalado **Python**
2. Tener instalado **Streamlit**
3. Tener instalado **Pandas**
4. Tener instalado **Owlready2**
5. Tener instalado **Java version 25**

## Pasos para la ejecución en Linux
Al descargar el proyecto de GitHub y tener instaladas las bibliotecas mencionadas anteriormente seguir leyendo la primera sección, si no pasar a la sección 2.

### ------ Seccion 1 ------
1. Abrir una terminar 
2. Ir a la carpeta del proyecto 
3. Crear un entorno virtual para evitar fallas

**python3 -m venv venv**

4. Activar el entono vitual 

**source ./venv/bin/activate**

5. Ejecutar programa

**streamlit run main.py**

### ----- Seccion 2 ------
- Para distribuciones de Linux como Ubuntu/Debian/Mint

Actualizar el sistema e instalar Python, el gestor pip, el entorno virtual y Java

1. Actualizar e instalar python3

**sudo apt update**

**sudo apt install python3 python3-pip python3-venv default-jre -y**

3. Instalar java version 25 

**sudo apt install openjdk-25-jdk -y**

4. Ir a la carpeta del proyecto y dentro crear un entorno virtual con venv

**python3 -m venv venv**

5. Activar el entorno virtual

**source ./venv/bin/activate**

6. Instalar las librerías requeridas dentro del entorno

**pip install --upgrade pip**

**pip install streamlit pandas owlready2**

7. Ejecutar el tutor inteligente

**streamlit run tu_archivo_principal.py**

---

- Para la distribucion de Linux Fedora
1. Actualizar repositorios e instalar Python, herramientas de desarrollo, venv y Java

**sudo dnf check-update**

**sudo dnf install python3 python3-pip python3-devel java-latest-openjdk -y**

2. Ir a la carpeta de tu proyecto (reemplaza con tu ruta real)

**cd /ruta/de/tu/proyecto**

3. Crear y activar el entorno virtual aislado

**python3 -m venv env**

**source env/bin/activate**

4. Instalar las librerías requeridas dentro del entorno

**pip install --upgrade pip**

**pip install streamlit pandas owlready2**

5. Ejecutar tu tutor inteligente

**streamlit run main.py**
