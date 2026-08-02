import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Tienda LKCFRATE", page_icon="🛍️")

# Título principal visual
st.title("🛒 BIENVENIDO A LA TIENDA LKCFRATE")
st.write("Catálogo interactivo de productos")

# Datos de tu tienda (podés cambiar los nombres y precios)
datos = {
    "CÓDIGO": ["P01", "P02", "P03", "P04"],
    "NOMBRE": ["Remera Oversize", "Pantalón Cargo", "Buzo Hoodie", "Zapatillas Urban"],
    "PRECIO": [15000, 28000, 35000, 42000],
    "STOCK": [10, 5, 8, 4]
}
df = pd.DataFrame(datos)

# Buscador WEB (Esto reemplaza al input() que trababa todo)
st.header("🔍 Buscar Productos")
busqueda = st.text_input("Ingrese CÓDIGO o NOMBRE (o escriba 'TODOS'):", value="TODOS")

# Mostrar resultados
if busqueda:
    if busqueda.upper() == "TODOS" or busqueda.strip() == "":
        st.success("¡Catálogo cargado al 100%! Mostrando productos:")
        st.dataframe(df, use_container_width=True)
    else:
        resultado = df[df["NOMBRE"].str.contains(busqueda, case=False) | (df["CÓDIGO"].str.upper() == busqueda.upper())]
        if not resultado.empty:
            st.write("Resultados encontrados:")
            st.dataframe(resultado, use_container_width=True)
        else:
            st.warning("No se encontraron productos con ese nombre o código.")
