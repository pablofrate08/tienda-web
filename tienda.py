import streamlit as st
import pandas as pd
import requests
import re
import html
import os
import base64
from io import BytesIO
from urllib.parse import quote_plus

# =========================================================
# TIENDA VIRTUAL LKCFRATE
# Catálogo Excel + carrito + imágenes automáticas
# =========================================================

st.set_page_config(
    page_title="LKCFRATE | Tienda Virtual",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CONFIGURACIÓN
# =========================================================

EXCEL_PRINCIPAL = "derivadosll.xlsx"
EXCEL_ANTERIOR = "actualizacionesll.xlsx"

SITE_ID = "MLA"
ML_SEARCH_URL = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"

# Cantidad de productos mostrados por página.
# No conviene cargar miles de tarjetas e imágenes al mismo tiempo.
PRODUCTOS_POR_PAGINA = 24

# Tiempo de caché de las búsquedas de imágenes.
CACHE_IMAGEN_SEGUNDOS = 60 * 60 * 24 * 7

# =========================================================
# ESTILO VISUAL
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            background: linear-gradient(135deg, #0b2d4d 0%, #123f68 100%);
            padding: 28px 30px;
            border-radius: 18px;
            color: white;
            margin-bottom: 22px;
            box-shadow: 0 8px 24px rgba(0,0,0,.10);
        }

        .main-title h1 {
            margin: 0;
            font-size: 2.3rem;
            font-weight: 800;
        }

        .main-title p {
            margin: 7px 0 0 0;
            color: #e8f0f7;
            font-size: 1.03rem;
        }

        .product-name {
            font-size: 1.02rem;
            font-weight: 700;
            line-height: 1.25;
            min-height: 48px;
        }

        .product-code {
            color: #64748b;
            font-size: .82rem;
            margin-top: 5px;
        }

        .product-price {
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 8px;
        }

        .product-image-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 8px;
            min-height: 210px;
        }

        .source-note {
            color: #64748b;
            font-size: .72rem;
            margin-top: 5px;
        }

        .cart-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 18px;
        }

        .total-box {
            background: #0b2d4d;
            color: white;
            padding: 16px;
            border-radius: 12px;
            margin-top: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FUNCIONES GENERALES
# =========================================================

def normalizar_texto(texto):
    """Normaliza texto para comparar nombres de productos."""
    if texto is None:
        return ""

    texto = str(texto).upper().strip()

    # Reemplazos sencillos para mejorar coincidencias.
    reemplazos = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "Ñ": "N",
        "–": "-",
        "—": "-",
    }

    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def tokens_importantes(texto):
    """Devuelve palabras útiles para comparar dos nombres."""
    palabras = normalizar_texto(texto).split()

    # Quitamos palabras demasiado genéricas.
    stopwords = {
        "DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "PARA",
        "CON", "SIN", "X", "UN", "UNA", "COLOR", "COLORES",
        "TAMAÑO", "MEDIDA", "UNIDAD", "UNIDADES", "PZA",
        "PZAS", "PRESENTACION", "PRESENTACION",
    }

    return {
        palabra
        for palabra in palabras
        if len(palabra) >= 3 and palabra not in stopwords
    }


def crear_svg_respaldo(nombre, codigo):
    """
    Crea una imagen individual de respaldo.
    No queda una tarjeta vacía aunque no exista una foto real disponible.
    """
    nombre_limpio = html.escape(str(nombre)[:42])
    codigo_limpio = html.escape(str(codigo)[:24])

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650">
        <rect width="900" height="650" fill="#f8fafc"/>
        <rect x="35" y="35" width="830" height="580" rx="28" fill="#ffffff"
              stroke="#dbe4ee" stroke-width="4"/>

        <rect x="260" y="105" width="380" height="240" rx="22"
              fill="#edf2f7" stroke="#cbd5e1" stroke-width="3"/>

        <circle cx="450" cy="210" r="62" fill="#d7e1ec"/>
        <rect x="354" y="285" width="192" height="22" rx="11" fill="#c5d2df"/>

        <text x="450" y="390"
              text-anchor="middle"
              font-family="Arial, sans-serif"
              font-size="32"
              font-weight="700"
              fill="#0b2d4d">
            Imagen del producto
        </text>

        <text x="450" y="440"
              text-anchor="middle"
              font-family="Arial, sans-serif"
              font-size="25"
              fill="#334155">
            {nombre_limpio}
        </text>

        <text x="450" y="482"
              text-anchor="middle"
              font-family="Arial, sans-serif"
              font-size="19"
              fill="#64748b">
            Código: {codigo_limpio}
        </text>

        <text x="450" y="550"
              text-anchor="middle"
              font-family="Arial, sans-serif"
              font-size="17"
              fill="#94a3b8">
            Foto real pendiente de una fuente pública compatible
        </text>
    </svg>
    """

    return svg


# =========================================================
# BÚSQUEDA AUTOMÁTICA DE IMÁGENES
# =========================================================

@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def buscar_imagen_url(codigo_barra, codigo_articulo, descripcion):
    """
    Busca una imagen individual del producto.

    Prioridad:
    1) Código de barras.
    2) Código de artículo.
    3) Descripción.

    Se consulta Mercado Libre Argentina mediante su buscador público.
    Si no hay una coincidencia razonable, devuelve None.
    """

    codigo_barra = normalizar_texto(codigo_barra)
    codigo_articulo = normalizar_texto(codigo_articulo)
    descripcion_original = str(descripcion or "").strip()

    queries = []

    # El código de barras suele ser el dato más preciso.
    if codigo_barra and len(codigo_barra) >= 6:
        queries.append(("barcode", codigo_barra))

    # Código interno.
    if codigo_articulo:
        queries.append(("codigo", codigo_articulo))

    # Nombre.
    if descripcion_original:
        queries.append(("descripcion", descripcion_original))

    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0 Safari/537.36"
        )
    }

    for tipo_busqueda, query in queries:
        try:
            response = session.get(
                ML_SEARCH_URL,
                params={
                    "q": query,
                    "limit": 8,
                },
                headers=headers,
                timeout=8,
            )

            if response.status_code != 200:
                continue

            data = response.json()
            resultados = data.get("results", [])

            if not resultados:
                continue

            mejor_resultado = None
            mejor_puntaje = -1

            tokens_producto = tokens_importantes(descripcion_original)

            for resultado in resultados:
                titulo = resultado.get("title", "")
                titulo_tokens = tokens_importantes(titulo)

                # Coincidencia por palabras.
                coincidencias = len(tokens_producto & titulo_tokens)

                # Puntaje relativo.
                puntaje = coincidencias * 10

                titulo_normalizado = normalizar_texto(titulo)

                # Prioridad extra para códigos que aparezcan en el título.
                if codigo_barra and codigo_barra in titulo_normalizado:
                    puntaje += 100

                if codigo_articulo and codigo_articulo in titulo_normalizado:
                    puntaje += 50

                # Si la búsqueda fue por código de barras, damos más peso.
                if tipo_busqueda == "barcode":
                    puntaje += 25

                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_resultado = resultado

            if mejor_resultado is None:
                continue

            # Evitamos aceptar cualquier producto totalmente distinto.
            if tipo_busqueda == "descripcion" and mejor_puntaje < 10:
                continue

            # Mercado Libre suele ofrecer thumbnail / secure_thumbnail.
            imagen = (
                mejor_resultado.get("secure_thumbnail")
                or mejor_resultado.get("thumbnail")
            )

            # Si la miniatura no existe, intentamos pictures.
            if not imagen:
                pictures = mejor_resultado.get("pictures", [])
                if pictures:
                    primera = pictures[0]
                    imagen = primera.get("secure_url") or primera.get("url")

            if imagen:
                return imagen

        except (requests.RequestException, ValueError, TypeError):
            continue

    return None


@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def descargar_imagen(imagen_url):
    """
    Descarga la imagen desde el servidor y la entrega como bytes.
    Esto evita depender de que el navegador del cliente pueda hacer hotlink
    directamente al servidor de imágenes.
    """
    if not imagen_url:
        return None

    try:
        response = requests.get(
            imagen_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
                )
            },
            timeout=10,
        )

        if response.status_code != 200:
            return None

        contenido = response.content

        # Seguridad básica: no aceptamos HTML como si fuera una imagen.
        content_type = response.headers.get("content-type", "").lower()

        if (
            "image/" not in content_type
            and not contenido.startswith(b"\xFF\xD8\xFF")   # JPEG
            and not contenido.startswith(b"\x89PNG")        # PNG
            and not contenido.startswith(b"RIFF")           # WEBP posible
        ):
            return None

        return contenido

    except requests.RequestException:
        return None


def obtener_visual_producto(row):
    """
    Devuelve:
    - imagen real encontrada automáticamente, o
    - una imagen individual de respaldo.
    """
    codigo_barra = row.get("COD_BARRA", "")
    codigo_articulo = row.get("COD_ARTICU", "")
    descripcion = row.get("DESCRIPCIO", "")

    imagen_url = buscar_imagen_url(
        codigo_barra=codigo_barra,
        codigo_articulo=codigo_articulo,
        descripcion=descripcion,
    )

    if imagen_url:
        imagen_bytes = descargar_imagen(imagen_url)

        if imagen_bytes:
            return imagen_bytes, True

    return crear_svg_respaldo(descripcion, codigo_articulo), False


# =========================================================
# CARGA DEL EXCEL
# =========================================================

@st.cache_data
def cargar_datos():
    """
    Lee derivadosll.xlsx.
    Si no existe, intenta usar actualizacionesll.xlsx.
    """

    if os.path.exists(EXCEL_PRINCIPAL):
        archivo = EXCEL_PRINCIPAL
    elif os.path.exists(EXCEL_ANTERIOR):
        archivo = EXCEL_ANTERIOR
    else:
        raise FileNotFoundError(
            "No se encontró derivadosll.xlsx ni actualizacionesll.xlsx."
        )

    df = pd.read_excel(archivo)

    # Limpiamos nombres de columnas.
    df.columns = [str(col).strip() for col in df.columns]

    # Columnas obligatorias.
    columnas_posibles = {
        "COD_ARTICU": ["COD_ARTICU", "CODIGO", "CODIGO_ARTICULO"],
        "DESCRIPCIO": ["DESCRIPCIO", "DESCRIPCION", "NOMBRE", "PRODUCTO"],
        "PRECIO": ["PRECIOFINAL", "FINAL", "PRECIO"],
    }

    columnas_encontradas = {}

    for destino, opciones in columnas_posibles.items():
        encontrada = None

        for opcion in opciones:
            if opcion in df.columns:
                encontrada = opcion
                break

        if encontrada is None:
            raise ValueError(
                f"No encontré la columna necesaria para '{destino}'. "
                f"Columnas disponibles: {', '.join(df.columns)}"
            )

        columnas_encontradas[destino] = encontrada

    salida = pd.DataFrame()

    salida["COD_ARTICU"] = (
        df[columnas_encontradas["COD_ARTICU"]]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    salida["DESCRIPCIO"] = (
        df[columnas_encontradas["DESCRIPCIO"]]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    salida["PRECIO"] = pd.to_numeric(
        df[columnas_encontradas["PRECIO"]],
        errors="coerce",
    )

    # Intentamos conservar el código de barras si existe.
    columna_barra = None

    for opcion in [
        "COD_BARRA",
        "COD_BARRAS",
        "CODIGO_BARRA",
        "CODIGO_BARRAS",
        "EAN",
        "GTIN",
    ]:
        if opcion in df.columns:
            columna_barra = opcion
            break

    if columna_barra:
        salida["COD_BARRA"] = (
            df[columna_barra]
            .fillna("")
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )
    else:
        salida["COD_BARRA"] = ""

    # Quitamos filas que no tengan nombre o precio válido.
    salida = salida[
        (salida["DESCRIPCIO"].str.strip() != "")
        & salida["PRECIO"].notna()
    ].copy()

    salida["PRECIO"] = salida["PRECIO"].round(2)

    # Identificador estable para los widgets.
    salida = salida.reset_index(drop=True)
    salida["ROW_ID"] = salida.index.astype(str)

    return salida


# =========================================================
# CARGA DE PRODUCTOS
# =========================================================

try:
    df = cargar_datos()

except Exception as error:
    st.error(f"❌ No se pudo cargar el catálogo: {error}")
    st.stop()


# =========================================================
# CARRITO
# =========================================================

if "carrito" not in st.session_state:
    st.session_state.carrito = []


def agregar_al_carrito(row, cantidad):
    """Agrega o acumula un producto en el carrito."""
    codigo = str(row["COD_ARTICU"])
    nombre = str(row["DESCRIPCIO"])
    precio = float(row["PRECIO"])

    # Si ya existe, acumulamos cantidad.
    for item in st.session_state.carrito:
        if item["codigo"] == codigo:
            item["cantidad"] += int(cantidad)
            item["subtotal"] = item["precio"] * item["cantidad"]
            return

    st.session_state.carrito.append(
        {
            "codigo": codigo,
            "nombre": nombre,
            "precio": precio,
            "cantidad": int(cantidad),
            "subtotal": precio * int(cantidad),
        }
    )


def quitar_producto(indice):
    if 0 <= indice < len(st.session_state.carrito):
        st.session_state.carrito.pop(indice)


def calcular_total():
    return sum(
        float(item["subtotal"])
        for item in st.session_state.carrito
    )


# =========================================================
# ENCABEZADO
# =========================================================

st.markdown(
    """
    <div class="main-title">
        <h1>🛒 LKCFRATE</h1>
        <p>Tienda virtual · Librería · Escolar · Comercial</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Catálogo activo: **{len(df):,} artículos**"
    .replace(",", ".")
)


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:
    st.header("⚙️ Catálogo")

    st.write(
        "La tienda busca automáticamente una imagen individual "
        "para cada artículo cuando el producto aparece en pantalla."
    )

    st.divider()

    st.subheader("🔎 Información")

    if "COD_BARRA" in df.columns:
        cantidad_con_barra = (
            df["COD_BARRA"].astype(str).str.strip().ne("").sum()
        )
        st.metric(
            "Productos con código de barras",
            f"{cantidad_con_barra:,}".replace(",", "."),
        )

    st.divider()

    st.subheader("📦 Visualización")

    productos_por_pagina = st.selectbox(
        "Productos por página",
        [12, 24, 36, 48],
        index=1,
    )

    st.caption(
        "La paginación evita cargar miles de imágenes simultáneamente."
    )

    st.divider()

    st.subheader("ℹ️ Imágenes")

    st.info(
        "Primero se intenta encontrar la foto del producto. "
        "Si la fuente no tiene una coincidencia, se muestra una "
        "imagen individual de respaldo con el nombre y código del artículo."
    )


# =========================================================
# FILTRO / BUSCADOR
# =========================================================

col_busqueda, col_orden = st.columns([3, 1])

with col_busqueda:
    busqueda = st.text_input(
        "🔎 Buscar producto",
        placeholder=(
            "Ej.: lápiz, tempera, cuaderno, abrochadora, "
            "código o código de barras..."
        ),
    ).strip()

with col_orden:
    orden = st.selectbox(
        "Ordenar",
        [
            "Predeterminado",
            "Nombre A → Z",
            "Nombre Z → A",
            "Precio menor → mayor",
            "Precio mayor → menor",
        ],
    )


# =========================================================
# FILTRADO
# =========================================================

resultados = df.copy()

if busqueda:
    termino = normalizar_texto(busqueda)

    mascara = (
        resultados["COD_ARTICU"]
        .astype(str)
        .map(normalizar_texto)
        .str.contains(termino, regex=False, na=False)
        |
        resultados["DESCRIPCIO"]
        .astype(str)
        .map(normalizar_texto)
        .str.contains(termino, regex=False, na=False)
        |
        resultados["COD_BARRA"]
        .astype(str)
        .map(normalizar_texto)
        .str.contains(termino, regex=False, na=False)
    )

    resultados = resultados[mascara].copy()


if orden == "Nombre A → Z":
    resultados = resultados.sort_values("DESCRIPCIO", ascending=True)

elif orden == "Nombre Z → A":
    resultados = resultados.sort_values("DESCRIPCIO", ascending=False)

elif orden == "Precio menor → mayor":
    resultados = resultados.sort_values("PRECIO", ascending=True)

elif orden == "Precio mayor → menor":
    resultados = resultados.sort_values("PRECIO", ascending=False)


# =========================================================
# CONTADOR
# =========================================================

st.markdown(
    f"**{len(resultados):,} productos encontrados**"
    .replace(",", ".")
)

st.divider()


# =========================================================
# CARRITO
# =========================================================

def mostrar_carrito():
    with st.container():
        st.markdown(
            "<div class='cart-box'>",
            unsafe_allow_html=True,
        )

        st.subheader("🛒 Tu carrito")

        if not st.session_state.carrito:
            st.info("Todavía no agregaste productos.")
        else:
            total = 0.0

            for i, item in enumerate(st.session_state.carrito):
                c1, c2 = st.columns([4, 1])

                with c1:
                    st.markdown(
                        f"**{item['cantidad']} × {item['nombre']}**"
                    )
                    st.caption(
                        f"Código: {item['codigo']} · "
                        f"Subtotal: ${item['subtotal']:,.2f}"
                    )

                with c2:
                    if st.button(
                        "❌",
                        key=f"remove_cart_{i}",
                        help="Quitar del carrito",
                    ):
                        quitar_producto(i)
                        st.rerun()

                total += item["subtotal"]

            st.markdown(
                f"""
                <div class="total-box">
                    <div style="font-size:.9rem;">TOTAL</div>
                    <div style="font-size:1.55rem;font-weight:800;">
                        ${total:,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            if st.button(
                "🗑️ Vaciar carrito",
                use_container_width=True,
            ):
                st.session_state.carrito = []
                st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# PAGINACIÓN
# =========================================================

cantidad_resultados = len(resultados)

if cantidad_resultados == 0:
    st.warning(
        "No encontramos productos con ese criterio de búsqueda."
    )

else:
    total_paginas = max(
        1,
        (cantidad_resultados + productos_por_pagina - 1)
        // productos_por_pagina,
    )

    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = 1

    # Si cambia la búsqueda, evitamos quedar en una página inexistente.
    if st.session_state.pagina_actual > total_paginas:
        st.session_state.pagina_actual = 1

    pagina_actual = st.session_state.pagina_actual

    inicio = (pagina_actual - 1) * productos_por_pagina
    fin = inicio + productos_por_pagina

    pagina_df = resultados.iloc[inicio:fin].copy()

    # -----------------------------------------------------
    # PRODUCTOS
    # -----------------------------------------------------

    col_catalogo, col_carrito = st.columns([2.7, 1])

    with col_catalogo:

        # Tres columnas tipo tienda online.
        columnas = st.columns(3)

        for posicion, (_, row) in enumerate(pagina_df.iterrows()):
            columna = columnas[posicion % 3]

            with columna:
                with st.container(border=True):

                    # IMAGEN
                    imagen, es_real = obtener_visual_producto(row)

                    st.markdown(
                        "<div class='product-image-box'>",
                        unsafe_allow_html=True,
                    )

                    st.image(
                        imagen,
                        width="stretch",
                    )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True,
                    )

                    if es_real:
                        st.markdown(
                            "<div class='source-note'>"
                            "🖼️ Imagen encontrada automáticamente"
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div class='source-note'>"
                            "📌 Imagen de respaldo"
                            "</div>",
                            unsafe_allow_html=True,
                        )

                    # NOMBRE
                    nombre = str(row["DESCRIPCIO"])
                    codigo = str(row["COD_ARTICU"])

                    st.markdown(
                        f"""
                        <div class="product-name">
                            {html.escape(nombre)}
                        </div>
                        <div class="product-code">
                            Código: {html.escape(codigo)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # BARRA
                    codigo_barra = str(row.get("COD_BARRA", "")).strip()

                    if codigo_barra:
                        st.caption(
                            f"EAN/Código de barras: {codigo_barra}"
                        )

                    # PRECIO
                    precio = float(row["PRECIO"])

                    st.markdown(
                        f"""
                        <div class="product-price">
                            ${precio:,.2f}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    cantidad = st.number_input(
                        "Cantidad",
                        min_value=1,
                        max_value=999,
                        value=1,
                        step=1,
                        key=f"qty_{row['ROW_ID']}",
                    )

                    if st.button(
                        "🛒 Agregar al carrito",
                        key=f"add_{row['ROW_ID']}",
                        use_container_width=True,
                    ):
                        agregar_al_carrito(row, cantidad)

                        st.toast(
                            f"Agregado: {nombre}",
                            icon="✅",
                        )

                        st.rerun()

    # -----------------------------------------------------
    # CARRITO
    # -----------------------------------------------------

    with col_carrito:
        mostrar_carrito()

        st.divider()

        st.subheader("💳 Finalizar compra")

        total_actual = calcular_total()

        if total_actual > 0:

            metodo = st.radio(
                "Forma de pago",
                [
                    "Mercado Pago",
                    "Transferencia / Efectivo",
                ],
                key="metodo_pago",
            )

            # Pedimos datos de cliente.
            nombre_cliente = st.text_input(
                "Nombre",
                key="cliente_nombre",
            )

            telefono_cliente = st.text_input(
                "WhatsApp",
                key="cliente_telefono",
            )

            observaciones = st.text_area(
                "Observaciones del pedido",
                key="cliente_observaciones",
                placeholder="Ej.: retiro por el local, envío, etc.",
            )

            # Armado del pedido.
            resumen = [
                "NUEVO PEDIDO - LKCFRATE",
                "",
            ]

            for item in st.session_state.carrito:
                resumen.append(
                    f"{item['cantidad']} x "
                    f"{item['nombre']} "
                    f"(Código {item['codigo']}) "
                    f"- ${item['subtotal']:,.2f}"
                )

            resumen.extend(
                [
                    "",
                    f"TOTAL: ${total_actual:,.2f}",
                    f"Cliente: {nombre_cliente}",
                    f"WhatsApp: {telefono_cliente}",
                    f"Método: {metodo}",
                    f"Observaciones: {observaciones}",
                ]
            )

            resumen_texto = "\n".join(resumen)

            if metodo == "Mercado Pago":
                # -------------------------------------------------
                # REEMPLAZAR POR TU LINK REAL
                # -------------------------------------------------
                LINK_MERCADO_PAGO = (
                    "https://link.mercadopago.com.ar/TULINKAQUI"
                )

                st.link_button(
                    "💳 Pagar con Mercado Pago",
                    LINK_MERCADO_PAGO,
                    use_container_width=True,
                )

                st.caption(
                    "Pegá tu Link de Pago real de Mercado Pago "
                    "en LINK_MERCADO_PAGO."
                )

            # -----------------------------------------------------
            # WHATSAPP
            # -----------------------------------------------------

            NUMERO_WHATSAPP = "549343XXXXXXX"

            url_whatsapp = (
                "https://wa.me/"
                + NUMERO_WHATSAPP
                + "?text="
                + quote_plus(resumen_texto)
            )

            st.link_button(
                "📲 Enviar pedido por WhatsApp",
                url_whatsapp,
                use_container_width=True,
            )

        else:
            st.info(
                "Agregá productos al carrito para continuar."
            )


    # -----------------------------------------------------
    # PAGINADOR
    # -----------------------------------------------------

    st.divider()

    p1, p2, p3 = st.columns([1, 2, 1])

    with p1:
        if st.button(
            "⬅️ Anterior",
            disabled=(pagina_actual <= 1),
            use_container_width=True,
        ):
            st.session_state.pagina_actual -= 1
            st.rerun()

    with p2:
        st.markdown(
            f"""
            <div style="text-align:center;padding-top:8px;">
                Página <b>{pagina_actual}</b> de <b>{total_paginas}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p3:
        if st.button(
            "Siguiente ➡️",
            disabled=(pagina_actual >= total_paginas),
            use_container_width=True,
        ):
            st.session_state.pagina_actual += 1
            st.rerun()


# =========================================================
# PIE DE PÁGINA
# =========================================================

st.divider()

st.caption(
    "LKCFRATE · Catálogo online · Las imágenes se obtienen automáticamente "
    "cuando existe una coincidencia pública compatible."
)
