import pandas as pd
import os

def cargar_catalogo():
    archivo_excel = 'actualizacionesll.xlsx.xlsx'
    
    if not os.path.exists(archivo_excel):
        archivo_excel = 'actualizacionesll.xlsx'

    try:
        # Carga los 864 productos enteros
        df = pd.read_excel(archivo_excel)
        df_limpio = df[['COD_ARTICU', 'DESCRIPCIO', 'FINAL']].dropna().copy()
        
        # Formatear columnas
        df_limpio['COD_ARTICU'] = df_limpio['COD_ARTICU'].astype(str).str.strip()
        df_limpio['DESCRIPCIO'] = df_limpio['DESCRIPCIO'].astype(str).str.strip()
        df_limpio['FINAL'] = df_limpio['FINAL'].astype(float).round(2)
        
        return df_limpio
    except Exception as e:
        print(f"❌ Error al cargar el Excel: {e}")
        return None

def sistema_tienda():
    df = cargar_catalogo()
    if df is None:
        return

    print(f"\n✓ ¡Catálogo cargado al 100%! Se cargaron los {len(df)} artículos del Excel.")
    
    subtotal_carrito = 0
    carrito = []

    print("\n============================================")
    print("     BIENVENIDO A LA TIENDA LKCFRATE")
    print("============================================")

    while True:
        print("\n--------------------------------------------")
        busqueda = input("🔍 Ingrese CÓDIGO o NOMBRE (o escriba 'TODOS' para ver los 864 productos): ").strip().upper()

        if not busqueda:
            continue

        # Si el usuario quiere ver absolutamente todo el catálogo
        if busqueda in ['TODOS', 'VER', 'TODO']:
            coincidencias = df.copy()
        else:
            # Busca en los 864 productos por código o por cualquier coincidencia en el nombre
            coincidencias = df[
                df['COD_ARTICU'].str.upper().str.contains(busqueda) | 
                df['DESCRIPCIO'].str.upper().str.contains(busqueda)
            ]

        if coincidencias.empty:
            print("❌ No se encontraron productos con ese criterio de búsqueda.")
            continue

        # Si hay un único resultado exacto
        if len(coincidencias) == 1:
            prod_seleccionado = coincidencias.iloc[0]
        else:
            # Muestra TODOS los resultados encontrados entre los 864 productos
            print(f"\nSe encontraron {len(coincidencias)} productos:")
            lista_resultados = coincidencias.reset_index(drop=True)
            
            for idx, row in lista_resultados.iterrows():
                print(f" [{idx + 1}] Cód: {row['COD_ARTICU']} | {row['DESCRIPCIO']} - ${row['FINAL']:,.2f}")

            try:
                opcion = int(input(f"\nSeleccione el NÚMERO (1 a {len(lista_resultados)}) o 0 para cancelar: "))
                if opcion == 0 or opcion > len(lista_resultados) or opcion < 0:
                    print("Búsqueda cancelada.")
                    continue
                prod_seleccionado = lista_resultados.iloc[opcion - 1]
            except ValueError:
                print("Opción no válida.")
                continue

        # Selección y agregado al carrito
        nombre = prod_seleccionado['DESCRIPCIO']
        precio = prod_seleccionado['FINAL']
        print(f"\n✓ Producto Seleccionado: {nombre} (${precio:,.2f})")

        try:
            cantidad = int(input("Ingrese la cantidad: "))
            if cantidad > 0:
                costo_item = precio * cantidad
                subtotal_carrito += costo_item
                carrito.append((nombre, cantidad, costo_item))
                print(f"-> Añadido con éxito (+${costo_item:,.2f})")
            else:
                print("Cantidad no válida.")
        except ValueError:
            print("Por favor, ingrese un número entero.")

        continuar = input("\n¿Desea agregar otro producto? (SI/NO): ").strip().upper()
        if continuar in ['NO', 'N']:
            break

    # Resumen Final y Cobro
    if subtotal_carrito > 0:
        print("\n============================================")
        print("MÉTODOS DE PAGO DISPONIBLES:")
        print(" 1. Efectivo (5% de descuento)")
        print(" 2. Tarjeta de Crédito")
        print(" 3. Mercado Pago")
        
        opcion_pago = input("Seleccione método de pago (1, 2 o 3): ").strip()

        descuento = subtotal_carrito * 0.05 if opcion_pago == '1' else 0
        subtotal_con_desc = subtotal_carrito - descuento
        iva = subtotal_con_desc * 0.19
        total_final = subtotal_con_desc + iva

        print("\n============================================")
        print("             RESUMEN DE SU COMPRA           ")
        print("============================================")
        for item, cant, sub in carrito:
            print(f"• {cant}x {item} = ${sub:,.2f}")
        print("--------------------------------------------")
        print(f"Subtotal bruto:      ${subtotal_carrito:,.2f}")
        print(f"Descuento pago:     -${descuento:,.2f}")
        print(f"IVA (19%):           +${iva:,.2f}")
        print("--------------------------------------------")
        print(f"TOTAL A PAGAR:        ${total_final:,.2f}")
        print("============================================")
        print("¡Gracias por su compra!")
    else:
        print("\nCarrito vacío. Proceso cancelado.")

if __name__ == "__main__":
    sistema_tienda()