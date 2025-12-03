from RouteGenerator import RouteGenerator
from TreeRoute import TreeRoute
import math


class Recommender:

    def __init__(self, route_generator:RouteGenerator):
        self.route_generator = route_generator
        self.cache = {}
        self.driver= route_generator.driver

    def __str__(self):
        return "Recommender using RouteGenerator and TreeRoute"
    
    def get_user_history(self, user_id):

        print(f"[RECOMMENDER] Obteniendo historial para user_id: {user_id}")
        # Usamos un 'set' para evitar POIs duplicados
        history_set = set() 
        
        # Esta consulta busca todos los POIs que el usuario ha visitado
        query = """
        MATCH (p:POI)-[r:VISITED {user_id: $user_id}]->()
        RETURN p.fsq_id AS visited_poi
        UNION
        MATCH (p:POI)<-[r:VISITED {user_id: $user_id}]-()
        RETURN p.fsq_id AS visited_poi
        """
        
        with self.driver.session() as session:
            results = session.run(query, user_id=user_id)
            for record in results:
                history_set.add(record['visited_poi'])
        
        print(f"[RECOMMENDER] Usuario ha visitado {len(history_set)} POIs únicos.")
        return history_set
    
    def get_final_tree(self, user_id, lat, lon, context, steps):
        print(f"[RECOMMENDER] Nueva recomendación para user: {user_id} en ({lat}, {lon}) con contexto: {context}")
        
        # obtenemos el historial de POIs visitados por el usuario
        history = self.get_user_history(user_id)
        
        # llamamos al generador de rutas, pero ahora pasándole
        # el contexto y el historial para que los filtre.
        candidate_tree = self.route_generator.get_routes(
            lat=lat, 
            lon=lon, 
            steps=steps
        )
        
        if not candidate_tree:
            print(f"[RECOMMENDER] No se encontraron rutas que cumplan los criterios de user_id: {user_id}, lat: {lat}, lon: {lon}, context: {context} y steps: {steps}.")
            return None
        
        final_tree = self.route_generator.update(
            candidate_tree=candidate_tree,
            history=history,
            context=context
        )

        if not final_tree:
            print("[RECOMMENDER] Ninguna ruta superó los filtros.")
            return None
        
        return final_tree

    def calculate_route_score(self, path_nodes):
        """
        Calcula una puntuación para la ruta basada en el Rating y la Popularidad.
        Score = Suma de (Rating * Popularidad_Log) de cada POI.
        """
        total_score = 0
        
        for node in path_nodes:

            # obtenemos datos del POI
            if node.is_root():
                poi = node.data
            else:
                poi = node.data.get('poi_data', {})

            # obtenemos el rating del poi
            rating = poi.get('rating', -1)
            if rating == -1: 
                rating = 0.0
            
            # obtenemos el total_ratings del poi
            total_ratings = poi.get('total_ratings', 0)
            if total_ratings == -1:
                total_ratings = 0
            
            # calculamos el factor de popularidad del total ratings
            # si total_ratings es 0 -> log10(1) = 0 -> Multiplicador es 0.
            # si total_ratings es 10 -> log10(11) = 1.04
            # si total_ratings es 100 -> log10(101) = 2.0
            # si total_ratings es 1000 -> log10(1001) = 3.0
            popularity_factor = math.log10(1 + total_ratings)
            
            # finalmente calculamos el score del poi
            # ejemplo: si Rating 9.0 y hay 100 votos -> 9.0 * 2.0 = 18 puntos
            # ejemplo: si Rating 9.0 y hay 0 votos   -> 9.0 * 0.0 = 0 puntos
            poi_score = rating * popularity_factor
            
            total_score += poi_score

        print(f"[RECOMMENDER] Puntuación total de la ruta: {total_score}")
        print(f"[RECOMMENDER] Ruta: {[node.tag for node in path_nodes]}")


        return total_score
        
    def recommend_simple(self, user_id, lat, lon, context, steps):
        final_tree=self.get_final_tree(
            user_id=user_id,
            lat=lat,
            lon=lon,
            context=context,
            steps=steps
        )
        
        # MODO SELECCION RUTAL FINAL CON STEPS EXACTOS
        # UNA VEZ TENEMOS EL ARBOL FINAL FILTRADO, SELECCIONAMOS LA PRIMERA RUTA CON LOS STEPS SOLICITADOS
        
        if not final_tree:
            return None
        
        all_paths = final_tree.get_all_paths()
        num_pois = steps + 1
        selected_path_nodes = None
        
        for path in all_paths:
            if len(path) == num_pois:
                selected_path_nodes = path
                break

        if not selected_path_nodes:
            print(f"[RECOMMENDER] No se encontró una ruta con el número de pasos solicitados({steps}). Buscando la siguiente ruta más larga...")
            best_len = float('inf')
            for path in all_paths:
                current_path= path
                if len(current_path) < best_len:
                    best_len = len(current_path)
                    selected_path_nodes = current_path
                

        #creamos un nuevo TreeRoute solo con la ruta seleccionada
        start_poi = selected_path_nodes[0].data
        final_route = TreeRoute(start_poi)
        
        for i in range(1, len(selected_path_nodes)):
            parent_node = selected_path_nodes[i-1]
            current_node = selected_path_nodes[i]
            
            parent_id = parent_node.identifier
            current_poi = current_node.data.get('poi_data', {})
            edge_data = current_node.data.get('edge_data', {})
            
            final_route.agregarPoi(
                poi_padre_id=parent_id,
                nuevo_poi=current_poi,
                datos_relacion=edge_data
            )

        return final_route
    
    def recommend_by_score(self, user_id, lat, lon, context, steps):
        # Método alternativo de recomendación basado en puntuaciones
        final_tree=self.get_final_tree(
            user_id=user_id,
            lat=lat,
            lon=lon,
            context=context,
            steps=steps
        )
        
        if not final_tree:
            return None
        
        
        # MODO SELECCION RUTAL FINAL CON STEPS EXACTOS Y SCORE MEJOR
        # UNA VEZ TENEMOS EL ARBOL FINAL FILTRADO, SELECCIONAMOS LA RUTA CON MEJOR SCORE(RATING*POPULARIDAD)
        # ejemplo: si hay un sitio con un 9 de media con 1000 valoraciones se prioriza a uno con 9 y 10 valoraciones
        
        all_paths = final_tree.get_all_paths()
        target_len = steps + 1
        
        best_path = None
        best_score = -1
        
        print(f"[RECOMMENDER] Analizando {len(all_paths)} rutas posibles para encontrar la mejor...")

        for path in all_paths:
            if len(path) == target_len:          
                # con la funcion calculamos el score
                current_score = self.calculate_route_score(path)

                
                #si es mejor que las anteriores se guarda
                if current_score > best_score:
                    print(f"[RECOMMENDER] Nueva mejor ruta encontrada con score: {current_score}")
                    best_score = current_score
                    best_path = path
        
        # si no encontramos ruta con la longitud exacta, buscamos la mejor ruta corta
        if not best_path and all_paths:
            print("[RECOMMENDER] No se encontró ruta de longitud exacta. Buscando la mejor ruta corta...")
            for path in all_paths:
                current_score = self.calculate_route_score(path)
                if current_score > best_score:
                    best_score = current_score
                    best_path = path

            print(f"[RECOMMENDER] Mejor ruta corta encontrada con score: {best_score}")

        if not best_path:
            return None
        
        #creamos un nuevo TreeRoute solo con la ruta seleccionada
        start_poi = best_path[0].data
        final_route = TreeRoute(start_poi)
        
        for i in range(1, len(best_path)):
            parent_node = best_path[i-1]
            current_node = best_path[i]
            
            parent_id = parent_node.identifier
            current_poi = current_node.data.get('poi_data', {})
            edge_data = current_node.data.get('edge_data', {})
            
            final_route.agregarPoi(
                poi_padre_id=parent_id,
                nuevo_poi=current_poi,
                datos_relacion=edge_data
            )
        
        return final_route
        