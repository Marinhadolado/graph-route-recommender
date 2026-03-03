from GTGraph import GTGraph
from gestion_datos.Neo4jConnection import Neo4jConnection

class GraphGenerator:
    def __init__(self, neo4j_client):
        """Recibe el cliente ya conectado a Neo4j."""
        if not isinstance(neo4j_client, Neo4jConnection):
            raise TypeError(f"[GraphGenerator] Error: El cliente debe ser una instancia de Neo4jConnection. "
                            f"Recibido: {type(neo4j_client)}")
        
        self.db = neo4j_client
        self.graph = GTGraph()
        self.is_loaded = False

    def generateGraph(self):
        """Trae los datos de Neo4j y construye el grafo en memoria."""
        if self.is_loaded: 
            return self.graph
        
        print("[GraphGenerator] Hidratando grafo (esto puede tardar)...")
        
        # 1. Cargar Nodos
        pois = self.db.run_read("MATCH (p:POI) RETURN p.fsq_id as id")
        for p in pois:
            self.graph.add_node(p['id'])
            
        # 2. Cargar Relaciones
        rels = self.db.run_read("MATCH (p1:POI)-[:VISITED]->(p2:POI) RETURN p1.fsq_id as p1, p2.fsq_id as p2")
        for r in rels:
            self.graph.add_edge(r['p1'], r['p2'])
            
        self.is_loaded = True
        print("[GraphGenerator] Grafo hidratado correctamente.")
        return self.graph