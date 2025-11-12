from RouteGenerator import RouteGenerator
from TreeRoute import TreeRoute
from Recommender import Recommender 

def test():
    print("PRUEBA MAIN DE GENERADOR DE RUTAS\n")
    
    generador = None # Para el 'finally'
    try:
        # --- PRUEBA 1: Primera llamada (Usa Cypher) ---
        print("\n--- GENERATOR DE RUTAS ---")
        print("----------------------------------")


        # datos para generar la ruta
        lat_ejemplo = 40.71149
        lon_ejemplo = -74.01321
        pasos_ejemplo = 4

        print("Creando GeneradorRutas...")
        generador = RouteGenerator()

        print(f"\n Buscando rutas para ({lat_ejemplo}, {lon_ejemplo}) con {pasos_ejemplo} pasos...")
        treeRoute = generador.get_routes(lat_ejemplo, lon_ejemplo, steps=pasos_ejemplo)

        if treeRoute:
            print("\n¡ÉXITO! Se encontró una ruta.")
            print("Árbol de rutas generado:")
            print(treeRoute)
        elif not treeRoute:
             print("\nNo se encontraron rutas en la primera búsqueda.")

        # --- PRUEBA 2: Recomendador rutas ---
        print("\n--- RECOMMENDER DE RUTAS ---")
        print("----------------------------------")

        #USAR ESTE USER_ID PARA TESTEAR EL HISTORIAL
        # trail_id= "2657913"
        user_id_historial="172831"

        recommender = Recommender(route_generator=generador)

        print(f"\n TESTEANDO EL CASO DE ELIMINAR HISTORIAL DE USER_ID: {user_id_historial} ...")
        print(f"\n Generando recomendación para user_id: {user_id_historial} en ({lat_ejemplo}, {lon_ejemplo}) sin contexto: ...")
        recommended_tree = recommender.recommend(
            user_id=user_id_historial,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=None,
            steps=pasos_ejemplo
        )

        if recommended_tree:
            print("\n¡ÉXITO! Se encontró una ruta recomendada.")
            print("Árbol de rutas recomendado:")
            print(recommended_tree)
        else:
            print("\nNo se encontraron rutas recomendadas que cumplan los criterios.")

        # --- PRUEBA 3: Filtrado por contexto ---
        print("\n TESTEANDO FILTRADO POR CONTEXTO CON TEMPERATURA...")

        #datos para recomendación
        user_id_contexto="26182"
        p1_temp = 22.0
        context= {
            'context_retrieve': 'p1',
            'temp': p1_temp,
        }

        print(f"\n Generando recomendación para user_id: {user_id_contexto} en ({lat_ejemplo}, {lon_ejemplo}) con contexto: {context}...")
        recommended_tree_context = recommender.recommend(
            user_id=user_id_contexto,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=context,
            steps=pasos_ejemplo
        )

        if recommended_tree_context:
            print("\n¡ÉXITO! Se encontró una ruta recomendada con contexto.")
            print("Árbol de rutas recomendado con contexto:")
            print(recommended_tree_context)
        else:
            print("\nNo se encontraron rutas recomendadas que cumplan los criterios de contexto.")        

    except Exception as e:
        print(f"\n¡HA OCURRIDO UN ERROR FATAL!")
        print(f"Error: {e}")
    finally:
        if generador:
            #generador.cerrar_conexion()
            print("\n Al finalizar, cerrando conexión del generador de rutas...")

if __name__ == "__main__":
    test()