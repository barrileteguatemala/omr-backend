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
RUN python -c "import oemer; print('Oemer ready')" || true
RUN oemer --help || true
RUN python -c "
import os, urllib.request
base = '/usr/local/lib/python3.10/site-packages/oemer/checkpoints'
os.makedirs(base + '/unet_big', exist_ok=True)
os.makedirs(base + '/seg_net', exist_ok=True)
files = [
    ('https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx', base + '/unet_big/model.onnx'),
    ('https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model_metadata.json', base + '/unet_big/metadata.json'),
    ('https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx', base + '/seg_net/model.onnx'),
    ('https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model_metadata.json', base + '/seg_net/metadata.json'),
]
for url, path in files:
    if not os.path.exists(path):
        print(f'Downloading {url}')
        urllib.request.urlretrieve(url, path)
        print(f'Saved to {path}')
print('Models ready')
" 

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
