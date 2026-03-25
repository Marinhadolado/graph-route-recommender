import graph_tool.all as gt
import os
from .GTGraph import GTGraph
from persistencia.Neo4jConnection import Neo4jConnection
from persistencia.LoadDB import LoadDB

class BuildGraph:
    def __init__(self, neo4j_client, city_name):
        if not isinstance(neo4j_client, Neo4jConnection):
            raise ValueError("El cliente de base de datos debe ser una instancia de Neo4jConnection.")
        self.db = neo4j_client
        self.city_name = city_name
        self.graph = GTGraph()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.import_path= os.path.join(base_dir, "../../../import")
        os.makedirs(self.import_path, exist_ok=True)

    def build(self):
        """Trae los datos de Neo4j y guarda en una carpeta el grafo."""
        
        print("[BuildGraph] Cargando grafo...")

        print(f"[BuildGraph] Cargando POIs")

        self.graph = GTGraph()

        # cargamos los pois
        query_pois = """
        MATCH (p:POI) 
        WHERE p.city = $city_name
        RETURN p.fsq_id as fsq_id, p.latitude as latitude, p.longitude as longitude, 
               p.category as category, p.price as price, p.rating as rating, 
               p.total_ratings as total_ratings, p.total_tips as total_tips, p.category_lvlFs as category_lvlFs, 
               p.city as city,p.Weekday_EarlyMorning as Weekday_EarlyMorning, p.Weekday_Morning as Weekday_Morning, 
               p.Weekday_Afternoon as Weekday_Afternoon, p.Weekday_Night as Weekday_Night, 
               p.Weekend_EarlyMorning as Weekend_EarlyMorning, p.Weekend_Morning as Weekend_Morning, 
               p.Weekend_Afternoon as Weekend_Afternoon, p.Weekend_Night as Weekend_Night
        """
        pois = self.db.run_read(query_pois, {"city_name": self.city_name})
        for p in pois:
            self.graph.addNode(p)

        print(f"[BuildGraph] Cargando Relaciones")
            
        # cargamos las relaciones
        query_rels = """
        MATCH (p1:POI)-[r:VISITED]->(p2:POI) 
        WHERE p1.city = $city_name AND p2.city = $city_name
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
        rels = self.db.run_read(query_rels, {"city_name": self.city_name})
        for r in rels:
            # Pasamos p1_id y p2_id para la conexión y el resto en el dict rel_data
            self.graph.addEdge(r['p1_id'], r['p2_id'], r)
            
        output_dir = os.path.join(self.import_path, self.city_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{self.city_name}.gt")

        #graphtool tiene una función para guardar rápido en un archivo
        self.graph.g.save(output_file)
        print(f"[BuildGraph] Grafo guardado en {output_file}")

if __name__ == "__main__":
    connection = Neo4jConnection()
    ld = LoadDB(connection)
    cities = ld.listCities()

    print("=== CARGA DE GRAFOS GT ===")

    if not cities:
        print("No se encontraron ciudades en la base de datos.")
    
    print("\n=== OPCIONES ===")
    for i, city in enumerate(cities):
        print(f"{i + 1}. {city}")

    try:
        seleccion = int(input("\nElija una opción: "))
        if 1 <= seleccion <= len(cities):
            city_name = cities[seleccion - 1]
            print(f"\nConstruyendo grafo para {city_name}...")
            builder = BuildGraph(connection, city_name)
            builder.build()
        else:
            print("Selección no válida.")
    except ValueError:
        print("Entrada no válida. Por favor, ingrese un número.")

