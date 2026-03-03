# Este archivo parte del fichero test.csv y crea otro csv filtrandolo con una funcion concreta del recommender

import sys
import os
import csv
from datetime import datetime
from neo4j import GraphDatabase
from RouteGenerator import RouteGenerator
from RecommendationService import RecommendationService

class Predictor:

    def __init__(self):

        self.base_dir=os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir=os.path.join(self.base_dir,'..','dataset')

        #creamos la carptea donde se guardara el nuevo csv
        self.output_dir=os.path.join(self.base_dir,'..','predictions')
        os.makedirs(self.output_dir, exist_ok=True) 

        try:
            
            self.route_generator = RouteGenerator()
            self.recommender = RecommendationService(self.route_generator)            
           
            print("[PREDICTOR] Conexión exitosa a la base de datos Neo4j")

        except Exception as e:
            print(f"[PREDICTOR]Error al conectar a la base de datos Neo4j: {e}")
            raise
    
    def __str__(self):
        return "Predictor conectado a Neo4j"
    
    def cerrar_conexion(self):  
        if self.route_generator:
            self.route_generator.close()

    def _load_routes_from_csv(self, filepath):
        """
        Lee el csv linea por linea y agrupa las filas por trail_id.
        Devuelve un diccionario: { trail_id: [fila1, fila2, ...] }
        """
        if not os.path.exists(filepath):
            print(f"[PREDICTOR] El archivo {filepath} no existe.")
            return None
        
        routes = {}

        with open(filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                
                trail_id = row['trail_id']

                # si es la primera vez que vemos este trail_id, inicializamos la lista
                if trail_id not in routes:
                    routes[trail_id] = []
                    
                routes[trail_id].append(row)

        return routes
            
    def generate_predictions(self, user_id, context, steps, algorithm):
        print("[PREDICTOR] Generando predicciones con algoritmo:", algorithm)

        #Paso1: leemos el fichero test.csv        
    
        test_file=os.path.join(self.dataset_dir,'test.csv')

        #leemos el csv y agrupamos por trail_id
        print(f"[PREDICTOR] Leyendo rutas desde {test_file}...")
        routes = self._load_routes_from_csv(test_file)

        if not routes:
            print(f"[PREDICTOR] No se encontraron rutas en el archivo {test_file}.")
            return
        
        print(f"[PREDICTOR] Procesando {len(routes)} rutas para predicción...")
        print(f"[PREDICTOR] RUTAS: {list(routes.keys())}...")

        # Paso2: vamos ruta por ruta y aplicamos la función de predicción
        
        #antes de ir ruta por ruta creamos el nombre del csv
        city_name = self.route_generator.get_city()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{city_name}_{algorithm}_{timestamp}.csv"
        output_file = os.path.join(self.output_dir, filename)
        print(f"[PREDICTOR] El resultado se guardará en: {filename}")
        
        # Definimos el nuevo nombre dinámico
        filename = f"{city_name}_{algorithm}_{timestamp}.csv"
        output_file = os.path.join(self.output_dir, filename)
        print(f"[PREDICTOR] El resultado se guardará en: {filename}")

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(["trail_id", "step", "candidate_rank", "poi_id", "prediction"])

            #vamos ruta por ruta añadiendo info a prediction.csv
            for trail_id, trail_steps in routes.items():
                print("----------------------------------------------")
                print("------------RUTA:", trail_id, "----------------")
                print("----------------------------------------------")

                if not trail_steps:
                    continue
                
                # vamos poi a poi haciendo predicciones para el siguiente poi
                for i in range(len(trail_steps)-1):
                    print("----ANALIZANDO PASO:", i+1, "----")
                    current_step = trail_steps[i]
                    poi_id= current_step['poi_id']

                    route_user= trail_steps[0]['user_id']

                    #Paso2.1: obtenemos las coordenadas del poi actual
                    coordenadas= self.route_generator._get_poi_coordinates(poi_id)
                    if not coordenadas:
                        print(f"[PREDICTOR] No se pudieron obtener coordenadas para el POI {poi_id}. Saltando paso.")
                        continue
                    print(f"[PREDICTOR] Coordenadas del POI {poi_id}: {coordenadas}")
                    lat, lon = coordenadas

                    #Paso2.2: obtenemos los candidatos para la siguiente posicion según el algortimo
                    candidates = []

                    if algorithm == 'ratings':
                        candidates = self.recommender.getCandidates(
                            user_id=route_user,
                            lat=lat,
                            lon=lon,
                            context=context,
                            steps=steps,
                            algorithm_name=algorithm
                        )
                    
                    if not candidates:
                        print(f"[PREDICTOR] No se encontraron candidatos para la ruta {trail_id} en el paso {i+1}.")
                        continue


                    print(f"[PREDICTOR] CANDIDATOS ENCONTRADOS PARA RUTA {trail_id} PASO {i+1}: {[c['poi_id'] for c in candidates]}")
                    
                    #Paso2.3: escribimos los candidatos en el csv de salida

                    step_num = i+2
                    
                    for rank, candidate in enumerate(candidates, start=1):
                        rank_etiqueta= f"poi_{step_num}_{rank}"

                        writer.writerow([
                            trail_id,
                            step_num,
                            rank_etiqueta,
                            candidate['poi_id'],
                            f"{candidate['score']:.4f}"
                        ])

        print(f"[PREDICTOR] Predicciones guardadas en {output_file}.")                  
            
if __name__ == "__main__":

    predictor= Predictor()

    try:
        if len(sys.argv) != 5:
            print("Uso: python Predictor.py <user_id> <context> <steps> <algorithm>")
            print("Si no se proporciona el contexto y los pasos, se usarán valores por defecto.")
            sys.exit(1)
        user_id = sys.argv[1]
        context_arg = sys.argv[2] 
        steps = int(sys.argv[3])
        algorithm = sys.argv[4]

        if context_arg=="None":
            context=None

        print(f"[PREDICTOR] Iniciando predicciones para el usuario: {user_id}")
        predictor.generate_predictions(user_id, context, steps, algorithm)
    except Exception as e:
        print(f"[PREDICTOR] ¡ERROR FATAL!: {e}")
    finally:
        if predictor:
            predictor.cerrar_conexion()