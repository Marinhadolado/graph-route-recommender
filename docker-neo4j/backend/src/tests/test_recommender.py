from RouteGenerator import RouteGenerator
from TreeRoute import TreeRoute
from Recommender import Recommender 

def test():
    print("PRUEBA MAIN DE GENERADOR DE RUTAS\n")
    
    generador = None
    try:
        #-----------------------------------
        # --- PRUEBA 1: Route Generator ----
        #-----------------------------------

        print("\n--- GENERATOR DE RUTAS ---")
        print("----------------------------------")


        # datos para generar la ruta
        lat_ejemplo = 40.71149
        lon_ejemplo = -74.01321
        pasos_ejemplo = 4

        print("[MAIN] Creando GeneradorRutas...")
        generador = RouteGenerator()

        print(f"\n[MAIN] Buscando rutas para ({lat_ejemplo}, {lon_ejemplo}) con {pasos_ejemplo} pasos...")
        treeRoute = generador.get_routes(lat_ejemplo, lon_ejemplo, steps=pasos_ejemplo)

        if treeRoute:
            print("\n[MAIN] ¡ÉXITO! Se encontró una ruta.")
            print("[MAIN] Árbol de rutas generado:")
            print(treeRoute)
        elif not treeRoute:
             print("\n[MAIN] No se encontraron rutas en la primera búsqueda.")



        #-----------------------------------------------------------------
        # --- PRUEBA 2: Pruebas de filtrado para el recommender ----------
        #-----------------------------------------------------------------

        print("\n--- FILTRADO DE RUTAS ---")
        print("----------------------------------")

        recommender = Recommender(route_generator=generador)

        # --- Filtrado por historial ---

        # trail_id= "2657913"
        user_id_historial="172831" # se debería eliminar la rama de Scenic Lookout (la del trail_id de arriba)

        print(f"\n[MAIN] TESTEANDO EL CASO DE FILTRADO DE HISTORIAL")
        print(f"\n[MAIN] Generando recomendación para user_id: {user_id_historial} en ({lat_ejemplo}, {lon_ejemplo}) sin contexto: ...")
        
        history_tree=recommender.get_final_tree(
            user_id=user_id_historial,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=None,
            steps=pasos_ejemplo
        )

        if history_tree:
            print("\n[MAIN] Árbol de rutas recomendado tras filtrar por historial:")
            print(history_tree)
        else:
            print("[MAIN] No se encontraron rutas recomendadas que cumplan los criterios de historial.")   


        print("\n----------------------------------")

        # --- Filtrado por contexto ---

        user_id_contexto="26182"
        p1_temp = 22.0 # solo se obtiene una sola ruta de 2 pois
        context= {
            'context_retrieve': 'p1',
            'temp': p1_temp,
        }

        print("\n[MAIN] TESTEANDO FILTRADO POR CONTEXTO CON TEMPERATURA")
        print(f"\n[MAIN] Generando recomendación para user_id: {user_id_contexto} en ({lat_ejemplo}, {lon_ejemplo}) con contexto: {context}...")

        context_tree=recommender.get_final_tree(
            user_id=user_id_contexto,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=context,
            steps=pasos_ejemplo
        )

        if context_tree:
            print("\n[MAIN] Árbol de rutas recomendado tras filtrar por contexto:")
            print(context_tree)
        else:
            print("[MAIN] No se encontraron rutas recomendadas que cumplan los criterios de contexto.")   


        #-----------------------------------------------------------------
        # --- PRUEBA 2: Prueba de recommender ----------
        #-----------------------------------------------------------------

        print("\n--- RECOMMENDER ---")
        print("----------------------------------")

        # --- Recomendación simple ---
        user_id_ok="11111"
        
        print(f"\n[MAIN] TESTEANDO EL CASO DE RECOMENDACIÓN SIMPLE CON USUARIO RANDOM")
        print(f"\n[MAIN] Generando recomendación para user_id: {user_id_ok} en ({lat_ejemplo}, {lon_ejemplo}) con contexto: {context}...")
        recommended_tree_simple = recommender.recommend_simple(
            user_id=user_id_ok,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=None,
            steps=pasos_ejemplo
        )

        if recommended_tree_simple:
            print("\n[MAIN] ¡ÉXITO! Se encontró una ruta recomendada con contexto.")
            print("[MAIN] Árbol de rutas recomendado con contexto:")
            print(recommended_tree_simple)
        else:
            print("\n[MAIN] No se encontraron rutas recomendadas que cumplan los criterios de contexto.")     
         
        # --- Recomendación por score ---
        
        print(f"\n[MAIN] TESTEANDO EL CASO DE RECOMENDACIÓN POR SCORE CON USUARIO RANDOM")
        print(f"\n[MAIN] Generando recomendación para user_id: {user_id_ok} en ({lat_ejemplo}, {lon_ejemplo}) con contexto: {context}...")
        recommended_tree_score = recommender.recommend_by_score(
            user_id=user_id_ok,
            lat=lat_ejemplo,
            lon=lon_ejemplo,
            context=None,
            steps=pasos_ejemplo
        )

        if recommended_tree_score:
            print("\n[MAIN] ¡ÉXITO! Se encontró una ruta recomendada con contexto.")
            print("[MAIN] Árbol de rutas recomendado con contexto:")
            print(recommended_tree_score)
        else:
            print("\n[MAIN] No se encontraron rutas recomendadas que cumplan los criterios de contexto.")

    except Exception as e:
        print(f"\n¡HA OCURRIDO UN ERROR FATAL!")
        print(f"Error: {e}")
    finally:
        if generador:
            #generador.cerrar_conexion()
            print("\n Al finalizar, cerrando conexión del generador de rutas...")

if __name__ == "__main__":
    test()