import os
import sys
import pandas as pd
from datetime import datetime
from .Neo4jConnection import Neo4jConnection


class LoadDB:
    """Handles database purging, indexing, and transactional batch data loading into Neo4j."""

    def __init__(self, db_connection):
        if not isinstance(db_connection, Neo4jConnection):
            raise TypeError("The provided db_connection must be an instance of Neo4jConnection.")
            
        self.db= db_connection
        self.driver = db_connection.driver
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.import_path= os.path.join(base_dir, "../../../import")

    def clear_database(self):
        """Completely purges all nodes and relationships using controlled transactional batches."""
        confirm = input("\n  Are you sure you want to PURGE the entire database? (y/N): ").lower()
        if confirm != 'y':
            print(" Operation cancelled.")
            return
        
        print("[LoadDB] Purging the database...")
        
        query = "MATCH (n) WITH n LIMIT 1000 DETACH DELETE n RETURN count(n) AS deleted"
        
        try:
            with self.driver.session() as session:
                total_deleted = 0
                while True:
                    result = session.run(query)
                    deleted_count = result.single().value()
                    
                    if deleted_count == 0:
                        break
                    
                    total_deleted += deleted_count
                    print(f"   -> Deleted {total_deleted} nodes...", end='\r')
            
            print(f"\n[LoadDB] Purging finished. {total_deleted} elements were deleted.")
            
        except Exception as e:
            print(f"\n[LoadDB] Error while purging the database: {e}")

    def create_indexes(self):
        """ Creates necessary indexes for efficient querying of POIs and Users."""
        print("[LoadDB] Creating Neo4j indexes...")
        with self.driver.session() as session:
            session.run("CREATE INDEX IF NOT EXISTS FOR (p:POI) ON (p.fsq_id);")
            session.run("CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.user_id);")

    def list_cities(self):
        """ Lists available cities based on the directory structure in the import path."""
        if not os.path.exists(self.import_path):
            os.makedirs(self.import_path, exist_ok=True)
            return []
        
        cities= []
        
        all_cities = os.listdir(self.import_path)

        for city in all_cities:
            full_path= os.path.join(self.import_path, city) 

            if os.path.isdir(full_path):
                cities.append(city)

        return cities
    
    @staticmethod
    def time_segment(iso_str):
        """ Derives the time segment (Weekday/Weekend + part of day) from an ISO timestamp
        that still carries its local UTC offset (e.g. '2017-10-14 08:58:00+09:00'). """
        if not iso_str:
            return ''
        try:
            dt = datetime.fromisoformat(str(iso_str))
        except ValueError:
            return ''
        part = ("EarlyMorning" if dt.hour < 6 else
                "Morning"      if dt.hour < 12 else
                "Afternoon"    if dt.hour < 18 else
                "Night")
        day = "Weekend" if dt.weekday() >= 5 else "Weekday"

        return f"{day}_{part}"

    def loadPOIs(self, filepath, city_name):
        """ Charges POI nodes into Neo4j from a CSV file using batch transactions. The CSV is read in chunks and data is cleaned and transformed before insertion."""

        f = pd.read_csv(filepath, dtype=str)

        data = f.fillna("").to_dict('records')

        query = """
        UNWIND $batch AS row

        CALL (row){
            WITH row WHERE row.fsq_id IS NOT NULL AND toFloat(row.latitude) <> -1.0 AND toFloat(row.longitude) <> -1.0
            MERGE (p:POI {fsq_id: row.fsq_id})
            SET
                p.latitude = CASE WHEN row.latitude <> '' THEN toFloat(row.latitude) END,
                p.longitude = CASE WHEN row.longitude <> '' THEN toFloat(row.longitude) END,
                p.category = row.category,
                p.price = CASE WHEN row.price <> '' THEN toInteger(row.price) END,
                p.rating = CASE WHEN row.rating <> '' THEN toFloat(row.rating) END,
                p.total_ratings = CASE WHEN row.total_ratings <> '' THEN toInteger(row.total_ratings) END,
                p.total_tips = CASE WHEN row.total_tips <> '' THEN toInteger(row.total_tips) END,
                p.Weekday_EarlyMorning = CASE WHEN row.Weekday_EarlyMorning <> '' THEN toInteger(row.Weekday_EarlyMorning) END,
                p.Weekday_Morning = CASE WHEN row.Weekday_Morning <> '' THEN toInteger(row.Weekday_Morning) END,
                p.Weekday_Afternoon = CASE WHEN row.Weekday_Afternoon <> '' THEN toInteger(row.Weekday_Afternoon) END,
                p.Weekday_Night = CASE WHEN row.Weekday_Night <> '' THEN toInteger(row.Weekday_Night) END,
                p.Weekend_EarlyMorning = CASE WHEN row.Weekend_EarlyMorning <> '' THEN toInteger(row.Weekend_EarlyMorning) END,
                p.Weekend_Morning = CASE WHEN row.Weekend_Morning <> '' THEN toInteger(row.Weekend_Morning) END,
                p.Weekend_Afternoon = CASE WHEN row.Weekend_Afternoon <> '' THEN toInteger(row.Weekend_Afternoon) END,
                p.Weekend_Night = CASE WHEN row.Weekend_Night <> '' THEN toInteger(row.Weekend_Night) END,
                p.category_lvlFs = row.category_lvlFs,
                p.city = $cityName
        } IN TRANSACTIONS;
        """

        print(f"    Procesando {len(data)} POIs...")
        chunck_size= 10000 
        processed= 0

        with pd.read_csv(filepath, dtype=str, chunksize=chunck_size) as reader:
            with self.driver.session() as session:

                for chunck in reader:
                    chunck = chunck.fillna("")

                    batch_data = chunck.to_dict('records')

                    session.run(query, batch=batch_data, cityName=city_name)

                    processed+= len(batch_data)

                    print(f"   -> Processed {processed} POIs...", end='\r')

        return processed

    def loadTrails(self, filepath, city_name):
        """ Charges trail relationships into Neo4j from a CSV file. The CSV is read in chunks, cleaned, and transformed to create VISITED relationships between POIs with properties derived from the original data.   """  
        
        df = pd.read_csv(filepath, sep=';', dtype=str)
        
        print(f"   -> Archivo leído ({len(df)} filas). Preparando lógica de enlaces...")

        df['p1_time_segment'] = df['timestamp'].apply(LoadDB.time_segment)

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        numeric_cols = ['temp', 'precip', 'windspeed']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)                                                                                               

        df['next_venue_id'] = df['venue_id'].shift(-1)
        df['next_timestamp'] = df['timestamp'].shift(-1)
        df['next_user_id'] = df['user_id'].shift(-1)
        df['next_trail_id'] = df['trail_id'].shift(-1)

        cols_props = ['temp', 'precip', 'windspeed', 'conditions', 'preciptype']
        for col in cols_props:
            if col in df.columns:
                df[f'next_{col}'] = df[col].shift(-1)

        valid_rows = (df['user_id'] == df['next_user_id']) & \
                     (df['trail_id'] == df['next_trail_id']) & \
                     (df['venue_id'] != df['next_venue_id']) 

        df = df[valid_rows].copy()

        df['time_diff_min'] = (df['next_timestamp'] - df['timestamp']).dt.total_seconds() / 60.0

        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        df['next_timestamp'] = df['next_timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

        df = df.where(pd.notnull(df), None)

        query = """
        UNWIND $batch AS row
        
        MATCH (p1:POI {fsq_id: row.venue_id})
        MATCH (p2:POI {fsq_id: row.next_venue_id})
        
        MERGE (u:User {user_id: toString(row.user_id)})
        
        CREATE (p1)-[v:VISITED {
            user_id: toString(row.user_id),
            trail_id: toString(row.trail_id),
            
            p1_timestamp: row.timestamp,
            p1_temp: toFloat(row.temp),
            p1_precip: toFloat(row.precip),
            p1_windspeed: toFloat(row.windspeed),
            p1_conditions: row.conditions,
            p1_preciptype: CASE WHEN row.preciptype IS NULL THEN '' ELSE toString(row.preciptype) END,
            p1_time_segment: CASE WHEN row.p1_time_segment IS NULL THEN '' ELSE toString(row.p1_time_segment) END,

            p2_timestamp: row.next_timestamp,
            p2_temp: toFloat(row.next_temp),
            p2_precip: toFloat(row.next_precip),
            p2_windspeed: toFloat(row.next_windspeed),
            p2_conditions: row.next_conditions,
            p2_preciptype: CASE WHEN row.next_preciptype IS NULL THEN '' ELSE toString(row.next_preciptype) END,
            
            time_diff_min: toFloat(row.time_diff_min)
        }]->(p2)
        """

        batch_size = 5000
        total = len(df)
        print(f"    Processing {total} relationships(pre-filtered)...")

        with self.driver.session() as session:
            for start in range(0, total, batch_size):
                end = start + batch_size
                batch = df.iloc[start:end].to_dict('records')
                session.run(query, batch=batch)
                print(f"      Progress: {end}/{total}", end='\r')

        print("")
        return total

    def load_city(self, city_name):
        print(f"[LoadData] --------- Loading data from city {city_name}---------")

        city_dir = os.path.join(self.import_path, city_name)
        if not os.path.exists(city_dir):
            print(f"[LoadData] ERROR the directory does not exist: {city_dir}")
            return

        city_files= os.listdir(city_dir)
        pois_file=None
        trail_file=None
        
        for file in city_files:

            if file == "pois.csv":
                pois_file= file
            elif file== "trail_train.csv":
                trail_file= file
            
        if pois_file is None or trail_file is None:
            print(f"[LoadDB] ERROR: Missing files for city {city_name}")
            print("       Required files: 'pois.csv' and 'trail_train.csv'")
            return
        
        self.clear_database()

        self.create_indexes()

        print("[LoadDB] Loading nodes...")
        num_pois=self.loadPOIs(os.path.join(city_dir, pois_file), city_name)

        print("[LoadDB] Loading relationships...")
        num_rels=self.loadTrails(os.path.join(city_dir, trail_file), city_name)

        print("[LoadDB] Data loading completed.")
        print(f"[LoadDB] With {num_pois} pois and {num_rels} previousrelationships")

if __name__ == "__main__":
    connection = Neo4jConnection()
    ld= LoadDB(connection)
    cities= ld.list_cities()

    print("=== Data Loading in Neo4j ===")

    if not cities:
        print(f"The directory {ld.import_path} does not contain any city data.")
        exit()

    print("\n=== OPTIONS ===")
    for i, city in enumerate(cities):
        print(f"{i + 1}. {city}")

    limpiar = len(cities) + 1
    print(f"{limpiar}. ONLY Clear the Database (no loading)")

    try:
        seleccion = int(input("\n> Choose an option: ")) - 1
        if 0 <= seleccion < len(cities):
            ld.load_city(cities[seleccion])
        elif seleccion == limpiar - 1:
            ld.clear_database()
        else:
            print(" No valid option.")
    except ValueError:
        print("Please enter a number.")

