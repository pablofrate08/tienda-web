import streamlit as st
import pandas as pd
import urllib.parse
import os
import html

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
    .product-card-img {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Generador Específico de Imágenes según Producto
# ---------------------------------------------------------
def generar_imagen_especifica_svg(descripcion):
    desc = str(descripcion).upper()
    
    # Detección de Gramaje
    gramaje = "80g"
    if "70G" in desc or "70 G" in desc:
        gramaje = "70g"
    elif "75G" in desc or "75 G" in desc:
        gramaje = "75g"
    elif "90G" in desc or "90 G" in desc:
        gramaje = "90g"
        
    # Detección de Tamaño
    tamano = "A4"
    if "OFICIO" in desc or "OF" in desc or "22X34" in desc:
        tamano = "OFICIO"
    elif "CARTA" in desc or "LETTER" in desc:
        tamano = "CARTA"
    elif "A3" in desc:
        tamano = "A3"

    # --- CATEGORÍA 1: RESMAS ---
    if 'RESMA' in desc or 'PAPEL OBRA' in desc:
        # Marca: BOREAL (Verde / Amarillo)
        if 'BOREAL' in desc:
            bg_pack = "%23eab308"  # Amarillo
            bg_header = "%23166534"  # Verde Boreal
            brand_name = "Boreal"
        # Marca: AUTOR (Azul / Blanco)
        elif 'AUTOR' in desc:
            bg_pack = "%232563eb"  # Azul Autor
            bg_header = "%231e3a8a"  # Azul Oscuro
            brand_name = "Autor"
        # Marca: LEDESMA / NAT / PUNAX (Ecológico / Crema / Naranja)
        elif 'LEDESMA' in desc or 'NAT' in desc or 'PUNAX' in desc:
            bg_pack = "%23d97706"  # Tono Kraft/Naranja
            bg_header = "%2378350f"  # Marrón
            brand_name = "Ledesma"
        # Marca Generica de Resma
        else:
            bg_pack = "%230284c7"  # Celeste
            bg_header = "%230369a1"
            brand_name = "Resma"

        svg_str = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 240' width='100%' height='180'>
            <rect width='300' height='240' fill='%23f1f5f9' rx='8'/>
            <ellipse cx='150' cy='210' rx='95' ry='12' fill='%23cbd5e1'/>
            <rect x='45' y='40' width='100' height='150' fill='%23ffffff' stroke='%2394a3b8' stroke-width='2' rx='3'/>
            <rect x='45' y='40' width='100' height='35' fill='{bg_header}' rx='2'/>
            <text x='95' y='62' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='13' text-anchor='middle'>{tamano}</text>
            <g transform='rotate(-4 180 120)'>
                <rect x='125' y='35' width='120' height='160' fill='{bg_pack}' stroke='%23475569' stroke-width='2' rx='4'/>
                <rect x='125' y='35' width='120' height='40' fill='{bg_header}'/>
                <text x='185' y='60' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='15' text-anchor='middle'>{tamano} {gramaje}</text>
                <rect x='140' y='90' width='90' height='55' fill='%23ffffff' rx='3'/>
                <text x='185' y='122' fill='%230f172a' font-family='sans-serif' font-weight='bold' font-size='16' text-anchor='middle'>{brand_name}</text>
            </g>
        </svg>"""
        return f"data:image/svg+xml;utf8,{svg_str}"

    # --- CATEGORÍA 2: ESCRITURA (Lápices, Bolígrafos, Marcadores) ---
    elif any(k in desc for k in ['LAPIZ', 'MARCADOR', 'FIBRA', 'LAPICERA', 'BOLIGRAFO', 'MICROFIBRA', 'ROLLER']):
        svg_str = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 240' width='100%' height='180'>
            <rect width='300' height='240' fill='%23f1f5f9' rx='8'/>
            <ellipse cx='150' cy='205' rx='75' ry='10' fill='%23cbd5e1'/>
            <polygon points='85,180 100,180 100,50 85,50' fill='%23f59e0b'/>
            <polygon points='85,50 100,50 92,30' fill='%23fde047'/>
            <polygon points='90,38 95,38 92,30' fill='%231e293b'/>
            <rect x='120' y='45' width='22' height='135' fill='%232563eb' rx='3'/>
            <rect x='120' y='25' width='22' height='25' fill='%231e40af' rx='2'/>
            <rect x='155' y='60' width='26' height='120' fill='%23dc2626' rx='4'/>
            <rect x='155' y='40' width='26' height='25' fill='%23991b1b' rx='2'/>
        </svg>"""
        return f"data:image/svg+xml;utf8,{svg_str}"

    # --- CATEGORÍA 3: CUADERNOS Y REPUESTOS ---
    elif any(k in desc for k in ['CUADERNO', 'REPUESTO', 'HOJA', 'LIBRETA', 'BLOCK', 'ANOTADOR']):
        svg_str = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 240' width='100%' height='180'>
            <rect width='300' height='240' fill='%23f1f5f9' rx='8'/>
            <ellipse cx='150' cy='210' rx='85' ry='10' fill='%23cbd5e1'/>
            <rect x='75' y='35' width='150' height='170' fill='%231e3a8a' rx='6'/>
            <rect x='92' y='35' width='133' height='170' fill='%232563eb' rx='2'/>
            <circle cx='84' cy='55' r='5' fill='%2394a3b8'/><circle cx='84' cy='85' r='5' fill='%2394a3b8'/>
            <circle cx='84' cy='115' r='5' fill='%2394a3b8'/><circle cx='84' cy='145' r='5' fill='%2394a3b8'/>
            <circle cx='84' cy='175' r='5' fill='%2394a3b8'/>
            <rect x='110' y='75' width='95' height='14' fill='%23ffffff' rx='2'/>
            <text x='157' y='125' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='15' text-anchor='middle'>CUADERNO</text>
        </svg>"""
        return f"data:image/svg+xml;utf8,{svg_str}"

    # --- CATEGORÍA 4: ARTÍCULOS GENERALES DE LIBRERÍA ---
    else:
        svg_str = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 240' width='100%' height='180'>
            <rect width='300' height='240' fill='%23f1f5f9' rx='8'/>
            <ellipse cx='150' cy='205' rx='70' ry='10' fill='%23cbd5e1'/>
            <path d='M 75 175 L 225 175 L 215 155 L 85 155 Z' fill='%23475569'/>
            <path d='M 85 150 L 215 150 C 215 115 165 105 125 115 L 85 150 Z' fill='%230f172a'/>
            <rect x='80' y='170' width='145' height='10' fill='%230f172a' rx='2'/>
            <text x='150' y='80' fill='%23334155' font-family='sans-serif' font-weight='bold' font-size='13' text-anchor='middle'>LIBRERIA / OFICINA</text>
        </svg>"""
        return f"data:image/svg+xml;utf8,{svg_str}"

# ---------------------------------------------------------
# 3. Carga y Preparación del Catálogo
# ---------------------------------------------------------
@st.cache_data
def cargar_datos():
    archivo = 'derivadosll.xlsx'
    if not os.path.exists(archivo):
        archivo = 'actualizacionesll.xlsx'
    
    df = pd.read_excel(archivo)
    
    col_precio = 'PRECIOFINAL' if 'PRECIOFINAL' in df.columns else 'FINAL'
    
    df_limpio = df[['COD_ARTICU', 'DESCRIPCIO', col_precio]].dropna().copy()
    df_limpio['COD_ARTICU'] = df_limpio['COD_ARTICU'].astype(str).str.strip()
    df_limpio['DESCRIPCIO'] = df_limpio['DESCRIPCIO'].astype(str).str.strip()
    df_limpio['PRECIO'] = df_limpio[col_precio].astype(float).round(2)
    
    # Generación de imagen específica
    df_limpio['IMAGEN_DATA'] = df_limpio['DESCRIPCIO'].apply(generar_imagen_especifica_svg)
    
    return df_limpio

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error al conectar con la base de datos de productos: {e}")
    st.stop()

# Inicialización del carrito
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# ---------------------------------------------------------
# 4. Encabezado / Banner Institucional
# ---------------------------------------------------------
st.markdown("""
    <div class="header-box">
        <h1>📚 TIENDA VIRTUAL LKCFRATE</h1>
        <p>Distribución de Artículos de Librería, Comercial & Escolar</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Barra Lateral de Navegación & Filtros
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Panel de Filtros")
    modo_vista = st.radio("Cantidad de productos en pantalla:", ["Mostrar 20 Destacados", "Ver Catálogo Completo"])
    st.divider()
    st.markdown("### 📞 Atención al Cliente")
    st.info("Atención de Lunes a Viernes de 8:00 a 17:00 hs.\n\nEnvíos a todo el país.")

# ---------------------------------------------------------
# 6. Cuerpo Principal: Búsqueda y Productos
# ---------------------------------------------------------
col_tienda, col_carrito = st.columns([2.2, 1])

with col_tienda:
    st.subheader("🔎 Buscador de Productos")
    busqueda = st.text_input(
        "Buscar por nombre o código de artículo:",
        placeholder="Ej: BOREAL, AUTOR, LEDESMA, RESMA, ABACO, TEMPERA...",
        key="main_search"
    ).upper().strip()

    if busqueda:
        resultados = df[
            df['COD_ARTICU'].str.upper().str.contains(busqueda) | 
            df['DESCRIPCIO'].str.upper().str.contains(busqueda)
        ]
    else:
        if modo_vista == "Ver Catálogo Completo":
            resultados = df
        else:
            resultados = df.head(20)

    st.caption(f"Mostrando **{len(resultados)}** artículos encontrados de **{len(df):,}** disponibles.")
    st.divider()

    for idx, row in resultados.iterrows():
        with st.container(border=True):
            img_col, text_col, action_col = st.columns([1.3, 2.4, 1.3])
            
            with img_col:
                # Renderizado limpio a través de un contenedor HTML optimizado
                img_src = html.escape(row['IMAGEN_DATA'])
                st.markdown(
                    f"<div class='product-card-img'><img src='{img_src}' style='max-width:100%; height:auto;'/></div>",
                    unsafe_allow_html=True
                )
                
            with text_col:
                st.markdown(f"### {row['DESCRIPCIO']}")
                st.markdown(f"Código: <span class='code-badge'>{row['COD_ARTICU']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Precio Unitario:** `${row['PRECIO']:,.2f}`")
                
            with action_col:
                cant = st.number_input("Cantidad:", min_value=1, value=1, key=f"cant_{idx}")
                if st.button("🛒 Agregar", key=f"btn_{idx}", type="secondary", use_container_width=True):
                    st.session_state.carrito.append({
                        "codigo": row['COD_ARTICU'],
                        "nombre": row['DESCRIPCIO'],
                        "precio": row['PRECIO'],
                        "cantidad": cant,
                        "subtotal": row['PRECIO'] * cant
                    })
                    st.toast(f"Agregado al carrito: {row['DESCRIPCIO']}", icon="✅")

# ---------------------------------------------------------
# 7. Columna Derecha: Carrito y Pedido Formal
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
