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

        print(f"Obteniendo historial para user_id: {user_id}")
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
        
        print(f"Usuario ha visitado {len(history_set)} POIs únicos.")
        return history_set
     
    def recommend(self, user_id, lat, lon, context, steps=4):
        print(f"Nueva recomendación para user: {user_id} en ({lat}, {lon}) con contexto: {context}")
        
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
            print(" No se encontraron rutas que cumplan los criterios.")
            return None
        
        final_tree = self.route_generator.update(
            candidate_tree=candidate_tree,
            history=history,
            context=context
        )

        if not final_tree:
            print("Ninguna ruta superó los filtros.")
            return None
        
        #---------------------
        #RUTA FINAL

        #obtenemos la ruta final seleccionando la que tenga los 'steps' solicitados
        #all_valid_paths = final_tree.get_all_paths()
        #
        #target_length = steps + 1 # +1 porque si son 3 saltos son 4 nodos
        #selected_path_nodes = None
        #for path in all_valid_paths:
        #    #encontramos la primera ruta que tenga los 'steps' exactos
        #    if len(path) == target_length:
        #        selected_path_nodes = path
        #        break
        #
        ## Si no encontramos ninguna con los 'steps' exactos cogemos la primera ruta válida que haya.
        #if not selected_path_nodes and all_valid_paths:
        #    print(f"No se encontró ruta con {steps} pasos, se seleccionará la primera disponible.")
        #    selected_path_nodes = all_valid_paths[0]
#
        #print(f"Ruta seleccionada con {len(selected_path_nodes) - 1} pasos. Creando árbol final...")
#
        ##creamos el nuevo arbol con los nodos seleccionados
        #root_data = selected_path_nodes[0].data
        #final_route = TreeRoute(root_data)
        #
        #for i in range(len(selected_path_nodes) - 1):
        #    parent_node = selected_path_nodes[i]
        #    child_node = selected_path_nodes[i+1]
        #    
        #    final_route.agregarPoi(
        #        poi_padre_id=parent_node.identifier,
        #        nuevo_poi=child_node.data['poi_data'],
        #        datos_relacion=child_node.data['edge_data']
        #    )

        print("Devolviendo el árbol de rutas filtrado.")
        return  final_tree