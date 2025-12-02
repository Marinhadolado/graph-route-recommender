from RouteGenerator import RouteGenerator
from TreeRoute import TreeRoute

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
     
    def recommend(self, user_id, lat, lon, context, steps):
        final_tree=self.get_final_tree(
            user_id=user_id,
            lat=lat,
            lon=lon,
            context=context,
            steps=steps
        )
        
        # MODO SELECCION RUTAL FINAL CON STEPS EXACTOS
        # UNA VEZ TENEMOS EL ARBOL FINAL FILTRADO, SELECCIONAMOS LA RUTA CON LOS STEPS SOLICITADOS
        
        if not final_tree:
            return None
        
        all_paths = final_tree.get_all_paths()
        num_pois = steps + 1
        selected_path_nodes = None
        
        for path in all_paths:
            if len(path) == num_pois:
                selected_path_nodes = path
                break

        if not selected_path_nodes and all_paths:
            print(f"[RECOMMENDER] No se encontró ruta de {steps} pasos exactos. Usando la mejor disponible.")
            selected_path_nodes = all_paths[0]

        if not selected_path_nodes:
            print("[RECOMMENDER] El árbol filtrado estaba vacío (caso raro).")
            return None

        #creamos un nuevo TreeRoute solo con la ruta seleccionada
        if selected_path_nodes:
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
