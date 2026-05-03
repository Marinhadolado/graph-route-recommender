import graph_tool.all as gt
import os
import csv
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
        self.train_file = os.path.join(base_dir, "..", "..", "dataset", "train.csv")
        self.import_path = os.path.join(base_dir, "..", "..", "..","import")
        os.makedirs(self.import_path, exist_ok=True)

    def build(self):
        """Trae los datos de Neo4j y guarda en una carpeta el grafo."""
        
        print(f"\n[BuildGraph] Construyendo subgrafo para {self.city_name} basado en train.csv...")

        if not os.path.exists(self.train_file):
            raise FileNotFoundError(f"[BuildGraph] ERROR: No se encontró el archivo de entrenamiento en {self.train_file}. ¡Asegúrate de que el dataset esté en la carpeta correcta!")
        
        
        print(f"[BuildGraph] Leyendo train.csv...")

        #como estamos leyendo de un train.csv no vamos a tener todos los datos de los pois de rating, price...
        # lo qe vamos a hacer escargar las rutas del train.csv en un set para tener los pois que sí aparecen en el train.csv 
        # y luego cargar solo esos pois de la base de datos

        print("[BuildGraph] Extrayendo rutas y pois válidos del train.csv...")
        rutas_del_train = set()
        pois_validos_train = set()
        with open(self.train_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rutas_del_train.add(row['trail_id'])
                pois_validos_train.add(row['poi_id'])

        print(f"[BuildGraph] Rutas válidas encontradas: {len(rutas_del_train)}")
        print(f"[BuildGraph] POIs válidos encontrados: {len(pois_validos_train)}")

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
        nodos_totales = 0
        pois = self.db.run_read(query_pois, {"city_name": self.city_name})
        for p in pois:
            if p['fsq_id'] in pois_validos_train:
                self.graph.addNode(p)
                nodos_totales += 1

        print(f"[BuildGraph] {nodos_totales} POIs válidos agregados al grafo (se han descartado los que no aparecen en train).")

        print(f"[BuildGraph] Cargando Relaciones")

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
        
        aristas_añadidas = 0
        for r in rels:
            if str(r['trail_id']) in rutas_del_train:
                exito =self.graph.addEdge(r['p1_id'], r['p2_id'], r)
                if exito:
                    aristas_añadidas += 1

        print(f"[BuildGraph] {aristas_añadidas} relaciones válidas agregadas (se han descartado las que no cumplen con los criterios).")

        output_dir = os.path.join(self.import_path, self.city_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{self.city_name}.gt")
        if os.path.exists(output_file):
            print(f"[BuildGraph] Advertencia: El archivo {output_file} ya existe y será sobrescrito.")

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

