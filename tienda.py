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
# 2. Mapeo de Fotos Reales de Productos (Fondo Blanco)
# ---------------------------------------------------------
def obtener_imagen_producto_real(descripcion):
    desc = str(descripcion).upper()
    
    # Foto real de Resma Boreal A4/Oficio con caja y paquete amarillo/verde
    if any(k in desc for k in ['BOREAL', 'RESMA', 'AUTOR', 'PUNTO 80', 'A4', 'OFICIO', 'DISCIPLINA']):
        return "https://http2.mlstatic.com/D_NQ_NP_900037-MLA47738243171_102021-O.webp"
    
    # Témperas y Pinturas
    elif any(k in desc for k in ['TEMPERA', 'PINTURA', 'ACRILICO', 'PINCEL', 'ACUARELA', 'PIGMENTOS']):
        return "https://http2.mlstatic.com/D_NQ_NP_983198-MLA43285750242_082020-O.webp"
    
    # Lápices, Marcadores y Bolígrafos
    elif any(k in desc for k in ['LAPIZ', 'MARCADOR', 'FIBRA', 'LAPICERA', 'BOLIGRAFO', 'MICROFIBRA', 'FABER', 'SIMBALL']):
        return "https://http2.mlstatic.com/D_NQ_NP_753235-MLA44083818961_112020-O.webp"
    
    # Cuadernos, Repuestos y Hojas
    elif any(k in desc for k in ['CUADERNO', 'REPUESTO', 'HOJA', 'LIBRETA', 'BLOCK', 'ANOTADOR', 'RIVADAVIA', 'SUCCESS', 'GLORIA']):
        return "https://http2.mlstatic.com/D_NQ_NP_888126-MLA43743849132_102020-O.webp"
    
    # Mochilas y Cartucheras
    elif any(k in desc for k in ['MOCHILA', 'CARTUCHERA', 'CARPETA', 'MALETIN']):
        return "https://http2.mlstatic.com/D_NQ_NP_602334-MLA45305953041_032021-O.webp"
    
    # Ábacos y Juegos Didácticos
    elif any(k in desc for k in ['ABACO', 'JUEGO', 'DIDACTICO', 'JUGUETE', 'PUZZLE', 'GEOMETRIA']):
        return "https://http2.mlstatic.com/D_NQ_NP_833618-MLA43542283921_092020-O.webp"
    
    # Artículos de Oficina y Abrochadoras
    elif any(k in desc for k in ['ABROCHADORA', 'CORRECTOR', 'TIJERA', 'REGLA', 'CINTA', 'BROCHE', 'PERFORADORA', 'CLIP', 'CUTER', 'INVICTA']):
        return "https://http2.mlstatic.com/D_NQ_NP_843513-MLA43743841120_102020-O.webp"
    
    else:
        return "https://http2.mlstatic.com/D_NQ_NP_900037-MLA47738243171_102021-O.webp"

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
    
    # Asignación de imagen de producto real
    df_limpio['IMAGEN_URL'] = df_limpio['DESCRIPCIO'].apply(obtener_imagen_producto_real)
    
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
