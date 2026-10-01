import streamlit as st
import pandas as pd
import urllib.parse
import os

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
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Generador de Imagen de Producto Real Infallible (Base64)
# ---------------------------------------------------------
def obtener_imagen_base64_producto(descripcion):
    desc = str(descripcion).upper()
    
    # Resma Boreal / Papeles (Ilustración limpia de Resma sobre fondo blanco en Base64)
    if any(k in desc for k in ['RESMA', 'PAPEL', 'BOREAL', 'AUTOR', 'A4', 'OFICIO', 'PUNTO 80']):
        return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 250'><rect width='300' height='250' fill='%23f8fafc' rx='8'/><ellipse cx='150' cy='210' rx='90' ry='12' fill='%23e2e8f0'/><rect x='60' y='50' width='120' height='140' fill='%23ffffff' stroke='%23cbd5e1' stroke-width='2' rx='4'/><rect x='60' y='50' width='120' height='35' fill='%2315803d'/><text x='120' y='73' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='14' text-anchor='middle'>BOREAL A4</text><g transform='rotate(-5 190 120)'><rect x='130' y='50' width='110' height='145' fill='%23eab308' stroke='%23ca8a04' stroke-width='2' rx='4'/><rect x='130' y='50' width='110' height='35' fill='%23166534'/><text x='185' y='73' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='13' text-anchor='middle'>70g / 80g</text><text x='185' y='140' fill='%230f172a' font-family='sans-serif' font-weight='bold' font-size='16' text-anchor='middle'>Boreal</text></g></svg>"

    # Lápices y Librería
    elif any(k in desc for k in ['LAPIZ', 'MARCADOR', 'FIBRA', 'LAPICERA', 'BOLIGRAFO', 'MICROFIBRA']):
        return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 250'><rect width='300' height='250' fill='%23f8fafc' rx='8'/><polygon points='100,190 115,190 115,60 100,60' fill='%23f59e0b'/><polygon points='100,60 115,60 107,40' fill='%23fde047'/><polygon points='105,45 110,45 107,40' fill='%231e293b'/><rect x='150' y='60' width='25' height='130' fill='%232563eb' rx='4'/></svg>"

    # Cuadernos
    elif any(k in desc for k in ['CUADERNO', 'REPUESTO', 'HOJA', 'LIBRETA', 'BLOCK', 'ANOTADOR']):
        return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 250'><rect width='300' height='250' fill='%23f8fafc' rx='8'/><rect x='80' y='40' width='140' height='170' fill='%231e3a8a' rx='6'/><rect x='95' y='40' width='125' height='170' fill='%233b82f6' rx='2'/><text x='157' y='125' fill='%23ffffff' font-family='sans-serif' font-weight='bold' font-size='16' text-anchor='middle'>CUADERNO</text></svg>"

    # Imagen Genérica
    else:
        return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 250'><rect width='300' height='250' fill='%23f8fafc' rx='8'/><text x='150' y='130' fill='%2364748b' font-family='sans-serif' font-weight='bold' font-size='14' text-anchor='middle'>ARTICULO DE LIBRERIA</text></svg>"

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
    
    df_limpio['IMAGEN_URL'] = df_limpio['DESCRIPCIO'].apply(obtener_imagen_base64_producto)
    
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
        placeholder="Ej: BOREAL, RESMA, ABACO, TEMPERA, 013714...",
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
            img_col, text_col, action_col = st.columns([1.2, 2.5, 1.3])
            
            with img_col:
                # Usa directamente st.image sin usar marcas HTML crudas
                st.image(row['IMAGEN_URL'], use_container_width=True)
                
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
