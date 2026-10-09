import pandas as pd
import json
import os
import re
import time
import sys
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ddgs import DDGS
except ImportError:
    print("❌ ERROR: Falta instalar la nueva librería. Ejecuta en la terminal: pip install ddgs")
    sys.exit()

print("🚀 Iniciando búsqueda WEB ACELERADA (Multihilo)...")

excel_file = 'derivadosll.xlsx' if os.path.exists('derivadosll.xlsx') else 'actualizacionesll.xlsx'
if not os.path.exists(excel_file):
    print("❌ Error: No se encontró el archivo Excel.")
    sys.exit()

df = pd.read_excel(excel_file)
col_desc = 'DESCRIPCIO'
col_cod = 'COD_ARTICU'

# 1. AGRUPAR PRODUCTOS
productos_agrupados = {}
for idx, row in df.iterrows():
    desc = str(row[col_desc]).strip() if pd.notna(row[col_desc]) else ""
    cod = str(row[col_cod]).strip() if pd.notna(row[col_cod]) else str(idx)
    
    if not desc or desc.lower() == "nan": continue
    if desc not in productos_agrupados: productos_agrupados[desc] = []
    if cod not in productos_agrupados[desc]: productos_agrupados[desc].append(cod)

descripciones_unicas = list(productos_agrupados.keys())
print(f"📦 Excel procesado. Se buscarán {len(descripciones_unicas)} imágenes únicas.")

# 2. CARGAR CACHÉ
cache = {}
archivo_cache = 'imagenes_cache.json'
if os.path.exists(archivo_cache):
    with open(archivo_cache, 'r', encoding='utf-8') as f:
        try:
            cache = json.load(f)
            print(f"🔄 Progreso anterior cargado: {len(cache)} códigos.")
        except Exception:
            pass

def limpiar_busqueda(texto):
    texto = str(texto).upper()
    diccionario = {"ABROCH": "ABROCHADORA", "PLAST": "PLASTICO", "COL": "COLORES",
                   "GRAP": "GRAPAS", "BOLIG": "BOLIGRAFO", "CUAD": "CUADERNO",
                   "RESM": "RESMA", "CART": "CARTULINA"}
    for abrev, palabra_completa in diccionario.items():
        texto = re.sub(rf'\b{abrev}\b', palabra_completa, texto)
    texto = re.sub(r'[^a-zA-Z0-9\s]', ' ', texto)
    palabras = texto.split()
    if len(palabras) >= 3:
        return f"{palabras[0]} {palabras[1]} {palabras[2]}"
    return " ".join(palabras)

# Candado de seguridad para que los hilos no choquen al guardar el archivo
lock_guardado = threading.Lock()
imagenes_procesadas = 0

# 3. FUNCIÓN QUE EJECUTA CADA "TRABAJADOR"
def procesar_producto(desc):
    codigos_asociados = productos_agrupados[desc]
    
    if codigos_asociados[0] in cache:
        return f"⏩ '{desc[:15]}...' ya en caché"

    query_base = limpiar_busqueda(desc)
    query_web = f"articulo libreria {query_base}"
    
    url_encontrada = None
    intentos = 0
    
    # Creamos una sesión nueva por cada trabajador para evitar cruces
    with DDGS() as ddgs:
        while intentos < 2:
            try:
                # Pausa aleatoria para simular comportamiento humano
                time.sleep(random.uniform(1.5, 3.0))
                resultados = list(ddgs.images(query_web, max_results=1))
                if resultados:
                    url_encontrada = resultados[0].get('image')
                break 
            except Exception as e:
                if "403" in str(e) or "Ratelimit" in str(e):
                    time.sleep(8) # Enfriamiento si lo bloquean
                    intentos += 1
                else:
                    break

    # Guardar resultados bloqueando el hilo momentáneamente
    with lock_guardado:
        if url_encontrada:
            for cod in codigos_asociados:
                cache[cod] = url_encontrada
            resultado = f"✅ Encontrado: {query_web}"
        else:
            resultado = f"❌ Sin foto: {query_web}"
            
        global imagenes_procesadas
        imagenes_procesadas += 1
        
        # Guardado de seguridad cada 20 productos procesados
        if imagenes_procesadas % 20 == 0:
            with open(archivo_cache, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
                
    return resultado

# 4. LANZAMIENTO DEL MULTIHILO
MAX_TRABAJADORES = 3  # <-- Si te tira muchos errores 403, baja esto a 2 o a 1

try:
    print(f"🚀 Iniciando {MAX_TRABAJADORES} trabajadores en simultáneo...")
    with ThreadPoolExecutor(max_workers=MAX_TRABAJADORES) as executor:
        futuros = {executor.submit(procesar_producto, desc): desc for desc in descripciones_unicas}
        
        for i, futuro in enumerate(as_completed(futuros), 1):
            resultado = futuro.result()
            print(f"[{i}/{len(descripciones_unicas)}] {resultado}")

except KeyboardInterrupt:
    print("\n\n🛑 PROCESO DETENIDO MANUALMENTE. GUARDANDO PROGRESO...")

finally:
    with lock_guardado:
        with open(archivo_cache, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"💾 Guardado de seguridad completado. Hay {len(cache)} imágenes en '{archivo_cache}'.")