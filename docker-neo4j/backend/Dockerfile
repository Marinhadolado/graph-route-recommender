# Usa una imagen oficial de Python
FROM python:3.10

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# copiar primero el archivo de requisitos
COPY requirements.txt .

# instalar las dependencias de Python
RUN pip install -r requirements.txt

# Copia el contenido del directorio actual al directorio de trabajo en el contenedor
COPY . .

# para ejecutar el main creado donde se usan todos los archivos del src
CMD ["python3", "src/main.py"]