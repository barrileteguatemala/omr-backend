from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import tempfile
import os
import base64
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['ORT_PROVIDERS'] = 'CPUExecutionProvider'

app = FastAPI(title="OMR Backend - AI Music Teacher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "OMR Backend running ✅"}

@app.post("/convert")
async def convert_score(file: UploadFile = File(...)):
    """Convierte PDF/imagen a MusicXML usando Oemer OMR"""
    
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
        raise HTTPException(400, "Formato no soportado. Usa PDF, PNG o JPG.")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Guardar archivo subido
        input_path = os.path.join(tmpdir, f"score.{ext}")
        content = await file.read()
        with open(input_path, 'wb') as f:
            f.write(content)
        
        # Si es PDF, convertir a imagen primero
        if ext == 'pdf':
            img_path = os.path.join(tmpdir, 'score.png')
            result = subprocess.run([
                'pdftoppm', '-png', '-r', '150', '-singlefile',
                input_path, os.path.join(tmpdir, 'score')
            ], capture_output=True)
            if result.returncode != 0:
                raise HTTPException(500, f"Error convirtiendo PDF: {result.stderr.decode()}")
            input_path = img_path
        
        # Correr Oemer OMR
        output_dir = os.path.join(tmpdir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        result = subprocess.run([
            'oemer', input_path,
            '--output', output_dir,
        ], capture_output=True, timeout=300)
        
        # Buscar MusicXML generado
        xml_file = None
        for f in os.listdir(output_dir):
            if f.endswith('.musicxml') or f.endswith('.xml'):
                xml_file = os.path.join(output_dir, f)
                break
        
        if not xml_file:
            raise HTTPException(500, f"Oemer no generó MusicXML. Error: {result.stderr.decode()[:2000]}")
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            musicxml = f.read()
        
        return {
            "status": "success",
            "musicxml": musicxml,
            "filename": file.filename
        }

@app.post("/convert-base64")
async def convert_base64(data: dict):
    """Convierte imagen en base64 a MusicXML"""
    
    if 'image' not in data:
        raise HTTPException(400, "Se requiere campo 'image' en base64")
    
    ext = data.get('ext', 'png').lower()
    img_data = base64.b64decode(data['image'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"score.{ext}")
        with open(input_path, 'wb') as f:
            f.write(img_data)
        
        output_dir = os.path.join(tmpdir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        result = subprocess.run([
            'oemer', input_path,
            '--output', output_dir,
        ], capture_output=True, timeout=300)
        
        xml_file = None
        for fname in os.listdir(output_dir):
            if fname.endswith('.musicxml') or fname.endswith('.xml'):
                xml_file = os.path.join(output_dir, fname)
                break
        
        if not xml_file:
            raise HTTPException(500, "No se pudo convertir la imagen")
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            musicxml = f.read()
        
        return {"status": "success", "musicxml": musicxml}
