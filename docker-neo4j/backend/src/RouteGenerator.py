import os
from neo4j import GraphDatabase
from TreeRoute import TreeRoute

class RouteGenerator:

    def __init__(self):
        # Configuración de la conexión a Neo4j para el generador de rutas
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7999")
        user= os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("[ROUTE GENERATOR] Conexión exitosa a la base de datos Neo4j")
        except Exception as e:
            print(f"[ROUTE GENERATOR]Error al conectar a la base de datos Neo4j: {e}")
            raise

        self.treeRoutes_cache = {}

    def __str__(self):
        return "RouteGenerator conectado a Neo4j"

    def cerrar_conexion(self):  
        self.driver.close()

    def get_routes(self, lat, lon, steps):

        cache_key = (lat, lon, steps)

        print(f"[ROUTE GENERATOR]Ejecutando consulta Cypher para ({lat}, {lon}) con {steps} saltos.")

        query = f"""
        //
        MATCH (s:POI)-[:VISITED]->()
        WITH DISTINCT s,
        point({{ latitude:s.latitude, longitude:s.longitude }}) AS ps,
        point({{ latitude:$lat, longitude:$lon }}) AS q
         ORDER BY point.distance(ps, q) ASC
        LIMIT 1
        WITH s AS start

        // 2. Rutas de hasta N saltos
        MATCH p = (start)-[rs:VISITED*1..{steps}]->(end)

        // 3. Filtros (mismo user, sin bucles, tiempo ok)
        WITH p, rs, rs[0].user_id AS u, start
        WHERE all(r IN rs WHERE r.user_id = u)
         AND all(r IN rs WHERE r.time_diff_min IS null OR r.time_diff_min >= 0)
         AND size(reduce(acc = [], n IN nodes(p) | CASE WHEN n IN acc THEN acc ELSE acc + n END)) = size(nodes(p))

        // 4. Devolver lo que necesitamos para construir el árbol
        RETURN
        start AS startPOI,
        nodes(p) as pois,       // Lista de TODOS los nodos en la ruta
        relationships(p) as rels // Lista de TODAS las relaciones en la ruta
         ORDER BY size(rs) DESC
        """
        
        treeRoute = None
        
        with self.driver.session() as session:
            
            results = session.run(query, lat=lat, lon=lon, steps=steps)

            # peek para ver el primer resultado y comprobar si se obtuvieron rutas
            first_record = results.peek()
            
            if not first_record:
                print("[ROUTE GENERATOR] No se encontraron rutas.")
                return None

            
            # creamos el treeRoute con el POI inicial
            start_poi_data = dict(first_record["startPOI"])
            treeRoute = TreeRoute(start_poi_data)
            
            # vamos ruta por ruta para completar el arbol
            for record in results:
                # 'pois' es una lista de nodos: [POI1, POI2, POI3]
                # 'rels' es una lista de relaciones: [REL12, REL23]
                pois = record["pois"]
                rels = record["rels"]
                
                # vamos relacion por relación para crear la ruta en el árbol
                for i, rel in enumerate(rels):
                    # Obtenemos los datos que necesitamos
                    padre_poi = pois[i] # El nodo padre (ej. POI1)
                    hijo_poi = pois[i+1]  # El nodo hijo (ej. POI2)
                    edge_data = dict(rel)  # Los datos de la relación (ej. REL12)

                    # Usamos 'agregarPoi' para crear la ruta
                    treeRoute.agregarPoi(
                        poi_padre_id=padre_poi['fsq_id'],
                        nuevo_poi=dict(hijo_poi),
                        datos_relacion=edge_data
                    )

        if treeRoute:
            self.treeRoutes_cache[cache_key] = treeRoute

        return treeRoute
    
    def filter_path_by_history(self, path_nodes, history_set):
        """
        Comprueba si una ruta (lista de nodos) contiene POIs del historial.
        Devuelve True si la ruta es VÁLIDA (no tiene historial).
        """
        for node in path_nodes[1:]: # Empezamos en 1 para saltarnos la raíz
            poi_id = node.data['poi_data']['fsq_id']
            if poi_id in history_set:
                print(f"[ROUTE GENERATOR] Descartando por historial: POI {poi_id} ya visitado.")
                return False # ¡Este POI ya ha sido visitado! Ruta inválida.
        return True # Ruta válida

    def filter_path_by_context(self, path_nodes, context):
        """
        Comprueba si una ruta (lista de nodos) cumple con el contexto,
        usando la lógica de 'context_retrieve'.
        """
        if not context:
            return True # No hay contexto, la ruta es válida

        # Lógica de 'context_retrieve': usamos 'p1' (partida) por defecto
        retrieve_prefix = context.get('context_retrieve', 'p1') 

        for node in path_nodes[1:]: # Saltamos la raíz
            edge_data = node.data['edge_data'] 
            
            if 'preciptype' in context:
                key = f"{retrieve_prefix}_preciptype"
                if edge_data.get(key, "") != context['preciptype']:
                    print(f"[ROUTE GENERATOR] Descartando por preciptype: {edge_data.get(key)} != {context['preciptype']}")
                    return False
            
            if 'temp' in context:
                key = f"{retrieve_prefix}_temp"
                if edge_data.get(key) != context['temp']:
                    print(f"[ROUTE GENERATOR] Descartando por temp: {edge_data.get(key)} != {context['temp']}")
                    return False
                
            if 'windspeed' in context:
                key = f"{retrieve_prefix}_windspeed"
                if edge_data.get(key) != context['windspeed']:
                    print(f"[ROUTE GENERATOR] Descartando por windspeed: {edge_data.get(key)} != {context['windspeed']}")
                    return False
            
            if 'precip' in context:
                key = f"{retrieve_prefix}_precip"
                if edge_data.get(key) != context['precip']:
                    print(f"[ROUTE GENERATOR] Descartando por precip: {edge_data.get(key)} != {context['precip']}")
                    return False
            
            if 'conditions' in context:
                key = f"{retrieve_prefix}_conditions"
                if edge_data.get(key) != context['conditions']:
                    print(f"[ROUTE GENERATOR] Descartando por conditions: {edge_data.get(key)} != {context['conditions']}")
                    return False
            

        return True # Si ha pasado todos los filtros, la ruta es válida
    
    def update(self, candidate_tree: TreeRoute, history, context):
        """
        Toma un árbol de candidatas y lo filtra según el historial y el contexto.
        Devuelve un NUEVO TreeRoute solo con las rutas válidas.
        """
        
        if not candidate_tree:
            return None
        
        # 1. Extraemos todas las rutas del árbol candidato
        all_candidate_paths = candidate_tree.get_all_paths()
        print(f"[ROUTE GENERATOR] UPDATE Filtrando {len(all_candidate_paths)} rutas candidatas...")

        # 2. Creamos el nuevo árbol final
        root_data = candidate_tree.tree.get_node(candidate_tree.tree.root).data
        final_tree = TreeRoute(root_data)
        
        has_valid_routes = False

        for path in all_candidate_paths:
            
            # 3. Aplicamos los filtros
            is_valid_history = self.filter_path_by_history(path, history)
            is_valid_context = self.filter_path_by_context(path, context)
            
            # 4. Si la ruta es válida, la reconstruimos en el árbol final
            if is_valid_history and is_valid_context:
                has_valid_routes = True
                # Re-añadimos la ruta válida al nuevo árbol
                for i in range(len(path) - 1):
                    parent_node = path[i]
                    child_node = path[i+1]
                    
                    final_tree.agregarPoi(
                        poi_padre_id=parent_node.identifier,
                        nuevo_poi=child_node.data['poi_data'],
                        datos_relacion=child_node.data['edge_data']
                    )
        
        
        if not has_valid_routes:
            print("[ROUTE GENERATOR] UPDATE Ninguna ruta candidata superó los filtros.")
            return None

        return final_tree
    

