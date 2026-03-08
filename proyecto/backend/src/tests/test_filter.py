# En este test se probarña si el filtrado de rutas por historial y contexto funciona correctamente

import sys
import os

# aseguramos de que se puedan importar los módulos desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RouteGenerator import RouteGenerator
from Recommender import Recommender

def test_route_filtering():
    print("\n--- TEST FILTER: FILTRADO DE RUTAS SEGÚN HISTORIAL Y CONTEXTO ---")
    print("--------------------------------------------------")

    generador = None

    try:
        # Datos para generar la ruta
        lat = 40.71149
        lon = -74.01321
        steps = 4

        # Usuario conocido con historial en tu DB
        user_con_historial = "172831" 
        user_frio = "26182"
        contexto_frio = {'context_retrieve': 'p1', 'temp': 22.0}

        print("[TF] Conectando a Neo4j...")
        generador = RouteGenerator()

        print("\n[TF] Creamos el recommender...")
        recommender = Recommender(generador)

        print("\n[TF] Generando árbol de rutas candidato sin filtrar nada...")
        tree_candidato = generador.get_routes(lat, lon, steps)
        if tree_candidato:
            print("[TF] Árbol candidato generado:")
            print(tree_candidato)
        else:
            print("[TF] No se encontraron rutas candidatas.")
            return

        #------------------------------
        #CASO DE FILTRADO POR HISTORIAL
        #------------------------------

        print(f"\n[TFHISTORIAL] Aplicando filtrado por historial con usuario {user_con_historial}...")

        tree_history = recommender.get_final_tree(
            user_id=user_con_historial,
            lat=lat, lon=lon,
            context=None,
            steps=steps,
            filter_history=True
        )
        if tree_history:
            print("[TFHISTORIAL] Árbol generado tras filtrar historial:")
            print(tree_history)
        else:
            print("[TFHISTORIAL] El filtro de historial eliminó todas las rutas (o no se encontraron).")

        #------------------------------
        #CASO DE FILTRADO POR CONTEXTO
        #------------------------------

        print(f"\n[TFCONTEXTO] Aplicando filtrado por contexto al usuario {user_frio} con este contexto {contexto_frio}...")

        tree_context = recommender.get_final_tree(
            user_id=user_frio,
            lat=lat, lon=lon,
            context=contexto_frio,
            steps=steps,
            filter_history=True
        )

        if tree_context:    
            print("[TFCONTEXTO] Rutas válidas tras el filtrado:")
            print(tree_context)
        else:
            print("[TFCONTEXTO] El filtro de contexto eliminó todas las rutas (o no se encontraron).")
    
    except Exception as e:
        print(f"[TF] ERROR durante el test: {e}")

    finally:
        if generador:
            generador.cerrar_conexion()
            print("[TF] Conexión cerrada.")

if __name__ == "__main__":
    test_route_filtering()
