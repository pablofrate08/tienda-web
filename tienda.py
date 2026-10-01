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
    .product-img-box {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Generador de Imágenes Integradas Infalibles (SVG)
# ---------------------------------------------------------
def obtener_svg_producto(descripcion):
    desc = str(descripcion).upper()
    
    # SVG 1: Resma Boreal / Papeles (Verde y Amarillo con Caja y Paquete)
    if any(k in desc for k in ['RESMA', 'PAPEL', 'BOREAL', 'AUTOR', 'A4', 'OFICIO', 'PUNTO 80']):
        return """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 250" width="100%" height="180">
            <!-- Fondo neutro e-commerce -->
            <rect width="300" height="250" fill="#f1f5f9" rx="8"/>
            <!-- Sombra -->
            <ellipse cx="150" cy="220" rx="110" ry="12" fill="#cbd5e1"/>
            
            <!-- Caja de Resmas Boreal (Atrás) -->
            <rect x="40" y="70" width="110" height="130" fill="#ffffff" stroke="#94a3b8" stroke-width="2" rx="3"/>
            <rect x="40" y="70" width="110" height="35" fill="#15803d" rx="2"/>
            <text x="95" y="93" fill="#ffffff" font-family="Arial, sans-serif" font-weight="bold" font-size="14" text-anchor="middle">A4 80g</text>
            <rect x="40" y="105" width="110" height="10" fill="#eab308"/>
            
            <!-- Paquete de Resma Boreal (Adelante) -->
            <g transform="rotate(-3 190 135)">
                <rect x="140" y="60" width="115" height="145" fill="#facc15" stroke="#ca8a04" stroke-width="2" rx="4"/>
                <rect x="140" y="60" width="115" height="40" fill="#166534"/>
                <text x="197" y="86" fill="#ffffff" font-family="Arial, sans-serif" font-weight="bold" font-size="16" text-anchor="middle">A4 80g</text>
                <!-- Logo Boreal / Hoja -->
                <path d="M 180 130 C 180 110 210 110 210 130 C 210 150 180 150 180 130 Z" fill="#15803d"/>
                <text x="197" y="175" fill="#0f172a" font-family="Arial, sans-serif" font-weight="bold" font-size="18" text-anchor="middle">Boreal</text>
                <text x="197" y="192" fill="#334155" font-family="Arial, sans-serif" font-size="9" text-anchor="middle">RESMA DE PAPEL</text>
            </g>
        </svg>
        """
        
    # SVG 2: Lápices, Marcadores y Bolígrafos
    elif any(k in desc for k in ['LAPIZ', 'MARCADOR', 'FIBRA', 'LAPICERA', 'BOLIGRAFO', 'MICROFIBRA']):
        return """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 250" width="100%" height="180">
            <rect width="300" height="250" fill="#f1f5f9" rx="8"/>
            <ellipse cx="150" cy="215" rx="80" ry="10" fill="#cbd5e1"/>
            <!-- Lápiz 1 -->
            <polygon points="90,190 105,190 105,60 90,60" fill="#f59e0b"/>
            <polygon points="90,60 105,60 97,40" fill="#fde047"/>
            <polygon points="95,45 100,45 97,40" fill="#1e293b"/>
            <!-- Lápiz 2 -->
            <polygon points="120,195 135,195 135,50 120,50" fill="#ef4444"/>
            <polygon points="120,50 135,50 127,30" fill="#fde047"/>
            <polygon points="125,35 130,35 127,30" fill="#1e293b"/>
            <!-- Marcador -->
            <rect x="150" y="70" width="22" height="130" fill="#2563eb" rx="3"/>
            <rect x="150" y="45" width="22" height="25" fill="#1e40af" rx="2"/>
        </svg>
        """

    # SVG 3: Cuadernos y Repuestos
    elif any(k in desc for k in ['CUADERNO', 'REPUESTO', 'HOJA', 'LIBRETA', 'BLOCK', 'ANOTADOR']):
        return """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 250" width="100%" height="180">
            <rect width="300" height="250" fill="#f1f5f9" rx="8"/>
            <ellipse cx="150" cy="220" rx="90" ry="10" fill="#cbd5e1"/>
            <rect x="80" y="45" width="140" height="165" fill="#1e3a8a" rx="5"/>
            <rect x="95" y="45" width="125" height="165" fill="#3b82f6" rx="2"/>
            <!-- Espiral -->
            <circle cx="88" cy="65" r="5" fill="#94a3b8"/><circle cx="88" cy="95" r="5" fill="#94a3b8"/>
            <circle cx="88" cy="125" r="5" fill="#94a3b8"/><circle cx="88" cy="155" r="5" fill="#94a3b8"/>
            <circle cx="88" cy="185" r="5" fill="#94a3b8"/>
            <rect x="115" y="80" width="85" height="12" fill="#ffffff" rx="2"/>
            <text x="157" y="125" fill="#ffffff" font-family="Arial" font-weight="bold" font-size="16" text-anchor="middle">CUADERNO</text>
        </svg>
        """

    # SVG 4: Abrochadoras y Oficina
    else:
        return """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 250" width="100%" height="180">
            <rect width="300" height="250" fill="#f1f5f9" rx="8"/>
            <ellipse cx="150" cy="210" rx="80" ry="10" fill="#cbd5e1"/>
            <path d="M 70 180 L 220 180 L 210 160 L 80 160 Z" fill="#475569"/>
            <path d="M 80 155 L 210 155 C 210 120 160 110 120 120 L 80 155 Z" fill="#0f172a"/>
            <rect x="75" y="175" width="150" height="10" fill="#0f172a" rx="2"/>
            <text x="150" y="85" fill="#334155" font-family="Arial" font-weight="bold" font-size="14" text-anchor="middle">ARTÍCULO DE LIBRERÍA</text>
        </svg>
        """

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
            img_col, text_col, action_col = st.columns([1.3, 2.4, 1.3])
            
            with img_col:
                # Renderizado vectorial directo dentro del HTML sin consumo de red
                svg_code = obtener_svg_producto(row['DESCRIPCIO'])
                st.markdown(f"<div class='product-img-box'>{svg_code}</div>", unsafe_allow_html=True)
                
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
