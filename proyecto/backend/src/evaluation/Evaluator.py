from ranx import Qrels, Run, evaluate
from servicios.RecommendationService import RecommendationService
from persistencia.LoadDB import LoadDB
import os
import csv
import glob

class Evaluator:

    def __init__(self, city_name, algorithm_name, suffix=""):
        self.city_name = city_name
        self.algorithm_name = algorithm_name
        self.suffix = suffix
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = os.path.join(self.base_dir, '..', '..', 'dataset')
        self.predictions_dir = os.path.join(self.base_dir, '..', '..', 'predictions')   

    def _load_Qrel(self):
        test_file = os.path.join(self.dataset_dir, 'test.csv')
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"[Evaluator] {test_file} not found")
        
        qrel_dict = {}

        with open(test_file, mode='r', encoding='utf-8') as f:
            reader= csv.DictReader(f)
            prev_trail_id = None
            step_counter = 1

            for row in reader:
                current_trail_id = row['trail_id']
                current_poi_id = row['poi_id']

                if current_trail_id == prev_trail_id:
                    step_counter += 1
                    query_id = f"{current_trail_id}_{step_counter}"
                    qrel_dict[query_id] = {current_poi_id: 1} 
                else:
                    step_counter = 1
                    prev_trail_id = current_trail_id

        return qrel_dict
    
    def _load_run(self):
        if self.suffix:
            prefix_exacto = f"{self.city_name}_{self.algorithm_name}_{self.suffix}_20"
        else:
            prefix_exacto = f"{self.city_name}_{self.algorithm_name}_20"

        search_pattern = os.path.join(self.predictions_dir, f"{self.city_name}_{self.algorithm_name}*.csv")
        archivos_brutos = glob.glob(search_pattern)

        archivos_prediccion = []
        for archivo in archivos_brutos:
            nombre_archivo = os.path.basename(archivo)
            if nombre_archivo.startswith(prefix_exacto):
                archivos_prediccion.append(archivo)

        if not archivos_prediccion:
            raise FileNotFoundError(f"[Evaluator] No se encontraron archivos para el patrón exacto: {prefix_exacto}*.csv")
        
        latest_file = max(archivos_prediccion, key=os.path.getmtime)
        print(f"[Evaluator] Archivo de predicción encontrado: {os.path.basename(latest_file)}")

        run_dict = {}
        with open(latest_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                trail_id = row['trail_id']
                step_number = row['step']
                poi_id = row['poi_id']
                prediction = float(row['prediction']) 

                query_id = f"{trail_id}_{step_number}"
                if query_id not in run_dict:
                    run_dict[query_id] = {}

                run_dict[query_id][poi_id] = prediction

        return run_dict
    
    def evaluate(self):

        qrels_dict= self._load_Qrel()
        run_dict = self._load_run()

        qrels = Qrels(qrels_dict)
        run = Run(run_dict, name=f"{self.city_name}_{self.algorithm_name}")
        
        metricas = ["hit_rate@1", "hit_rate@5", "hit_rate@10", "ndcg@1", "ndcg@5", "ndcg@10","mrr@1","mrr@5","mrr@10"]

        evaluacion = evaluate(qrels, run, metricas, make_comparable=False)

        titulo = f"{self.algorithm_name.upper()}"
        if self.suffix:
            titulo += f" (Weights: {self.suffix})"

        print(f"\n RESULTS FOR: {titulo}")
        print("-" * 35)
        for metrica, valor in evaluacion.items():
            print(f"| {metrica.upper().ljust(15)} | {valor:.4f} |")
        print("-" * 35)


if __name__ == "__main__":

    base_dir = os.path.dirname(os.path.abspath(__file__))
    import_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'import'))
    
    ciudades = []
    if os.path.exists(import_dir):
        for item in os.listdir(import_dir):
            full_path = os.path.join(import_dir, item)
            if os.path.isdir(full_path):
                ciudades.append(item)

    recommender = RecommendationService()
    algoritmos = list(recommender.algorithms.keys())

    print("\n=== EVALUATION SYSTEM ===")

    print("\n[ Choose the City ]")
    for i, c in enumerate(ciudades):
        print(f"  {i + 1}. {c}")
    
    try:
        sel_c = int(input("\n> Option: ")) - 1
        ciudad_elegida = ciudades[sel_c]
    except (ValueError, IndexError):
        print("Invalid option. Exiting...")
        exit()

    print(f"\n[ Choose the Algorithm to evaluate for {ciudad_elegida} ]")
    for i, a in enumerate(algoritmos):
        print(f"  {i + 1}. {a.capitalize()}")
    
    try:
        sel_a = int(input("\n> Option: ")) - 1
        algo_elegido = algoritmos[sel_a]
    except (ValueError, IndexError):
        print("Invalid option. Exiting...")
        exit()

    sufijo_elegido = ""
    if algo_elegido == "markov_preferences":
        print("\n[ Weight Configuration ]")
        print("What balance do you want to evaluate? (e.g.: 20_80, 50_50, 70_30)")
        sufijo_elegido = input("> Enter the suffix: ").strip()

    print("\n" + "="*50)
    try:
        evaluador = Evaluator(ciudad_elegida, algo_elegido, sufijo_elegido)
        evaluador.evaluate()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")