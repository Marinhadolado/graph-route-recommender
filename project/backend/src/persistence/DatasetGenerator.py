import os
import csv
import sys
import random
from .Neo4jConnection import Neo4jConnection

class DatasetGenerator:
    def __init__(self, db_connection):
        if not isinstance(db_connection, Neo4jConnection):
            raise TypeError("The argument db_connection must be an instance of Neo4jConnection")

        self.driver = db_connection.driver
        try:

            base_dir= os.path.dirname(os.path.abspath(__file__))
            self.output_dir= os.path.join(base_dir, "../..", "dataset")
            os.makedirs(self.output_dir, exist_ok=True)
            print("[Dataset Generator] Connection successful to the Neo4j database")

        except Exception as e:
            print(f"[Dataset Generator] Error connecting to the Neo4j database: {e}")
            raise

    def __str__(self):
        if self.driver:
            status = "Connected"
        else:
            status = "Disconnected"
        return f"Neo4jConnection {status}"

    def close_connection(self):  
        self.driver.close()

    def generate_dataset(self, num_trails, min_steps, city_name):
        print("[Dataset Generator] Generating dataset...")

        print("[Dataset Generator] Selection criteria:")
        print(f"   -> Users with at least {num_trails} distinct routes.")
        print(f"   -> Each route must have at least {min_steps + 1} POIs ({min_steps} jumps).")

        data = self._fetch_valid_trails(num_trails=num_trails, min_steps=min_steps, city_name=city_name)

        if not data:
            print("[Dataset Generator] No valid routes found in the database.")
            return
        
        print(f"[Dataset Generator] Writing dataset to {self.output_dir}/dataset.csv")
        output_file = os.path.join(self.output_dir, "dataset.csv")
        self._write_to_csv(output_file, data)

        print("[Dataset Generator] Split the dataset in train and test (80%-20%)")
        self._split_dataset(output_file)

    def _fetch_valid_trails(self, num_trails, min_steps, city_name):
        query = """
        MATCH (p1:POI)-[r:VISITED]->()
        WHERE p1.city = $city_name
        WITH r.user_id AS user_id, r.trail_id AS trail_id, collect(r) AS rels
        WHERE size(rels) >= $min_steps
        
        WITH user_id, collect({trail_id: trail_id, rels: rels}) AS user_trails
        WHERE size(user_trails) >= $num_trails
        
        UNWIND user_trails AS ut
        UNWIND ut.rels AS r
        
        RETURN 
            r.trail_id AS trail_id,
            r.user_id AS user_id,
            
            startNode(r).fsq_id AS poi1_id,     
            endNode(r).fsq_id AS poi2_id,      
            
            startNode(r).rating AS poi1_rating,
            endNode(r).rating AS poi2_rating,
            
            r.p1_timestamp AS poi1_timestamp,
            r.p2_timestamp AS poi2_timestamp,
            
            r.p1_temp AS poi1_temp,
            r.p2_temp AS poi2_temp,
            
            r.p1_precip AS poi1_precip,
            r.p2_precip AS poi2_precip,
            
            r.p1_windspeed AS poi1_windspeed,
            r.p2_windspeed AS poi2_windspeed,
            
            r.p1_preciptype AS poi1_preciptype,
            r.p2_preciptype AS poi2_preciptype,
            
            r.p1_conditions AS poi1_conditions,
            r.p2_conditions AS poi2_conditions
            
        ORDER BY user_id, trail_id, poi1_timestamp ASC
        """
        
        data = []
        with self.driver.session() as session:
            result = session.run(query, num_trails=num_trails, min_steps=min_steps, city_name=city_name)
            result_list = list(result)

            if not result_list:
                return []

            current_trail = None
            last_added_poi = None
            counter = 1

            for record in result_list:
                row = dict(record)
                
                if row['trail_id'] != current_trail:
                    current_trail = row['trail_id']
                    last_added_poi = None
                    counter = 1

                if last_added_poi != row['poi1_id']:
                    data.append({
                        'trail_id': row['trail_id'],
                        'user_id': row['user_id'],
                        'num_poi': f"poi_{counter}",
                        'poi_id': row['poi1_id'],
                        'rating': row['poi1_rating'],
                        'timestamp': row['poi1_timestamp'],
                        'temp': row['poi1_temp'],
                        'precip': row['poi1_precip'],
                        'windspeed': row['poi1_windspeed'],
                        'preciptype': row['poi1_preciptype'],
                        'conditions': row['poi1_conditions'],
                        'city': city_name
                    })
                    counter += 1

                data.append({
                    'trail_id': row['trail_id'],
                    'user_id': row['user_id'],
                    'num_poi': f"poi_{counter}",
                    'poi_id': row['poi2_id'],
                    'rating': row['poi2_rating'],
                    'timestamp': row['poi2_timestamp'],
                    'temp': row['poi2_temp'],
                    'precip': row['poi2_precip'],
                    'windspeed': row['poi2_windspeed'],
                    'preciptype': row['poi2_preciptype'],
                    'conditions': row['poi2_conditions'],
                    'city': city_name
                })
                counter += 1
                last_added_poi = row['poi2_id']     
                
        # --- Métricas del dataset depurado (FINAL) ---
        pois_finales = {row['poi_id'] for row in data}
        rutas_finales = {row['trail_id'] for row in data}
        usuarios_finales = {row['user_id'] for row in data}
        # pasos de ruta = nº de transiciones = (nº de POIs en cada ruta - 1) sumado
        from collections import Counter
        pasos_por_ruta = Counter(row['trail_id'] for row in data)
        pasos_finales = sum(max(0, n - 1) for n in pasos_por_ruta.values())

        print("========== DATASET FINAL (tras depuración) ==========")
        print(f"[FINAL] POIs distintos:   {len(pois_finales)}")
        print(f"[FINAL] Pasos de ruta:    {pasos_finales}")
        print(f"[FINAL] Rutas válidas:    {len(rutas_finales)}")
        print(f"[FINAL] Usuarios:         {len(usuarios_finales)}")
        print("=====================================================")

        return data      
            
        return data
    
    def _write_to_csv(self, output_file, data):
        fieldnames = [
            'trail_id', 'user_id', 'num_poi', 'poi_id',
             'timestamp','rating',
            'temp', 'precip', 'windspeed', 'preciptype', 'conditions', 'city'
        ]
        
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"[DATASET GENERATOR] Dataset written successfully in {output_file}")
    
    def _split_dataset(self, input_file):
        train_file = os.path.join(self.output_dir, "train.csv")
        test_file = os.path.join(self.output_dir, "test.csv")
        
        routes_dict = {}
        routes_timestamps = {}
        header = []

        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            header = reader.fieldnames
            
            for row in reader:
                t_id = row['trail_id']
                timestamp = row['timestamp']

                if t_id not in routes_dict:
                    routes_dict[t_id] = []
                    routes_timestamps[t_id] = timestamp
                
                routes_dict[t_id].append(row)
        
        sorted_trail_ids = sorted(routes_timestamps, key=routes_timestamps.get, reverse=True)        
        
        total_routes = len(sorted_trail_ids)
        split_idx = int(0.2 * total_routes)
        
        test_ids = sorted_trail_ids[:split_idx]
        train_ids = sorted_trail_ids[split_idx:]
        
        print(f"   -> Total routes: {total_routes}")
        print(f"   -> Train routes: {len(train_ids)}")
        print(f"   -> Test routes:  {len(test_ids)}")
        
        self._write_split_file(train_file, header, train_ids, routes_dict)
        self._write_split_file(test_file, header, test_ids, routes_dict)

        print(f"[Dataset Generator] Files generated in {self.output_dir}")

    def _write_split_file(self, filepath, header, trail_ids, routes_dict):
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for t_id in trail_ids:
                writer.writerows(routes_dict[t_id])

    def delete_existing_files(self):
        print("[Dataset Generator] Deleting existing files in the dataset directory...")

        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"   -> File deleted: {file_path}")
            except Exception as e:
                print(f"[Dataset Generator] Error deleting the file {file_path}: {e}")

if __name__ == "__main__":
    connection = Neo4jConnection()
    generate_dataset = DatasetGenerator(connection)
    generate_dataset.delete_existing_files()

    try:
        if len(sys.argv) > 3:
            min_steps = int(sys.argv[1])
            num_trails = int(sys.argv[2])
            city_name = sys.argv[3]
            generate_dataset.generate_dataset(num_trails=num_trails, min_steps=min_steps, city_name=city_name)
        else:
            print("[Dataset Generator] Provide the minimum number of steps and the minimum number of routes per user as arguments.")
            print("     -> Usage: python src/DatasetGenerator.py <min_steps> <num_trails> <city_name>")
            print("     -> Example: python src/DatasetGenerator.py 3 2 NYC")
    
    except Exception as e:
        print(f"[Dataset Generator] Error during dataset generation: {e}")

    finally:
        generate_dataset.close_connection()