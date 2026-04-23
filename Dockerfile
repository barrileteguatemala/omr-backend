FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir onnxruntime --force-reinstall

# Pre-descargar modelos de Oemer
RUN mkdir -p /usr/local/lib/python3.10/site-packages/oemer/checkpoints/unet_big && \
    mkdir -p /usr/local/lib/python3.10/site-packages/oemer/checkpoints/seg_net && \
    wget -q --no-check-certificate -L -O /usr/local/lib/python3.10/site-packages/oemer/checkpoints/unet_big/model.onnx https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx && \
    wget -q --no-check-certificate -L -O /usr/local/lib/python3.10/site-packages/oemer/checkpoints/unet_big/metadata.json https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model_metadata.json && \
    wget -q --no-check-certificate -L -O /usr/local/lib/python3.10/site-packages/oemer/checkpoints/seg_net/model.onnx https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx && \
    wget -q --no-check-certificate -L -O /usr/local/lib/python3.10/site-packages/oemer/checkpoints/seg_net/metadata.json https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model_metadata.json

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
