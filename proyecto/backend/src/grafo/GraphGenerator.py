from .GTGraph import GTGraph
from persistencia.Neo4jConnection import Neo4jConnection

class GraphGenerator:
    _loaded_graph=None
    _is_loaded = False

    def __init__(self, neo4j_client):
        """Recibe el cliente ya conectado a Neo4j."""
        if not isinstance(neo4j_client, Neo4jConnection):
            raise TypeError(f"[GraphGenerator] Error: El cliente debe ser una instancia de Neo4jConnection. "
                            f"Recibido: {type(neo4j_client)}")
        
        self.db = neo4j_client


    def getGraph(self):
        """Trae los datos de Neo4j y construye el grafo en memoria."""
        
        if GraphGenerator._is_loaded:
            return GraphGenerator._loaded_graph
        
        print("[GraphGenerator] Cargando grafo...")

        print(f"[GraphGenerator] Cargando POIs")

        self.graph = GTGraph()

        # cargamos los pois
        query_pois = """
        MATCH (p:POI) 
        RETURN p.fsq_id as fsq_id, p.latitude as latitude, p.longitude as longitude, 
               p.category as category, p.price as price, p.rating as rating, 
               p.total_ratings as total_ratings, p.total_tips as total_tips, p.category_lvlFs as category_lvlFs, 
               p.city as city,p.Weekday_EarlyMorning as Weekday_EarlyMorning, p.Weekday_Morning as Weekday_Morning, 
               p.Weekday_Afternoon as Weekday_Afternoon, p.Weekday_Night as Weekday_Night, 
               p.Weekend_EarlyMorning as Weekend_EarlyMorning, p.Weekend_Morning as Weekend_Morning, 
               p.Weekend_Afternoon as Weekend_Afternoon, p.Weekend_Night as Weekend_Night
        """
        pois = self.db.run_read(query_pois)
        for p in pois:
            self.graph.addNode(p)

        print(f"[GraphGenerator] Cargando Relaciones")
            
        # cargamos las relaciones
        query_rels = """
        MATCH (p1:POI)-[r:VISITED]->(p2:POI) 
        RETURN p1.fsq_id as p1_id, p2.fsq_id as p2_id, 
               r.user_id as user_id, r.trail_id as trail_id,
               r.p1_timestamp as p1_timestamp, r.p1_temp as p1_temp, 
               r.p1_precip as p1_precip, r.p1_windspeed as p1_windspeed, 
               r.p1_conditions as p1_conditions, r.p1_preciptype as p1_preciptype,
               r.p2_timestamp as p2_timestamp, r.p2_temp as p2_temp, 
               r.p2_precip as p2_precip, r.p2_windspeed as p2_windspeed, 
               r.p2_conditions as p2_conditions, r.p2_preciptype as p2_preciptype,
               r.time_diff_min as time_diff
        """
        rels = self.db.run_read(query_rels)
        for r in rels:
            # Pasamos p1_id y p2_id para la conexión y el resto en el dict rel_data
            self.graph.addEdge(r['p1_id'], r['p2_id'], r)
            
        
        GraphGenerator._is_loaded = True
        GraphGenerator._loaded_graph = self.graph
        print("[GraphGenerator] Grafo cargado correctamente.")
        
        return GraphGenerator._loaded_graph
    
if __name__ == "__main__":
    neo4j_client = Neo4jConnection()
    graph_gen = GraphGenerator(neo4j_client)
    graph = graph_gen.getGraph()
    print(f"Grafo generado con {graph.g.num_vertices()} nodos y {graph.g.num_edges()} aristas.")
    neo4j_client.close()

