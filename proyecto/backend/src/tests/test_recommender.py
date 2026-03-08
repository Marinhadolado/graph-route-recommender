# En este test se probará si el recomendador devuelve las rutas con los filtros configurados

import sys
import os

# aseguramos de que se puedan importar los módulos desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RouteGenerator import RouteGenerator
from Recommender import Recommender

def test_recommender():

    generador = None
    try:
        # Datos para generar la ruta
        lat = 40.71149
        lon = -74.01321
        steps = 4
        context = {'context_retrieve': 'p1', 'temp': 22.0}

        print("[TR] Conectando a Neo4j...")
        generador = RouteGenerator()

        print("\n[TR] Creamos el recommender...")
        recommender = Recommender(generador)

        #------------------------------
        #CASO DE RECOMMENDER SIMPLE
        #------------------------------
        user_simple = "11111"

        print(f"\n[TRSIMPLE] Generando recomendación simple para usuario {user_simple} en ({lat}, {lon}) y con contexto {context}...")

        tree_simple = recommender.recommend_simple(
            user_id=user_simple,
            lat=lat,
            lon=lon,
            steps=steps,
            context=context
        )

        if tree_simple:
            print("[TRSIMPLE] Árbol generado por el recommender simple:")
            print(tree_simple)
        else:
            print("[TRSIMPLE] El recommender simple no encontró rutas.")

        #------------------------------
        #CASO DE RECOMMENDER POR SCORE
        #------------------------------

        print(f"\n[TRSCORE] Generando recomendación por score para usuario {user_simple} en ({lat}, {lon}) y con contexto {context}...")

        tree_score = recommender.recommend_by_score(
            user_id=user_simple,
            lat=lat,
            lon=lon,
            steps=steps,
            context=None
        )

        if tree_score:
            print("[TRSCORE] Árbol generado por el recommender por score:")
            print(tree_score)
        else:
            print("[TRSCORE] El recommender por score no encontró rutas.")

    except Exception as e:
        print(f"[TR] ERROR durante el test: {e}")
    finally:
        if generador:
            generador.cerrar_conexion()
            print("[TR] Conexión cerrada.")

if __name__ == "__main__":
    test_recommender()

