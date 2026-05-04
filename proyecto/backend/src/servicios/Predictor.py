import sys
import os
import csv
import json
from datetime import datetime
from grafo.GraphRepository import GraphRepository
from servicios.RecommendationService import RecommendationService
from persistencia.Neo4jConnection import Neo4jConnection

class Predictor:

    def __init__(self, city_name):

        self.base_dir=os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir=os.path.join(self.base_dir,'..','..', 'dataset')
        self.city_name = city_name

        #creamos la carptea donde se guardara el nuevo csv
        self.output_dir=os.path.join(self.base_dir,'..','..','predictions')
        os.makedirs(self.output_dir, exist_ok=True) 

        try:
            self.neo4j_client = Neo4jConnection()
            self.graph_repository = GraphRepository(city_name)
            self.recommender = RecommendationService()            
           
            print("[PREDICTOR] Conexión exitosa a la base de datos Neo4j")

        except Exception as e:
            print(f"[PREDICTOR]Error al conectar a la base de datos Neo4j: {e}")
            raise
    
    def __str__(self):
        return "Predictor configurado para " + self.city_name
    
    def cerrar_conexion(self):
        if self.neo4j_client:
            self.neo4j_client.close()

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

        grafo = self.graph_repository.getGraph()

        #Paso1: leemos el fichero test.csv        
        test_file=os.path.join(self.dataset_dir,'test.csv')

        #antes de nada nos aseguramos que los datos del test.csv son de la misma ciudad que el city_name que se ha pasado por argumento
        with open(test_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                    if row['poi_id'] not in grafo.id_map:
                        print(f"[PREDICTOR] ERROR: El archivo {test_file} contiene datos de la ciudad {row['city']} pero se esperaba {self.city_name}.")
                        return
                    break 
                
        print(f"[PREDICTOR] Leyendo rutas desde {test_file}...")
        routes = self._load_routes_from_csv(test_file)

        if not routes:
            print(f"[PREDICTOR] No se encontraron rutas en el archivo {test_file}.")
            return
        
        #USUARIO
        #si el usuario no existe en la bd error
        history = grafo.getUserHistory(user_id)
        if not history:
            print(f"[PREDICTOR] El usuario {user_id} no tiene historial en el grafo. No se pueden generar predicciones.")
            return
        
        print(f"[PREDICTOR] Procesando {len(routes)} rutas para predicción...")
        print(f"[PREDICTOR] RUTAS: {list(routes.keys())}...")

        # Paso2: vamos ruta por ruta y aplicamos la función de predicción
        #antes de ir ruta por ruta creamos el nombre del csv
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.city_name}_{algorithm}_{timestamp}.csv"
        output_file = os.path.join(self.output_dir, filename)

        print(f"[PREDICTOR] El resultado se guardará en: {filename}")
        
        # Definimos el nuevo nombre
        filename = f"{self.city_name}_{algorithm}_{timestamp}.csv"
        output_file = os.path.join(self.output_dir, filename)
        print(f"[PREDICTOR] El resultado se guardará en: {filename}")

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(["trail_id", "step", "candidate_rank", "poi_id", "prediction"])

            #vamos ruta por ruta añadiendo info a prediction.csv
            for trail_id, trail_steps in routes.items():
                if not trail_steps:
                    continue

                recomendados_en_ruta = set()
                
                # vamos poi a poi haciendo predicciones para el siguiente poi
                for i in range(len(trail_steps)-1):
                    current_step = trail_steps[i]
                    poi_id= current_step['poi_id']

                    if poi_id not in grafo.id_map:
                        #print(f"[PREDICTOR] El POI {poi_id} no se encuentra en el grafo. Saltando este paso.")
                        continue

                    #entre los candidatos no puede haber pois que haya visitado en
                    #su historial ni que hayan sido recomendados en pasos anteriores de la misma ruta
                    pois_evitar= set(history).union(recomendados_en_ruta)

                    #print(f"[PREDICTOR] Generando candidatos para el POI {poi_id} en la ruta {trail_id} (Paso {i+1}/{len(trail_steps)-1})...")
                    # Obtenemos candidatos
                    candidates = self.recommender.getCandidates(
                        current_poi_id=poi_id,
                        user_id=user_id,
                        context=context,
                        steps=steps,
                        algorithm_name=algorithm,
                        pois_evitar=pois_evitar,
                        graph=grafo
                    )
                    
                    if not candidates:
                        continue

                    for c in candidates:
                        recomendados_en_ruta.add(c['poi_id'])

                    step_num = i + 2
                    for rank, candidate in enumerate(candidates, start=1):
                        rank_etiqueta = f"poi_{step_num}_{rank}"
                        writer.writerow([
                            trail_id,
                            step_num,
                            rank_etiqueta,
                            candidate['poi_id'],
                            f"{candidate['prediction']:.4f}"
                        ])
        print(f"[PREDICTOR] Predicciones guardadas en {output_file}.")                  
            
if __name__ == "__main__":

    try:
        if len(sys.argv) != 6:
            print("Uso: python Predictor.py <user_id> <context> <steps> <algorithm> <city_name>")
            print("Si no se proporciona el contexto y los pasos, se usarán valores por defecto.")
            sys.exit(1)
        user_id = sys.argv[1]
        context_arg = sys.argv[2] 
        steps = int(sys.argv[3])
        algorithm = sys.argv[4]
        city_name = sys.argv[5]

        if context_arg=="None":
            context=None
        else:
            try:
                context = json.loads(context_arg)
            except json.JSONDecodeError:
                print(f"\n [PREDICTOR] ERROR El contexto introducido no es un JSON válido.")
                print(f"Ejemplo: '{{\"conditions\": \"Clear\", \"rating\": 8.0}}'\n")
                sys.exit(1)


        predictor= Predictor(city_name)
        print(f"[PREDICTOR] Iniciando predicciones para el usuario: {user_id}")

        predictor.generate_predictions(user_id, context, steps, algorithm)
        if predictor:
            predictor.cerrar_conexion()
    except Exception as e:
        print(f"[PREDICTOR] ¡ERROR FATAL!: {e}")