import streamlit as st
import pandas as pd
import requests
import json
import urllib.parse
import os
import io
import math
from PIL import Image, ImageDraw

# ---------------------------------------------------------
# 1. Configuración de la página (Estilo Corporativo)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tienda Virtual Lkcfrate | Mayorista & Minorista",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .header-box {
        background: linear-gradient(135deg, #0d3b66 0%, #001f3f 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-box h1 {
        color: #ffffff;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .header-box p {
        color: #e0e6ed;
        font-size: 1.1rem;
    }
    .code-badge {
        background-color: #eef2f7;
        color: #4a5568;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: monospace;
    }
    .price-tag {
        font-size: 1.2rem;
        font-weight: bold;
        color: #10b981;
    }
    .price-missing {
        font-size: 1rem;
        font-weight: 600;
        color: #f59e0b;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Gestión de Caché Persistente de Imágenes
# ---------------------------------------------------------
CACHE_FILE = "imagenes_cache.json"

def cargar_cache_imagenes():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_cache_imagenes(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if 'imagenes_cache' not in st.session_state:
    st.session_state.imagenes_cache = cargar_cache_imagenes()

# ---------------------------------------------------------
# 3. Generador PNG de Resguardo en Memoria (Evita FileNotFoundError)
# ---------------------------------------------------------
def generar_imagen_respaldo_png(descripcion, codigo):
    width, height = 400, 300
    image = Image.new('RGB', (width, height), color='#f8fafc')
    draw = ImageDraw.Draw(image)
    
    # Bordes limpios
    draw.rectangle([(8, 8), (width-8, height-8)], outline='#e2e8f0', width=2)
    draw.rectangle([(20, 20), (width-20, height-20)], fill='#ffffff', outline='#cbd5e1', width=1)
    
    d_text = str(descripcion).upper()
    if len(d_text) > 28:
        d_text = d_text[:26] + "..."
        
    c_text = f"Cód: {codigo}"
    
    draw.text((200, 90), "📦 LKCFRATE LIBRERÍA", fill='#0284c7', anchor="ms")
    draw.text((200, 135), d_text, fill='#0f172a', anchor="ms")
    draw.text((200, 175), c_text, fill='#475569', anchor="ms")
    draw.text((200, 215), "Imagen no disponible en catálogo", fill='#94a3b8', anchor="ms")
    
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# 4. Buscador Automático de Imágenes Reales (Mercado Libre MLA)
# ---------------------------------------------------------
def buscar_imagen_real_producto(row):
    cod_art = str(row.get('COD_ARTICU', '')).strip()
    desc = str(row.get('DESCRIPCIO', '')).strip()
    cod_barra = str(row.get('COD_BARRA', '')).strip() if 'COD_BARRA' in row and pd.notna(row.get('COD_BARRA')) else ""
    
    cache_key = cod_art if cod_art else desc
    
    if cache_key in st.session_state.imagenes_cache:
        return st.session_state.imagenes_cache[cache_key]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Estrategia de búsqueda
    consultas = []
    if cod_barra and len(cod_barra) >= 8 and cod_barra.isdigit():
        consultas.append(cod_barra)
    if desc:
        consultas.append(f"{desc}")
        
    for q in consultas:
        try:
            url_api = f"https://api.mercadolibre.com/sites/MLA/search?q={urllib.parse.quote(q)}&limit=1"
            resp = requests.get(url_api, headers=headers, timeout=2.5)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('results', [])
                if results:
                    thumb = results[0].get('thumbnail', '')
                    if thumb:
                        # Mejora la resolución sustituyendo -I.jpg por -O.jpg
                        high_res = thumb.replace("-I.jpg", "-O.jpg").replace("http://", "https://")
                        st.session_state.imagenes_cache[cache_key] = high_res
                        guardar_cache_imagenes(st.session_state.imagenes_cache)
                        return high_res
        except Exception:
            continue
            
    # Guarda None si no encuentra resultado online para usar el respaldo
    st.session_state.imagenes_cache[cache_key] = None
    guardar_cache_imagenes(st.session_state.imagenes_cache)
    return None

# ---------------------------------------------------------
# 5. Carga Completa del Excel (Sin descartar filas)
# ---------------------------------------------------------
@st.cache_data
def cargar_datos():
    archivo = 'derivadosll.xlsx'
    if not os.path.exists(archivo):
        archivo = 'actualizacionesll.xlsx'
        
    df = pd.read_excel(archivo)
    
    col_precio = 'PRECIOFINAL' if 'PRECIOFINAL' in df.columns else ('FINAL' if 'FINAL' in df.columns else None)
    
    df_limpio = df.copy()
    
    if 'COD_ARTICU' not in df_limpio.columns:
        df_limpio['COD_ARTICU'] = df_limpio.index.astype(str)
    if 'DESCRIPCIO' not in df_limpio.columns:
        df_limpio['DESCRIPCIO'] = "Producto sin descripción"
        
    df_limpio['COD_ARTICU'] = df_limpio['COD_ARTICU'].astype(str).str.strip()
    df_limpio['DESCRIPCIO'] = df_limpio['DESCRIPCIO'].astype(str).str.strip()
    
    if col_precio:
        df_limpio['PRECIO'] = pd.to_numeric(df_limpio[col_precio], errors='coerce')
    else:
        df_limpio['PRECIO'] = None
        
    if 'COD_BARRA' in df_limpio.columns:
        df_limpio['COD_BARRA'] = df_limpio['COD_BARRA'].astype(str).str.strip().replace('nan', '')
    else:
        df_limpio['COD_BARRA'] = ""
        
    return df_limpio

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error al conectar con el archivo Excel de productos: {e}")
    st.stop()

# Inicialización del carrito
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# ---------------------------------------------------------
# 6. Encabezado / Banner Institucional
# ---------------------------------------------------------
st.markdown("""
    <div class="header-box">
        <h1>📚 TIENDA VIRTUAL LKCFRATE</h1>
        <p>Distribución de Artículos de Librería, Comercial & Escolar</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. Barra Lateral de Navegación, Filtros y Paginación
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Panel de Control")
    st.write(f"Total en Catálogo: **{len(df):,}** artículos")
    
    PRODUCTOS_POR_PAGINA = 20
    
    st.divider()
    st.markdown("### 📞 Atención al Cliente")
    st.info("Atención de Lunes a Viernes de 8:00 a 17:00 hs.\n\nEnvíos a todo el país.")

# ---------------------------------------------------------
# 8. Cuerpo Principal: Búsqueda y Resultados Paginados
# ---------------------------------------------------------
col_tienda, col_carrito = st.columns([2.2, 1])

with col_tienda:
    st.subheader("🔎 Buscador de Productos")
    busqueda = st.text_input(
        "Buscar por nombre, código de artículo o código de barras:",
        placeholder="Ej: BOREAL, RESMA, ABACO, TEMPERA, 013714...",
        key="main_search"
    ).upper().strip()

    if busqueda:
        resultados = df[
            df['COD_ARTICU'].str.upper().str.contains(busqueda) | 
            df['DESCRIPCIO'].str.upper().str.contains(busqueda) |
            df['COD_BARRA'].str.upper().str.contains(busqueda)
        ]
    else:
        resultados = df

    total_resultados = len(resultados)
    total_paginas = max(1, math.ceil(total_resultados / PRODUCTOS_POR_PAGINA))
    
    col_info, col_pag = st.columns([1.5, 1])
    with col_info:
        st.caption(f"Mostrando **{total_resultados:,}** artículos encontrados de **{len(df):,}** disponibles.")
    with col_pag:
        pagina_actual = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1, step=1)

    st.divider()

    inicio_idx = (pagina_actual - 1) * PRODUCTOS_POR_PAGINA
    fin_idx = inicio_idx + PRODUCTOS_POR_PAGINA
    pagina_productos = resultados.iloc[inicio_idx:fin_idx]

    # Renderizado de Tarjetas de Productos
    for idx, row in pagina_productos.iterrows():
        with st.container(border=True):
            img_col, text_col, action_col = st.columns([1.2, 2.5, 1.3])
            
            with img_col:
                img_url = buscar_imagen_real_producto(row)
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    png_fallback = generar_imagen_respaldo_png(row['DESCRIPCIO'], row['COD_ARTICU'])
                    st.image(png_fallback, use_container_width=True)
                
            with text_col:
                st.markdown(f"### {row['DESCRIPCIO']}")
                
                detalles = f"Código: <span class='code-badge'>{row['COD_ARTICU']}</span>"
                if row['COD_BARRA']:
                    detalles += f" | Cód. Barra: <span class='code-badge'>{row['COD_BARRA']}</span>"
                st.markdown(detalles, unsafe_allow_html=True)
                
                if pd.notna(row['PRECIO']) and row['PRECIO'] > 0:
                    st.markdown(f"<span class='price-tag'>${row['PRECIO']:,.2f}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='price-missing'>Consultar precio</span>", unsafe_allow_html=True)
                
            with action_col:
                cant = st.number_input("Cantidad:", min_value=1, value=1, key=f"cant_{idx}")
                
                # Deshabilitar botón de agregar si no tiene precio
                puede_agregar = pd.notna(row['PRECIO']) and row['PRECIO'] > 0
                
                if st.button("🛒 Agregar", key=f"btn_{idx}", disabled=not puede_agregar, use_container_width=True):
                    st.session_state.carrito.append({
                        "codigo": row['COD_ARTICU'],
                        "nombre": row['DESCRIPCIO'],
                        "precio": row['PRECIO'],
                        "cantidad": cant,
                        "subtotal": row['PRECIO'] * cant
                    })
                    st.toast(f"Agregado al carrito: {row['DESCRIPCIO']}", icon="✅")

# ---------------------------------------------------------
# 9. Columna Derecha: Carrito y Pedido Formal
# ---------------------------------------------------------
with col_carrito:
    st.subheader("🛍️ Resumen de Compra")

    if not st.session_state.carrito:
        st.info("El carrito de compras está vacío.")
    else:
        total_acumulado = 0
        resumen_texto = "📋 *NUEVO PEDIDO DE COMPRA - TIENDA LKCFRATE*\n\n"
        
        for item in st.session_state.carrito:
            st.markdown(f"• **{item['cantidad']}x** {item['nombre']}")
            st.caption(f"Cód: {item['codigo']} | Subtotal: ${item['subtotal']:,.2f}")
            total_acumulado += item['subtotal']
            resumen_texto += f"- [{item['codigo']}] {item['cantidad']}x {item['nombre']} = ${item['subtotal']:,.2f}\n"
        
        st.divider()
        st.markdown(f"### **Total Final: ${total_acumulado:,.2f}**")

        if st.button("Vaciar Carrito 🗑️", use_container_width=True):
            st.session_state.carrito = []
            st.rerun()

        st.divider()
        st.subheader("💳 Finalización del Pedido")
        metodo = st.radio("Forma de Pago / Retiro:", ["Efectivo / Transferencia", "Mercado Pago"])

        resumen_texto += f"\n*TOTAL COMPRA:* ${total_acumulado:,.2f}\n*FORMA DE PAGO:* {metodo}"

        if metodo == "Mercado Pago":
            link_mp = "https://link.mercadopago.com.ar/TULINKAQUI" 
            st.link_button("Pagar con Mercado Pago 💳", link_mp, type="primary", use_container_width=True)
        else:
            telefono_ws = "549343XXXXXXX"
            url_whatsapp = f"https://wa.me/{telefono_ws}?text={urllib.parse.quote(resumen_texto)}"
            st.link_button("Enviar Orden por WhatsApp 📲", url_whatsapp, type="primary", use_container_width=True)
