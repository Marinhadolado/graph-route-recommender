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
            print("Conexión exitosa a la base de datos Neo4j")
        except Exception as e:
            print(f"Error al conectar a la base de datos Neo4j: {e}")
            raise

        self.treeRoutes_cache = {}

    def cerrar_conexion(self):
        self.driver.close()

    def get_routes(self, lat, lon, steps=4):

        cache_key = (lat, lon, steps)

        print(f"Ejecutando consulta Cypher para ({lat}, {lon}) con {steps} saltos.")

        query = """
        //
        MATCH (s:POI)-[:VISITED]->()
        WITH DISTINCT s,
        point({ latitude:s.latitude, longitude:s.longitude }) AS ps,
        point({ latitude:$lat, longitude:$lon }) AS q
         ORDER BY point.distance(ps, q) ASC
        LIMIT 1
        WITH s AS start

        // 2. Rutas de hasta N saltos
        MATCH p = (start)-[rs:VISITED*1..4]->(end)

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
                print("No se encontraron rutas.")
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
                    rel_data = dict(rel)  # Los datos de la relación (ej. REL12)

                    # Usamos 'agregarPoi' para crear la ruta
                    treeRoute.agregarPoi(
                        poi_padre_id=padre_poi['fsq_id'],
                        nuevo_poi=dict(hijo_poi),
                        datos_relacion=rel_data
                    )

        if treeRoute:
            self.treeRoutes_cache[cache_key] = treeRoute

        return treeRoute
    

