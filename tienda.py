import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Tienda Lkcfrate", page_icon="🛒", layout="wide")

@st.cache_data
def cargar_datos():
    archivo = 'actualizacionesll.xlsx'
    if not os.path.exists(archivo):
        archivo = 'actualizacionesll.xlsx.xlsx'
    
    df = pd.read_excel(archivo)
    df_limpio = df[['COD_ARTICU', 'DESCRIPCIO', 'FINAL']].dropna().copy()
    df_limpio['COD_ARTICU'] = df_limpio['COD_ARTICU'].astype(str).str.strip()
    df_limpio['DESCRIPCIO'] = df_limpio['DESCRIPCIO'].astype(str).str.strip()
    df_limpio['FINAL'] = df_limpio['FINAL'].astype(float).round(2)
    return df_limpio

# Cargar catálogo
try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error al cargar el Excel: {e}. Recordá subir el archivo 'actualizacionesll.xlsx' a GitHub.")
    st.stop()

# Inicializar carrito en la sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Título Principal
st.title("🛒 Tienda Virtual Lkcfrate")
st.caption(f"Catálogo activo con {len(df)} artículos disponibles")

# Diseño en 2 columnas: Izquierda (Buscador/Productos) - Derecha (Carrito/Checkout)
col_tienda, col_carrito = st.columns([2, 1])

with col_tienda:
    st.subheader("🔍 Buscar Productos")
    busqueda = st.text_input("Ingresá código o nombre (ej: 25247, PA, tempera):", "").upper().strip()

    if busqueda:
        # Filtrar entre los 864 productos
        resultados = df[
            df['COD_ARTICU'].str.upper().str.contains(busqueda) | 
            df['DESCRIPCIO'].str.upper().str.contains(busqueda)
        ]
    else:
        resultados = df.head(20) # Muestra los primeros 20 si no busca nada

    st.write(f"Mostrando **{len(resultados)}** resultados:")

    # Mostrar productos en tarjetas interactivas
    for idx, row in resultados.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{row['DESCRIPCIO']}**  \n`Cód: {row['COD_ARTICU']}`")
            c2.markdown(f"### ${row['FINAL']:,.2f}")
            cant = c3.number_input("Cant:", min_value=1, value=1, key=f"cant_{idx}")
            if c3.button("Agregar ➕", key=f"btn_{idx}"):
                st.session_state.carrito.append({
                    "nombre": row['DESCRIPCIO'],
                    "precio": row['FINAL'],
                    "cantidad": cant,
                    "subtotal": row['FINAL'] * cant
                })
                st.toast(f"¡Agregado: {row['DESCRIPCIO']}!", icon="✅")

with col_carrito:
    st.subheader("🛍️ Tu Carrito de Compras")

    if not st.session_state.carrito:
        st.info("El carrito está vacío.")
    else:
        total_bruto = 0
        for item in st.session_state.carrito:
            st.write(f"• **{item['cantidad']}x** {item['nombre']} — **${item['subtotal']:,.2f}**")
            total_bruto += item['subtotal']
        
        st.divider()
        st.markdown(f"#### Subtotal: **${total_bruto:,.2f}**")

        if st.button("Vaciar Carrito 🗑️"):
            st.session_state.carrito = []
            st.rerun()

        st.divider()
        st.subheader("💳 Métodos de Pago")
        metodo = st.radio("Seleccioná la forma de pago:", ["Efectivo (5% Desc.)", "Tarjeta de Crédito", "Mercado Pago"])

        descuento = total_bruto * 0.05 if "Efectivo" in metodo else 0
        subtotal_desc = total_bruto - descuento
        iva = subtotal_desc * 0.19
        total_final = subtotal_desc + iva

        st.write(f"Descuento: **-${descuento:,.2f}**")
        st.write(f"IVA (19%): **+${iva:,.2f}**")
        st.markdown(f"### **Total Final: ${total_final:,.2f}**")

        if st.button("Finalizar Compra 🎉", type="primary"):
            st.balloons()
            st.success("¡Compra realizada con éxito! Gracias por elegirnos.")
            st.session_state.carrito = []
