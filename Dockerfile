# Usa una versión específica de Python compatible con ARM64
FROM python:slim AS basetelethon

# Evitar buffering en la salida de Python (útil en contenedores)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar dependencias antes para aprovechar la caché de Docker
COPY requirements.txt requirements.txt

# Agregar repositorios necesarios y actualizar paquetes
RUN    apt-get update && apt-get -qy dist-upgrade && \
    apt-get install -qy --no-install-recommends \
    ffmpeg \
    unzip && \
    rm -rf /var/lib/apt/lists/*

# Actualizar pip e instalar dependencias sin caché para reducir tamaño
RUN python3 -m pip install --no-cache-dir --upgrade pip 
RUN pip install -r requirements.txt

# Segunda etapa para reducir el tamaño de la imagen final
FROM python:slim

WORKDIR /app

# Copiar aplicación desde la imagen base
COPY --from=basetelethon /app /app

# Copiar código fuente
COPY telethon-downloader /app

# Asegurar permisos correctos
RUN chmod +x /app/bottorrent.py

# Definir volúmenes
VOLUME /download /watch /config

# Comando de ejecución
CMD ["python3", "/app/bottorrent.py"]
