import pandas as pd
import json
import os
import time
import requests
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from ddgs import DDGS

archivo_cache = 'imagenes_cache.json'
archivo_revision = 'imagenes_a_revisar.json'
excel_file = 'derivadosll.xlsx' if os.path.exists('derivadosll.xlsx') else 'actualizacionesll.xlsx'

print("🚀 Iniciando Reparación Automática MULTIHILO...")

# 1. Verificaciones y Carga
if not os.path.exists(archivo_revision) or not os.path.exists(excel_file):
    print("❌ Faltan archivos necesarios (Excel o imagenes_a_revisar.json).")
    exit()

with open(archivo_cache, 'r', encoding='utf-8') as f:
    cache = json.load(f)
with open(archivo_revision, 'r', encoding='utf-8') as f:
    imagenes_rotas = json.load(f)

if not imagenes_rotas:
    print("✨ No hay imágenes para reparar. El archivo está vacío.")
    exit()

# Cargar nombres del Excel
df = pd.read_excel(excel_file)
diccionario_nombres = {
    str(row['COD_ARTICU']).strip() if pd.notna(row['COD_ARTICU']) else str(idx): str(row['DESCRIPCIO']).strip()
    for idx, row in df.iterrows() if pd.notna(row['DESCRIPCIO'])
}

# 2. Funciones súper rápidas
sesion_req = requests.Session()

def enlace_es_valido(url):
    try:
        # Pide solo el encabezado, súper rápido
        r = sesion_req.head(url, timeout=2, allow_redirects=True)
        return r.status_code < 400
    except:
        return False

def procesar_reparacion(codigo):
    descripcion = diccionario_nombres.get(codigo, "")
    if not descripcion or descripcion.lower() == "nan":
        return codigo, None

    query = f"articulo de libreria {descripcion}".replace("/", " ")
    intentos = 0
    
    while intentos < 2:
        try:
            # Micro-pausa aleatoria para burlar el anti-bot
            time.sleep(random.uniform(0.5, 1.5)) 
            with DDGS() as ddgs:
                resultados = list(ddgs.images(query, max_results=3))
            
            for res in resultados:
                nueva_url = res.get('image')
                if nueva_url and enlace_es_valido(nueva_url):
                    return codigo, nueva_url
            break # Si no hubo error pero ninguna funcionó, sale del bucle
            
        except Exception:
            intentos += 1
            time.sleep(3) # Pausa de enfriamiento si detecta bloqueo temporal
            
    return codigo, None

# 3. Lanzamiento Paralelo
reparadas = 0
total_rotas = len(imagenes_rotas)
procesadas = 0
candado = threading.Lock()

print(f"\n⚡ Buscando {total_rotas} reemplazos con 5 trabajadores en simultáneo...")

# El límite seguro es 5. Más de esto y DDG bloquea la IP.
with ThreadPoolExecutor(max_workers=5) as executor:
    futuros = [executor.submit(procesar_reparacion, cod) for cod in imagenes_rotas.keys()]
    
    for futuro in as_completed(futuros):
        codigo, nueva_url = futuro.result()
        
        with candado:
            procesadas += 1
            if nueva_url:
                cache[codigo] = nueva_url
                reparadas += 1
                
            porcentaje = (procesadas / total_rotas) * 100
            print(f"\r⏳ Progreso: {procesadas}/{total_rotas} [{porcentaje:.1f}%] | ✅ Fotos salvadas: {reparadas}", end="", flush=True)

# 4. Guardado Final
with open(archivo_cache, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

# Vaciar archivo de revisión porque ya las intentamos reparar todas
with open(archivo_revision, 'w', encoding='utf-8') as f:
    json.dump({}, f)

print(f"\n\n🎉 ¡Súper Reparación Finalizada! Se consiguieron {reparadas} imágenes nuevas al instante.")
print("💾 El archivo principal 'imagenes_cache.json' ha sido actualizado.")