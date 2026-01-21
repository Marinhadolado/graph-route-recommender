#En este test se probará si Neo4j devuelve las rutas sin ningún filtro aplicado

import sys
import os

# aseguramos de que se puedan importar los módulos desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RouteGenerator import RouteGenerator

def test_route_generation():
    print("\n--- TEST GENERATOR 1: GENERACIÓN DE RUTAS SIN FILTRADO ---")
    print("--------------------------------------------------")

    generador = None

    try:
        # Datos para generar la ruta
        lat = 40.71149
        lon = -74.01321
        steps = 4

        print("[TG1] Conectando a Neo4j...")
        generador = RouteGenerator()

        print(f"[TG1] Buscando rutas para ({lat}, {lon}) con {steps} pasos...")
        treeRoute = generador.get_routes(lat, lon, steps)

        if treeRoute is None:
            print("[TG1] ERROR: No se encontraron rutas.")
            return

        print("[TG1] Árbol de rutas generado:")
        print(treeRoute)
    
    except Exception as e:
        print(f"[TG1] ERROR durante el test: {e}")

    finally:
        if generador:
            generador.cerrar_conexion()
            print("[TG1] Conexión cerrada.")
    
if __name__ == "__main__":
    test_route_generation()