import os
import csv
import sys # para leer argumentos de la terminal
from neo4j import GraphDatabase

class Predictor:
    def __init__(self):
        uri= os.getenv("NEO4J_URI", "bolt://localhost:7999")
        user= os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        # creamos las carpetas para guardar los csv
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = os.path.join(base_dir, "..", "dataset")
        self.output_dir = os.path.join(base_dir, "predictions")
        os.makedirs(self.output_dir, exist_ok=True)

    def cerrar_conexion(self):
        self.driver.close()

    #METODO PRINCIPAL
    def generate_predictions(self, algorithm):
        print(f"[PREDICTION] Generando predicciones usando el algoritmo: {algorithm}")

        input_file = os.path.join(self.dataset_dir, "test.csv")
        if os.path.exists(input_file) is False:
            print(f"[PREDICTION] El archivo de entrada {input_file} no existe. Asegúrate de haberlo generado antes con DatasetGenerator.")
            return
        
        routes= self._load_test_routes(input_file)
        print(f"[PREDICTION] Cargando rutas de prueba desde {input_file}. Total rutas: {len(routes)}")

        output_file = os.path.join(self.output_dir, f"predictor_{algorithm}.csv")

        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(["trail_id", "poi_step", "poi_id","predicted_score", "algorithm"])

            #vamos ruta por ruta analizando sus opciones
            for trail_id, steps in routes.items():
                # Ordenamos los steps (poi_1, poi_2, poi_3...)
                # Extraemos el número del string "poi_X" para ordenar correctamente
                try:
                    sorted_steps = sorted(steps, key=lambda x: int(x['num_poi'].split('_')[1]))
                except:
                    # Si el formato no es poi_X, ordenamos por defecto
                    sorted_steps = steps

                for i in range(len(sorted_steps)-1):
                    # para cada paso, predecimos el siguiente POI
                    current_step = sorted_steps[i]
                    current_poi = current_step['poi_id']
                    candidates= self._get_recommendatios(current_poi, algorithm)
                
                    step_origin = current_step['num_poi']
                    step_destination = f"poi_{i+2}"

                    # escribimos el supuesto siguiente poi en el csv
                    for step, rank in enumerate(candidates, 1):
                        poi_candidate = step['poi_id']
                        predicted_score = step['predicted_score']

                        writer.writerow([trail_id, f"poi_{step_origin}{step_destination}", poi_candidate, predicted_score, algorithm])
                    
        print(f"[PREDICTION] Predicciones guardadas en {output_file}")

    def _load_test_routes(self, input_file):
        """Carga las rutas de prueba desde el archivo CSV de test.
        Devuelve un de diccionario con 'trail_id' y 'route con todos los datos del csv'.
        """
        routes = {}

        with open(input_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                t_id = row['trail_id']
                if t_id not in routes:
                    routes[t_id] = []
                routes[t_id].append(row)

        return routes
        
    def _get_recommendatios(self, current_poi, algorithm):
        return


if __name__ == "__main__":
    predictor = Predictor()

    try:
        if len(sys.argv) > 1:
            algorithm = sys.argv[1]
            predictor.generate_predictions(algorithm)
        else:
            print("[PREDICTION] Proporciona el nombre del algoritmo como argumento.")
            print("     -> Uso: python src/Predictor.py <nombre_algoritmo>")
            print("     -> Opciones de algoritmo: 'basico', 'score'")
    except Exception as e:
        print(f"[PREDICTION] Error durante la generación de predicciones: {e}")

    finally:
        predictor.cerrar_conexion()