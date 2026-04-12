from ranx import Qrels, Run, evaluate
from servicios.RecommendationService import RecommendationService
from persistencia.LoadDB import LoadDB
import os
import csv
import glob

class Evaluator:

    def __init__(self, city_name, algorithm_name):
        self.city_name = city_name
        self.algorithm_name = algorithm_name
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = os.path.join(self.base_dir, '..', '..', 'dataset')
        self.predictions_dir = os.path.join(self.base_dir, '..', '..', 'predictions')   

    def _load_Qrel(self):

        #primero obtenemos la ruta y el archivo test.csv
        test_file = os.path.join(self.dataset_dir, 'test.csv')
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"[Evaluator] No se encuentra {test_file}")
        
        #procedemos a llenar el diccionario 
        qrel_dict = {}

        with open(test_file, mode='r', encoding='utf-8') as f:

            # se usa dict reader para no cargar todo el archivo e ir leyendo línea por línea
            reader= csv.DictReader(f)

            #variables para control del bucle 
            prev_trail_id = None
            step_counter = 1

            for row in reader:
                current_trail_id = row['trail_id']
                current_poi_id = row['poi_id']

                if current_trail_id ==prev_trail_id:
                    # si estamos aun en un paso de la ruta aumentamos el numero de pasos
                    step_counter += 1

                    query_id = f"{current_trail_id}_{step_counter}"
                    qrel_dict[query_id] = {current_poi_id: 1} # se asigna relevancia 1 a los POIs que aparecen en el test.csv
                else:
                    # si hemos cambiado de ruta, reiniciamos el contador de pasos y actualizamos el trail_id previo
                    step_counter = 1
                    prev_trail_id = current_trail_id

                    #nunca se guarda el paso 1porque no hay predicciones para ese primer paso


        return qrel_dict
    
    def _load_run(self):

        #como en predictions el nombre se genera con la fecha
        #primero buscamos los archivos del algoritmo y la ciudad
        search_pattern = os.path.join(self.predictions_dir, f"{self.city_name}_{self.algorithm_name}_*.csv")
        #la libreria blob nos permite aplicar el filtro de *
        archivos_prediccion = glob.glob(search_pattern)

        if not archivos_prediccion:
            raise FileNotFoundError(f"[Evaluator] No se encontraron archivos de predicción para {self.city_name} y {self.algorithm_name}")
        
        latest_file = max(archivos_prediccion, key=os.path.getctime)
        print(f"[Evaluator] Archivo de predicción encontrado: {os.path.basename(latest_file)}")

        run_dict = {}
        with open(latest_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                trail_id = row['trail_id']
                step_number = row['step']
                poi_id = row['poi_id']

                prediction = float(row['prediction']) # se asume que la predicción es un valor numérico

                query_id = f"{trail_id}_{step_number}"
                if query_id not in run_dict:
                    run_dict[query_id] = {}

                run_dict[query_id][poi_id] = prediction

        return run_dict
    
    def evaluate(self):

        qrels_dict= self._load_Qrel()
        print(f"[Evaluator] Qrels cargados: {len(qrels_dict)} consultas")
        print("[Evaluator] 5 primeros elementos del qrels dict:")
        for i, (query_id, prediction) in enumerate(qrels_dict.items()):
            print(f"Query ID: {query_id} | Prediction: {prediction}")
            if i >= 5: 
                break

        run_dict = self._load_run()
        print(f"\n[Evaluator] Run cargado: {len(run_dict)} consultas")
        print("[Evaluator] 5 primeros elementos del run dict:")
        for i, (query_id, prediction) in enumerate(run_dict.items()):
            print(f"Query ID: {query_id} | Prediction: {prediction}")
            if i >= 5: 
                break

        qrels = Qrels(qrels_dict)
        run = Run(run_dict, name=f"{self.city_name}_{self.algorithm_name}")
        
        #hit rate es la métrica para saber si el poi del qrels aparece entre las k primeras poisibilidades del run
        metricas = ["hit_rate@1", "hit_rate@5", "hit_rate@10"]

        evaluacion = evaluate(qrels, run, metricas, make_comparable=True)

        print(f"\n RESULTADOS PARA: {self.algorithm_name.upper()}")
        print("-" * 30)
        for metrica, valor in evaluacion.items():
            print(f"| {metrica.upper().ljust(15)} | {valor:.4f} |")
        print("-" * 30)

if __name__ == "__main__":

    #obtenemos las ciudades
    base_dir = os.path.dirname(os.path.abspath(__file__))
    import_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'import'))
    
    ciudades = []
    if os.path.exists(import_dir):

        for item in os.listdir(import_dir):

            full_path = os.path.join(import_dir, item)

            if os.path.isdir(full_path):
                ciudades.append(item)

    #obtener algoritmos
    recommender = RecommendationService()
    algoritmos = list(recommender.algorithms.keys())

    print("\n=== EVALUACIÓN ===")

    # selector de ciudades
    print("\n[ Seleccione la Ciudad ]")
    for i, c in enumerate(ciudades):
        print(f"  {i + 1}. {c}")
    
    try:
        sel_c = int(input("\n> Opción: ")) - 1
        ciudad_elegida = ciudades[sel_c]
    except (ValueError, IndexError):
        print("Opción inválida. Saliendo...")
        exit()

    #selector de algoritmos
    print(f"\n[ Seleccione el Algoritmo a evaluar para {ciudad_elegida} ]")
    for i, a in enumerate(algoritmos):
        print(f"  {i + 1}. {a.capitalize()}")
    
    try:
        sel_a = int(input("\n> Opción: ")) - 1
        algo_elegido = algoritmos[sel_a]
    except (ValueError, IndexError):
        print("Opción inválida. Saliendo...")
        exit()

    #ahora sí vamos a ejecutar la evaluación
    print("\n" + "="*50)
    try:
        evaluador = Evaluator(ciudad_elegida, algo_elegido)
        evaluador.evaluate()
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")

