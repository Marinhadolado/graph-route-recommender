from RouteGenerator import RouteGenerator 

def test():
    print("PRUEBA MAIN DE GENERADOR DE RUTAS\n")
    
    generador = None # Para el 'finally'
    try:
        print("Creando GeneradorRutas...")
        generador = RouteGenerator()
        print("--- Generador de rutas creado y conectado. ---")

        # datos para generar la ruta
        lat_ejemplo = 40.71149
        lon_ejemplo = -74.01321
        pasos_ejemplo = 4

        # --- PRUEBA 1: Primera llamada (Usa Cypher) ---
        print(f"\n[PRUEBA 1] Buscando rutas para ({lat_ejemplo}, {lon_ejemplo}) con {pasos_ejemplo} pasos...")
        treeRoute = generador.get_routes(lat_ejemplo, lon_ejemplo, steps=pasos_ejemplo)

        if treeRoute:
            print("\n¡ÉXITO! Se encontró una ruta.")
            print("Árbol de rutas generado:")
            print(treeRoute)
        elif not treeRoute:
             print("\nNo se encontraron rutas en la primera búsqueda.")

    except Exception as e:
        print(f"\n¡HA OCURRIDO UN ERROR FATAL!")
        print(f"Error: {e}")
    finally:
        if generador:
            generador.cerrar_conexion()
            print("\n Al finalizar, cerrando conexión del generador de rutas...")

if __name__ == "__main__":
    test()