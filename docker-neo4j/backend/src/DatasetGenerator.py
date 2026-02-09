# Este archivo genera los .csv necesarios para entrenar el modelo de predicción
# Este archivo es un scrit que deberá ser ejecutado manualemente 

import os
import csv
import sys
import random
from neo4j import GraphDatabase

class DatasetGenerator:
    def __init__(self):
        # Configuración de la conexión a Neo4j para el generador de rutas
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7999")
        user= os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()

            base_dir= os.path.dirname(os.path.abspath(__file__))
            self.output_dir= os.path.join(base_dir, "..", "dataset")
            os.makedirs(self.output_dir, exist_ok=True)
            print("[DATASET GENERATOR] Conexión exitosa a la base de datos Neo4j")

        except Exception as e:
            print(f"[DATASET GENERATOR] Error al conectar a la base de datos Neo4j: {e}")
            raise

    def __str__(self):
        return "DatasetGenerator conectado a Neo4j"

    def cerrar_conexion(self):  
        self.driver.close()

    def generate_dataset(self, num_trails, min_steps):
        print("[DATASET GENERATOR] Generando dataset...")

        print("[DATASET GENERATOR] PASO1: Consultando Neo4j para obtener las rutas válidas.")
        print("[DATASET GENERATOR] Criterios de selección:")
        print(f"   -> Usuarios con al menos {num_trails} rutas distintas.")
        print(f"   -> Cada ruta debe tener al menos {min_steps + 1} POIs ({min_steps} saltos).")

        # consultamos las rutas que hayan sido realizadas por usuarios con al menos 2 rutas
        # y que cada ruta tenga al menos 4 POIs(3 saltos)
        data = self._fetch_valid_trails(num_trails=num_trails, min_steps=min_steps)

        if not data:
            print("[DATASET GENERATOR] No se encontraron rutas válidas en la base de datos.")
            return
        
        print(f"[DATASET GENERATOR] PASO2: Escribiendo dataset en {self.output_dir}/dataset.csv")
        # Escribimos los datos en un archivo CSV
        output_file = os.path.join(self.output_dir, "dataset.csv")
        self._write_to_csv(output_file, data)

        print("[DATASET GENERATOR] PASO3: Split del dataset en train y test (80%-20%)")
        self._split_dataset(output_file)

    #FUNCIONES AUXILIARES PARA GENERAR EL DATASET
    def _fetch_valid_trails(self, num_trails, min_steps):
        # QUERY EXPLICADA:
        # Filtramos usuarios que tengan al menos {num_trails} rutas distintas (trail_id).
        # Filtramos rutas que tengan al menos {min_steps} POIs
        # Ordenamos cronológicamente.
                
        query = f"""
        MATCH (p1:POI)-[r:VISITED]->(p2:POI)
        WITH r.user_id AS user, count(DISTINCT r.trail_id) AS num_trails
        WHERE num_trails >= $num_trails
        
        MATCH (p1:POI)-[r:VISITED]->(p2:POI)
        WHERE r.user_id = user
        
        WITH user, r.trail_id AS trail, collect(r) AS rels
        WHERE size(rels) >= $min_steps
        
        UNWIND rels AS r
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
            result = session.run(query, num_trails=num_trails, min_steps=min_steps)
            
            #convertimos el resultado a lista para poder mirar alante y atras
            result_list = list(result)

            if not result_list:
                return []

            counter=1

            for i, record in enumerate(result_list):
                row= dict(record)

                current_row= {
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
                    'conditions': row['poi1_conditions']
                }

                data.append(current_row)

                counter += 1

                if i == (len(result_list)-1):
                    last_record= True
                else:
                    last_record= False

                last_poi_route= False


                if not last_record:
                    # si no es el ultimo poi, comprobamos si el siguiente es de otra ruta
                    next_trail_id = result_list[i+1]['trail_id']
                    if next_trail_id != row['trail_id']:
                        last_poi_route= True

                if last_poi_route or last_record:
                    # añadimos el ultimo poi de la ruta
                    last_row= {
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
                        'conditions': row['poi2_conditions']
                    }

                    data.append(last_row)

                    counter=1  # reiniciamos el contador para la siguiente ruta            
            
        return data
    
    def _write_to_csv(self, output_file, data):
        fieldnames = [
            'trail_id', 'user_id', 'num_poi', 'poi_id',
             'timestamp','rating',
            'temp', 'precip', 'windspeed', 'preciptype', 'conditions'
        ]
        
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"[DATASET GENERATOR] Dataset escrito correctamente en {output_file}")
    
    def _split_dataset(self, input_file):
        train_file = os.path.join(self.output_dir, "train.csv")
        test_file = os.path.join(self.output_dir, "test.csv")
        
        routes_dict = {} # ejemplo { trail_id1: [row1, row2,...], trail_id2: [...] }
        routes_timestamps = {}
        header = []

        # Leer el archivo y agrupar por 'trail_id' en un diccionario routes_dict
        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Guardamos la cabecera
            header = reader.fieldnames
            
            for row in reader:
                t_id = row['trail_id']
                timestamp = row['timestamp']

                if t_id not in routes_dict:
                    routes_dict[t_id] = []
                    routes_timestamps[t_id] = timestamp
                
                routes_dict[t_id].append(row)
        
        # Obtener lista de rutas
        sorted_trail_ids = sorted(routes_timestamps, key=routes_timestamps.get, reverse=True)        
        
        # Calcular el punto de corte
        total_routes = len(sorted_trail_ids)
        split_idx = int(0.2 * total_routes)
        
        test_ids = sorted_trail_ids[:split_idx]
        train_ids = sorted_trail_ids[split_idx:]
        
        print(f"   -> Total Rutas: {total_routes}")
        print(f"   -> Train Rutas: {len(train_ids)}")
        print(f"   -> Test Rutas:  {len(test_ids)}")
        
        # 4. Escribir archivos
        self._write_split_file(train_file, header, train_ids, routes_dict)
        self._write_split_file(test_file, header, test_ids, routes_dict)

        print(f"[DATASET GENERATOR] Archivos generados en {self.output_dir}")

    def _write_split_file(self, filepath, header, trail_ids, routes_dict):
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for t_id in trail_ids:
                writer.writerows(routes_dict[t_id])

    def delete_existing_files(self):
        print("[DATASET GENERATOR] Eliminando archivos existentes en el directorio de dataset...")

        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"   -> Archivo eliminado: {file_path}")
            except Exception as e:
                print(f"[DATASET GENERATOR] Error al eliminar el archivo {file_path}: {e}")

if __name__ == "__main__":
    generate_dataset = DatasetGenerator()
    generate_dataset.delete_existing_files()

    try:
        if len(sys.argv) > 2:
            min_steps = int(sys.argv[1])
            num_trails = int(sys.argv[2])
            generate_dataset.generate_dataset(num_trails=num_trails, min_steps=min_steps)
        else:
            print("[DATASET GENERATOR] Proporciona el número mínimo de pasos y el número mínimo de rutas por usuario como argumentos.")
            print("     -> Uso: python src/DatasetGenerator.py <min_steps> <num_trails>")
            print("     -> Ejemplo: python src/DatasetGenerator.py 3 2")
    
    except Exception as e:
        print(f"[DATASET GENERATOR] Error durante la generación del dataset: {e}")

    finally:
        generate_dataset.cerrar_conexion()