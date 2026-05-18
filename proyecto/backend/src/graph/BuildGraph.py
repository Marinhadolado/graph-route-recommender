import graph_tool.all as gt
import os
import csv
from .GTGraph import GTGraph
from persistencia.Neo4jConnection import Neo4jConnection
from persistencia.LoadDB import LoadDB

class BuildGraph:
    def __init__(self, neo4j_client, city_name):
        if not isinstance(neo4j_client, Neo4jConnection):
            raise ValueError("The client must be an instance of Neo4jConnection.")
        self.db = neo4j_client
        self.city_name = city_name
        self.graph = GTGraph()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.train_file = os.path.join(base_dir, "..", "..", "dataset", "train.csv")
        self.import_path = os.path.join(base_dir, "..", "..", "..","import")
        os.makedirs(self.import_path, exist_ok=True)

    def build(self):
        """Gets the data from Neo4j and builds the graph in memory, then saves it to a file."""
        
        print(f"\n[Build Graph] Building subgraph for {self.city_name} based on train.csv...")

        if not os.path.exists(self.train_file):
            raise FileNotFoundError(f"[Build Graph] ERROR: The training file was not found in {self.train_file}. Make sure the dataset is in the correct folder!")
        
        print("[Build Graph] Extracting valid routes and POIs from train.csv...")
        train_routes = set()
        valid_pois = set()
        with open(self.train_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                train_routes.add(row['trail_id'])
                valid_pois.add(row['poi_id'])

        print(f"[Build Graph] Routes found: {len(train_routes)}")
        print(f"[Build Graph] Valid POIs found: {len(valid_pois)}")

        print(f"[Build Graph] Loading POIs")

        self.graph = GTGraph()

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
        total_nodes = 0
        pois = self.db.run_read(query_pois, {"city_name": self.city_name})
        for p in pois:
            if p['fsq_id'] in valid_pois:
                self.graph.addNode(p)
                total_nodes += 1

        print(f"[Build Graph] {total_nodes} valid POIs added to the graph (the ones that don't appear in train were discarded).")

        print(f"[Build Graph] Loading Relationships")

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
        
        loaded_rels = 0
        for r in rels:
            if str(r['trail_id']) in train_routes:
                exito =self.graph.addEdge(r['p1_id'], r['p2_id'], r)
                if exito:
                    loaded_rels += 1

        print(f"[Build Graph] {loaded_rels} valid relationships added (the ones that don't meet the criteria were discarded).")

        output_dir = os.path.join(self.import_path, self.city_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{self.city_name}.gt")
        if os.path.exists(output_file):
            print(f"[BuildGraph] The file {output_file} already exists and will be overwritten.")

        self.graph.g.save(output_file)
        print(f"[BuildGraph] Graph saved to {output_file}")

if __name__ == "__main__":
    connection = Neo4jConnection()
    ld = LoadDB(connection)
    cities = ld.list_cities()

    print("=== Loading GT Graphs ===")

    if not cities:
        print("No cities found in the database. Please run LoadDB.py first to populate the database with data.")
    
    print("\n=== OPTIONS ===")
    for i, city in enumerate(cities):
        print(f"{i + 1}. {city}")

    try:
        seleccion = int(input("\nChoose an option: "))
        if 1 <= seleccion <= len(cities):
            city_name = cities[seleccion - 1]
            print(f"\nBuilding graph for {city_name}...")
            builder = BuildGraph(connection, city_name)
            builder.build()
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input. Please enter a number.")

