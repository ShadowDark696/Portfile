#!/usr/bin/env python3
"""
Script para aplicar watermark a todas las imágenes en la carpeta Models
"""

import os
from PIL import Image
from pathlib import Path

# Configuración
MODELS_FOLDER = Path(__file__).parent / "Models"
WATERMARK_NAME = "WaterMark_ShadowDark.png"
OUTPUT_FOLDER = MODELS_FOLDER / "watermarked"
WATERMARK_OPACITY = 0.8  # 0.0 a 1.0 (0.8 = 80% opacidad, 20% transparente)
WATERMARK_POSITIONS = ["center", "top-left", "top-right", "bottom-left", "bottom-right"]  # 5 posiciones
WATERMARK_SIZE_PERCENT = 80  # Porcentaje del tamaño de la imagen (gigante)

def create_watermark(watermark_path, image_size, opacity=WATERMARK_OPACITY):
    """Carga y prepara el watermark"""
    watermark = Image.open(watermark_path).convert("RGBA")
    
    # Redimensiona el watermark según el porcentaje
    img_width, img_height = image_size
    watermark_width = int(img_width * WATERMARK_SIZE_PERCENT / 100)
    aspect_ratio = watermark.height / watermark.width
    watermark_height = int(watermark_width * aspect_ratio)
    
    watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
    
    # Aplicar opacidad al canal alpha
    if opacity < 1.0:
        r, g, b, a = watermark.split()
        a = a.point(lambda p: int(p * opacity))  # Reducir opacidad
        watermark = Image.merge("RGBA", (r, g, b, a))
    
    return watermark

def get_watermark_position(image_size, watermark_size, position):
    """Calcula la posición del watermark"""
    img_width, img_height = image_size
    wm_width, wm_height = watermark_size
    padding = 10
    
    if position == "bottom-right":
        x = img_width - wm_width - padding
        y = img_height - wm_height - padding
    elif position == "bottom-left":
        x = padding
        y = img_height - wm_height - padding
    elif position == "top-right":
        x = img_width - wm_width - padding
        y = padding
    elif position == "top-left":
        x = padding
        y = padding
    elif position == "center":
        x = (img_width - wm_width) // 2
        y = (img_height - wm_height) // 2
    else:
        x, y = padding, img_height - wm_height - padding
    
    return (x, y)

def apply_watermark_to_image(image_path, watermark_path, output_path):
    """Aplica múltiples watermarks a una imagen"""
    try:
        # Abrir imagen
        image = Image.open(image_path).convert("RGBA")
        
        # Crear capa para los watermarks
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        
        # Aplicar múltiples watermarks en diferentes posiciones
        for position_name in WATERMARK_POSITIONS:
            watermark = create_watermark(watermark_path, image.size)
            position = get_watermark_position(image.size, watermark.size, position_name)
            watermark_layer.paste(watermark, position, watermark)
        
        # Componer imagen con watermarks
        result = Image.alpha_composite(image, watermark_layer)
        
        # Guardar como PNG para máxima nitidez
        result.save(output_path.with_suffix('.png'), format='PNG')
        return True
    except Exception as e:
        print(f"❌ Error procesando {image_path.name}: {e}")
        return False

def main():
    """Función principal"""
    if not MODELS_FOLDER.exists():
        print(f"❌ La carpeta {MODELS_FOLDER} no existe")
        return
    
    watermark_path = MODELS_FOLDER / WATERMARK_NAME
    if not watermark_path.exists():
        print(f"❌ El watermark {WATERMARK_NAME} no encontrado en {MODELS_FOLDER}")
        return
    
    # Crear carpeta de salida
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    # Obtener todas las imágenes (excepto el watermark)
    image_extensions = {'.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff'}
    images = [f for f in MODELS_FOLDER.glob('*') 
              if f.is_file() and f.suffix.lower() in image_extensions 
              and f.name != WATERMARK_NAME]
    
    if not images:
        print("❌ No se encontraron imágenes para procesar")
        return
    
    print(f"🎯 Procesando {len(images)} imagen(s)...\n")
    
    successful = 0
    for i, image_path in enumerate(images, 1):
        output_path = OUTPUT_FOLDER / image_path.name
        print(f"[{i}/{len(images)}] Procesando: {image_path.name}...", end=" ")
        
        if apply_watermark_to_image(image_path, watermark_path, output_path):
            print("✅")
            successful += 1
        else:
            print("❌")
    
    print(f"\n{'='*60}")
    print(f"✅ Proceso completado: {successful}/{len(images)} imágenes procesadas")
    print(f"📁 Imágenes guardadas en: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    main()
