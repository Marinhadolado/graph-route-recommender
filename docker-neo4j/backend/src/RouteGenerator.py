import os
from neo4j import GraphDatabase
from TreeRoute import TreeRoute
from POI import POI

class RouteGenerator:

    def __init__(self):
        # Configuración de la conexión a Neo4j
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

    def __str__(self):
        if self.driver:
            estado = "Conectado" 
        else: 
            estado ="Desconectado"
        return f"RouteGenerator {estado}" 

    def close(self):  
        self.driver.close()

    def getRoutes(self, lat, lon, steps):
        """
        Crea un arbol de rutas ya hechas partiendo de un punto con un límite de steps establecidos
        
        :param self
        :param lat: latitud de referencia para el inicio de la ruta
        :param lon: longitud de referencia para el inicio de la ruta
        :param steps: número máximo de saltos de una ruta 
        """

        print(f"[ROUTE GENERATOR]Ejecutando consulta Cypher para ({lat}, {lon}) con máximo {steps} saltos.")

        query = f"""
        // 1. Primero buscamos el poi más cercano a las coordenadas dadas
        MATCH (s:POI)-[:VISITED]->()
        WITH DISTINCT s,
        point({{ latitude:s.latitude, longitude:s.longitude }}) AS poi_location,
        point({{ latitude:$lat, longitude:$lon }}) AS user_location
         ORDER BY point.distance(poi_location, user_location) ASC
        LIMIT 1
        WITH s AS start

        // 2. Rutas de hasta steps saltos
        MATCH p = (start)-[rs:VISITED*1..{steps}]->(end)

        // 3. Filtros (mismo user, sin bucles, tiempo ok)
        WITH p, rs, rs[0].user_id AS u, start
        WHERE all(r IN rs WHERE r.user_id = u)
         AND all(r IN rs WHERE r.time_diff_min IS null OR r.time_diff_min >= 0)
         AND size(reduce(acc = [], n IN nodes(p) | CASE WHEN n IN acc THEN acc ELSE acc + n END)) = size(nodes(p))

        // 4. Devolver lo que necesitamos para construir el árbol
        RETURN
        start AS startPOI,
        nodes(p) as pois,
        relationships(p) as rels
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
            start_node = first_record["startPOI"]
            start_poi = POI.nodeToPOI(start_node)
            treeRoute = TreeRoute(start_poi)
            
            # vamos ruta por ruta para completar el arbol
            for record in results:
                # 'pois' es una lista de nodos: [POI1, POI2, POI3]
                pois = record["pois"]
                # 'rels' es una lista de relaciones: [REL12, REL23]
                rels = record["rels"]
                
                # vamos relacion por relación para crear la ruta en el árbol
                for i, rel in enumerate(rels):
                    father_node = pois[i] # El nodo padre (ej. POI1)
                    son_node = pois[i+1]  # El nodo hijo (ej. POI2)

                    son_poi= POI.nodeToPOI(son_node)
                    edge_data = dict(rel)  # Los datos de la relación (ej. REL12)

                    # Usamos 'agregarPoi' para crear la ruta
                    treeRoute.agregarPoi(
                        poi_padre_id=father_node['fsq_id'],
                        nuevo_poi=son_poi,
                        datos_relacion=edge_data
                    )

        return treeRoute