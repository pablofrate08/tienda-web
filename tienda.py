import streamlit as st
import pandas as pd
import requests
import re
import html
import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

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


def crear_imagen_respaldo(nombre, codigo):
    """
    Crea una imagen PNG REAL en memoria para usar como respaldo.

    Es importante que sea PNG y no un texto SVG, porque Streamlit puede
    interpretar un string SVG como una ruta/URL y provocar FileNotFoundError.
    """
    ancho, alto = 900, 650

    imagen = Image.new("RGB", (ancho, alto), "#f8fafc")
    dibujo = ImageDraw.Draw(imagen)

    # Fuentes por defecto: no dependemos de archivos externos.
    fuente_grande = ImageFont.load_default(size=32)
    fuente_media = ImageFont.load_default(size=24)
    fuente_chica = ImageFont.load_default(size=18)

    # Marco principal.
    dibujo.rounded_rectangle(
        (35, 35, ancho - 35, alto - 35),
        radius=28,
        fill="#ffffff",
        outline="#dbe4ee",
        width=4,
    )

    # Ilustración neutra del artículo.
    dibujo.rounded_rectangle(
        (260, 105, 640, 345),
        radius=22,
        fill="#edf2f7",
        outline="#cbd5e1",
        width=3,
    )
    dibujo.ellipse(
        (388, 148, 512, 272),
        fill="#d7e1ec",
    )
    dibujo.rounded_rectangle(
        (354, 285, 546, 307),
        radius=11,
        fill="#c5d2df",
    )

    # Texto.
    titulo = "Imagen del producto"
    bbox = dibujo.textbbox((0, 0), titulo, font=fuente_grande)
    dibujo.text(
        ((ancho - (bbox[2] - bbox[0])) / 2, 390),
        titulo,
        fill="#0b2d4d",
        font=fuente_grande,
    )

    nombre = str(nombre or "Producto")[:52]
    bbox = dibujo.textbbox((0, 0), nombre, font=fuente_media)
    dibujo.text(
        ((ancho - (bbox[2] - bbox[0])) / 2, 440),
        nombre,
        fill="#334155",
        font=fuente_media,
    )

    codigo = str(codigo or "-")[:28]
    etiqueta = f"Código: {codigo}"
    bbox = dibujo.textbbox((0, 0), etiqueta, font=fuente_chica)
    dibujo.text(
        ((ancho - (bbox[2] - bbox[0])) / 2, 485),
        etiqueta,
        fill="#64748b",
        font=fuente_chica,
    )

    pie = "No se encontró una foto pública compatible"
    bbox = dibujo.textbbox((0, 0), pie, font=fuente_chica)
    dibujo.text(
        ((ancho - (bbox[2] - bbox[0])) / 2, 550),
        pie,
        fill="#94a3b8",
        font=fuente_chica,
    )

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


# =========================================================
# PRECIOS
# =========================================================

def precio_valido(valor):
    """Indica si el precio puede usarse para una operación de compra."""
    return pd.notna(valor) and isinstance(valor, (int, float)) and not pd.isna(valor)


def texto_precio(valor):
    """Muestra el precio sin romper si el Excel trae un valor vacío."""
    if not precio_valido(valor):
        return "Consultar precio"
    return f"${float(valor):,.2f}"


# =========================================================
# BÚSQUEDA AUTOMÁTICA DE IMÁGENES
# =========================================================

HEADERS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}


def limpiar_consulta(texto):
    """Convierte un texto de producto en una consulta limpia."""
    texto = str(texto or "").strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto[:180]


def consultas_producto(codigo_barra, codigo_articulo, descripcion):
    """
    Genera consultas en orden de precisión.

    Primero usamos el código de barras, porque es el identificador
    más preciso. Luego combinamos código + descripción y finalmente
    la descripción sola.
    """
    barra = str(codigo_barra or "").strip()
    codigo = str(codigo_articulo or "").strip()
    desc = limpiar_consulta(descripcion)

    consultas = []

    if barra and len(re.sub(r"\D", "", barra)) >= 6:
        numero_barra = re.sub(r"\D", "", barra)
        consultas.append(f'"{numero_barra}"')

    if codigo and desc:
        consultas.append(f'"{codigo}" "{desc}"')

    if desc:
        consultas.append(f'"{desc}"')

    # Quitamos duplicados preservando el orden.
    resultado = []
    vistos = set()

    for consulta in consultas:
        if consulta not in vistos:
            vistos.add(consulta)
            resultado.append(consulta)

    return resultado


@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def buscar_imagen_ddg(consulta):
    """
    Busca imágenes usando la búsqueda de imágenes pública de DuckDuckGo.

    No necesita una clave API.
    Devuelve una lista pequeña de candidatos con:
      - imagen real
      - miniatura
      - título
      - página de origen
    """

    consulta = limpiar_consulta(consulta)

    if not consulta:
        return []

    try:
        session = requests.Session()

        # Primera petición para obtener el token VQD.
        pagina = session.get(
            "https://duckduckgo.com/",
            params={
                "q": consulta,
                "ia": "images",
                "iax": "images",
            },
            headers=HEADERS_NAVEGADOR,
            timeout=10,
        )

        if pagina.status_code != 200:
            return []

        texto = pagina.text

        patrones_vqd = [
            r"vqd='([^']+)'",
            r'vqd="([^"]+)"',
            r'"vqd":"([^"]+)"',
            r"vqd=([\d-]+)",
        ]

        vqd = None

        for patron in patrones_vqd:
            coincidencia = re.search(patron, texto)

            if coincidencia:
                vqd = coincidencia.group(1)
                break

        if not vqd:
            return []

        # Segunda petición: resultados de imágenes.
        respuesta = session.get(
            "https://duckduckgo.com/i.js",
            params={
                "l": "ar-es",
                "o": "json",
                "q": consulta,
                "vqd": vqd,
                "f": ",,,",
                "p": "1",
            },
            headers={
                **HEADERS_NAVEGADOR,
                "Referer": "https://duckduckgo.com/",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=12,
        )

        if respuesta.status_code != 200:
            return []

        datos = respuesta.json()
        candidatos = datos.get("results", [])

        resultado = []

        for candidato in candidatos[:12]:
            resultado.append(
                {
                    "image": candidato.get("image"),
                    "thumbnail": candidato.get("thumbnail"),
                    "title": candidato.get("title", ""),
                    "url": candidato.get("url", ""),
                    "width": candidato.get("width"),
                    "height": candidato.get("height"),
                }
            )

        return resultado

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        AttributeError,
    ):
        return []


@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def buscar_og_image_en_web(consulta):
    """
    Segunda vía de recuperación:
    busca páginas web relacionadas y extrae og:image/twitter:image.

    Esto es especialmente útil cuando el código de barras lleva a una ficha
    de producto de una librería/mayorista y esa página tiene la imagen del
    artículo en sus metadatos.
    """

    consulta = limpiar_consulta(consulta)

    if not consulta:
        return None

    try:
        session = requests.Session()

        respuesta = session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": consulta},
            headers=HEADERS_NAVEGADOR,
            timeout=10,
        )

        if respuesta.status_code != 200:
            return None

        soup = BeautifulSoup(respuesta.text, "html.parser")

        enlaces = []

        for enlace in soup.select("a.result__a"):
            href = enlace.get("href")

            if href and href.startswith("http"):
                enlaces.append(href)

        # Evitamos demasiadas descargas por producto.
        for enlace in enlaces[:4]:
            try:
                pagina = session.get(
                    enlace,
                    headers=HEADERS_NAVEGADOR,
                    timeout=8,
                    allow_redirects=True,
                )

                if pagina.status_code != 200:
                    continue

                soup_pagina = BeautifulSoup(
                    pagina.text,
                    "html.parser",
                )

                # Prioridad 1: Open Graph.
                for selector in [
                    ("meta", {"property": "og:image"}),
                    ("meta", {"property": "og:image:url"}),
                    ("meta", {"name": "twitter:image"}),
                    ("meta", {"name": "twitter:image:src"}),
                ]:
                    meta = soup_pagina.find(*selector)

                    if meta and meta.get("content"):
                        imagen = meta["content"].strip()

                        if imagen.startswith("http"):
                            return imagen

                # Prioridad 2: JSON-LD con campo image.
                for script in soup_pagina.find_all(
                    "script",
                    type="application/ld+json",
                ):
                    try:
                        import json

                        datos = json.loads(script.string or script.get_text())

                        objetos = datos if isinstance(datos, list) else [datos]

                        for obj in objetos:
                            if not isinstance(obj, dict):
                                continue

                            imagen = obj.get("image")

                            if isinstance(imagen, str):
                                if imagen.startswith("http"):
                                    return imagen

                            if isinstance(imagen, list):
                                for elemento in imagen:
                                    if (
                                        isinstance(elemento, str)
                                        and elemento.startswith("http")
                                    ):
                                        return elemento

                    except (
                        ValueError,
                        TypeError,
                        json.JSONDecodeError,
                    ):
                        continue

            except requests.RequestException:
                continue

    except requests.RequestException:
        return None

    return None


def puntuar_candidato(candidato, descripcion, codigo_barra, codigo_articulo):
    """
    Puntúa una imagen por coincidencia del título y la consulta.
    """
    titulo = normalizar_texto(candidato.get("title", ""))
    desc_tokens = tokens_importantes(descripcion)

    coincidencias = len(desc_tokens & set(titulo.split()))
    puntaje = coincidencias * 10

    titulo_sin_simbolos = re.sub(r"\D", "", titulo)
    barra_limpia = re.sub(r"\D", "", str(codigo_barra or ""))
    codigo_limpio = normalizar_texto(codigo_articulo)

    if barra_limpia and len(barra_limpia) >= 6:
        if barra_limpia in titulo_sin_simbolos:
            puntaje += 100

    if codigo_limpio and codigo_limpio in titulo:
        puntaje += 40

    return puntaje


@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def buscar_imagen_url(codigo_barra, codigo_articulo, descripcion):
    """
    Busca una imagen individual del producto.

    Orden:
    1. Búsqueda por código de barras.
    2. Búsqueda por código + descripción.
    3. Búsqueda por descripción.
    4. Recuperación de og:image desde una ficha de producto encontrada.
    """

    consultas = consultas_producto(
        codigo_barra,
        codigo_articulo,
        descripcion,
    )

    # -----------------------------------------------------
    # VÍA 1: búsqueda de imágenes
    # -----------------------------------------------------

    for indice, consulta in enumerate(consultas):
        candidatos = buscar_imagen_ddg(consulta)

        if not candidatos:
            continue

        candidatos_ordenados = sorted(
            candidatos,
            key=lambda candidato: puntuar_candidato(
                candidato,
                descripcion,
                codigo_barra,
                codigo_articulo,
            ),
            reverse=True,
        )

        for candidato in candidatos_ordenados[:5]:
            # Primero la imagen original; luego la miniatura.
            imagen = (
                candidato.get("image")
                or candidato.get("thumbnail")
            )

            if imagen and imagen.startswith("http"):
                return imagen

        # Para el código de barras, si hubo resultados, confiamos especialmente
        # en el primer grupo porque la consulta ya era muy específica.
        if indice == 0 and candidatos_ordenados:
            imagen = (
                candidatos_ordenados[0].get("image")
                or candidatos_ordenados[0].get("thumbnail")
            )

            if imagen and imagen.startswith("http"):
                return imagen

    # -----------------------------------------------------
    # VÍA 2: ficha de producto con og:image
    # -----------------------------------------------------

    for consulta in consultas[:2]:
        imagen = buscar_og_image_en_web(consulta)

        if imagen:
            return imagen

    return None


@st.cache_data(ttl=CACHE_IMAGEN_SEGUNDOS, show_spinner=False)
def descargar_imagen(imagen_url):
    """
    Descarga la imagen y la entrega como bytes para que Streamlit la muestre
    directamente. Intentamos también una segunda vez sin Referer.
    """

    if not imagen_url:
        return None

    encabezados = [
        HEADERS_NAVEGADOR,
        {
            "User-Agent": HEADERS_NAVEGADOR["User-Agent"],
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    ]

    for headers in encabezados:
        try:
            response = requests.get(
                imagen_url,
                headers=headers,
                timeout=12,
                allow_redirects=True,
            )

            if response.status_code != 200:
                continue

            contenido = response.content

            content_type = (
                response.headers.get("content-type", "")
                .lower()
            )

            firma_imagen = (
                contenido.startswith(b"\xFF\xD8\xFF")   # JPEG
                or contenido.startswith(b"\x89PNG")     # PNG
                or contenido.startswith(b"RIFF")        # WEBP
                or contenido.startswith(b"GIF8")        # GIF
                or contenido.startswith(b"<svg")       # SVG
            )

            if "image/" in content_type or firma_imagen:
                return contenido

        except requests.RequestException:
            continue

    return None


def obtener_visual_producto(row):
    """
    Devuelve:
    - imagen real encontrada en la web, o
    - imagen PNG de respaldo.
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

    return crear_imagen_respaldo(
        descripcion,
        codigo_articulo,
    ), False



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

    # IMPORTANTE:
    # No eliminamos filas por tener nombre o precio vacío.
    # De esta manera el catálogo conserva TODAS las filas del Excel.
    # Un precio vacío se mostrará como "Consultar precio".
    salida["PRECIO"] = pd.to_numeric(salida["PRECIO"], errors="coerce").round(2)

    salida["DESCRIPCIO"] = salida["DESCRIPCIO"].replace("", "Producto sin descripción")
    salida["COD_ARTICU"] = salida["COD_ARTICU"].replace("", "-")

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

    if not precio_valido(row["PRECIO"]):
        return False

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

    return True


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
    + " · Se conservan todas las filas cargadas desde el Excel."
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
    resultados = resultados.sort_values(
        "PRECIO", ascending=True, na_position="last"
    )

elif orden == "Precio mayor → menor":
    resultados = resultados.sort_values(
        "PRECIO", ascending=False, na_position="last"
    )


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
                    # Mostramos UNA sola imagen directamente.
                    # No usamos un <div> HTML separado porque Streamlit
                    # renderiza st.image como un bloque independiente.
                    imagen, es_real = obtener_visual_producto(row)

                    st.image(
                        imagen,
                        width="stretch",
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
                    precio = row["PRECIO"]

                    st.markdown(
                        f"""
                        <div class="product-price">
                            {html.escape(texto_precio(precio))}
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
                        disabled=not precio_valido(precio),
                    )

                    if not precio_valido(precio):
                        st.warning(
                            "Este artículo no tiene un precio válido en el Excel."
                        )

                    if st.button(
                        "🛒 Agregar al carrito",
                        key=f"add_{row['ROW_ID']}",
                        use_container_width=True,
                        disabled=not precio_valido(precio),
                    ):
                        agregado = agregar_al_carrito(row, cantidad)

                        if agregado:
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
