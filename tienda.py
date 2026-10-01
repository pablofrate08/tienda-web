import pandas as pd
import requests
import json
import urllib.parse
import os

print("🚀 Iniciando búsqueda masiva de imágenes para derivadosll.xlsx...")

df = pd.read_excel('derivadosll.xlsx')
cache = {}

if os.path.exists('imagenes_cache.json'):
    with open('imagenes_cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)

headers = {'User-Agent': 'Mozilla/5.0'}
actualizados = 0

for idx, row in df.iterrows():
    cod_art = str(row.get('COD_ARTICU', '')).strip()
    desc = str(row.get('DESCRIPCIO', '')).strip()
    cod_barra = str(row.get('COD_BARRA', '')).strip() if 'COD_BARRA' in row and pd.notna(row.get('COD_BARRA')) else ""
    
    key = cod_art if cod_art else desc
    if key in cache and cache[key]:
        continue

    # Prioridad: Código de Barras > Descripción
    query = cod_barra if (cod_barra and len(cod_barra) >= 8 and cod_barra.isdigit()) else desc
    
    if not query or query == "nan":
        continue

    try:
        url_api = f"https://api.mercadolibre.com/sites/MLA/search?q={urllib.parse.quote(query)}&limit=1"
        resp = requests.get(url_api, headers=headers, timeout=2)
        if resp.status_code == 200:
            results = resp.json().get('results', [])
            if results:
                thumb = results[0].get('thumbnail', '').replace("-I.jpg", "-O.jpg").replace("http://", "https://")
                cache[key] = thumb
                actualizados += 1
                print(f"[{idx+1}/{len(df)}] Encontrada: {desc[:25]}... -> {thumb}")
    except Exception:
        pass

    # Guarda avance cada 100 productos
    if actualizados % 100 == 0 and actualizados > 0:
        with open('imagenes_cache.json', 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

with open('imagenes_cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f"✅ ¡Proceso finalizado! Se asociaron {len(cache)} imágenes en imagenes_cache.json")
