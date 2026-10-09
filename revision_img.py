import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

archivo_cache = 'imagenes_cache.json'
archivo_revision = 'imagenes_a_revisar.json'

# 1. Cargar el caché original
try:
    with open(archivo_cache, 'r', encoding='utf-8') as f:
        cache = json.load(f)
except FileNotFoundError:
    print("❌ No se encontró el archivo imagenes_cache.json.")
    exit()

total_imagenes = len(cache)
print(f"🚀 Auditando {total_imagenes} enlaces a máxima velocidad...")

# Usar una sesión global reduce el tiempo de conexión a la mitad
sesion = requests.Session()

# 2. Función de validación súper rápida
def auditar_url(codigo, url):
    if not url or "unsplash.com" in url:
        return codigo, url, True
        
    try:
        # Reducimos el timeout a 2 segundos para no perder tiempo con servidores lentos
        respuesta = sesion.head(url, timeout=2, allow_redirects=True)
        if respuesta.status_code >= 400:
            return codigo, url, True
        return codigo, url, False
    except requests.RequestException:
        return codigo, url, True

# 3. Procesamiento en paralelo con seguimiento
imagenes_falladas = {}
completadas = 0
candado = threading.Lock() # Para actualizar los números en pantalla sin errores

# Subimos a 50 conexiones simultáneas
with ThreadPoolExecutor(max_workers=50) as executor:
    # Enviamos todas las tareas
    futuros = [executor.submit(auditar_url, cod, url) for cod, url in cache.items()]
    
    # A medida que se van terminando, actualizamos la pantalla
    for futuro in as_completed(futuros):
        codigo, url, esta_rota = futuro.result()
        
        if esta_rota:
            imagenes_falladas[codigo] = url
            
        with candado:
            completadas += 1
            porcentaje = (completadas / total_imagenes) * 100
            # El \r hace que se reescriba la misma línea, creando un efecto de barra de carga
            print(f"\r⏳ Progreso: {completadas}/{total_imagenes} [{porcentaje:.1f}%] | ❌ Falladas detectadas: {len(imagenes_falladas)}", end="", flush=True)

# 4. Guardar el reporte de errores
with open(archivo_revision, 'w', encoding='utf-8') as f:
    json.dump(imagenes_falladas, f, ensure_ascii=False, indent=2)

print(f"\n\n✅ ¡Auditoría terminada al 100%! Se encontraron {len(imagenes_falladas)} imágenes con problemas.")
print(f"📂 El reporte listo para revisar manualmente se guardó en: {archivo_revision}")