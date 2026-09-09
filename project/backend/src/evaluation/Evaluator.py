from ranx import Qrels, Run, evaluate
from services.RecommendationService import RecommendationService
from graph.GraphRepository import GraphRepository
from persistence.LoadDB import LoadDB
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
            exact_prefix = f"{self.city_name}_{self.algorithm_name}_{self.suffix}_20"
        else:
            exact_prefix = f"{self.city_name}_{self.algorithm_name}_20"

        search_pattern = os.path.join(self.predictions_dir, f"{self.city_name}_{self.algorithm_name}*.csv")
        raw_files = glob.glob(search_pattern)

        prediction_files = []
        for file_path in raw_files:
            file_name = os.path.basename(file_path)
            if file_name.startswith(exact_prefix):
                prediction_files.append(file_path)

        if not prediction_files:
            raise FileNotFoundError(f"[Evaluator] No files found for the exact pattern: {exact_prefix}*.csv")
        
        latest_file = max(prediction_files, key=os.path.getmtime)
        print(f"[Evaluator] Prediction file found: {os.path.basename(latest_file)}")

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

    def _evaluate_coverage_diversity(self, run_dict, graph, k_coverage=5):
        stats = graph.get_category_stats()

        recommended_pois = set()
        recommended_categories = set()

        for query_id, poi_predictions in run_dict.items():
            sorted_pois = sorted(poi_predictions.items(), key=lambda x: x[1], reverse=True)
            for poi_id, _ in sorted_pois[:k_coverage]:
                recommended_pois.add(poi_id)
                v = graph.id_map.get(poi_id)
                if v is not None:
                    recommended_categories.add(graph.vp_category[v])

        if stats['total_pois'] > 0:
            coverage = len(recommended_pois) / stats['total_pois']
            diversity = len(recommended_categories) / stats['total_categorias']
        else:
            coverage = 0
            diversity = 0

        return {
        "coverage": coverage,
        "n_pois_recomendados": len(recommended_pois),
        "n_pois_totales": stats['total_pois'],
        "diversity": diversity,
        "n_categorias_recomendadas": len(recommended_categories),
        "n_categorias_totales": stats['total_categorias'],
        }

    def evaluate(self, graph=None, k_coverage=5):

        qrels_dict= self._load_Qrel()
        run_dict = self._load_run()

        if graph is None:
            graph = GraphRepository(self.city_name).get_graph()
        coverage_diversity = self._evaluate_coverage_diversity(run_dict, graph, k_coverage=k_coverage)
        

        qrels = Qrels(qrels_dict)
        run = Run(run_dict, name=f"{self.city_name}_{self.algorithm_name}")
        
        metrics = ["ndcg@5"]

        evaluation = evaluate(qrels, run, metrics, make_comparable=True)

        titulo = f"{self.algorithm_name.upper()}"
        if self.suffix:
            titulo += f" (Weights: {self.suffix})"

        print(f"\n RESULTS FOR: {titulo}")
        print("-" * 35)
        for metric, value in evaluation.items():
            print(f"| {metric.upper().ljust(15)} | {value:.4f} |")
        print("-" * 35)
        print(f"| {'COVERAGE'.ljust(15)} | {coverage_diversity['coverage']:.4f} |  ({coverage_diversity['n_pois_recomendados']}/{coverage_diversity['n_pois_totales']} POIs)")
        print(f"| {'DIVERSITY'.ljust(15)} | {coverage_diversity['diversity']:.4f} |  ({coverage_diversity['n_categorias_recomendadas']}/{coverage_diversity['n_categorias_totales']} categorías)")
        print("-" * 35)

        return {**evaluation, **coverage_diversity}


if __name__ == "__main__":

    base_dir = os.path.dirname(os.path.abspath(__file__))
    import_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'import'))
    
    cities = []
    if os.path.exists(import_dir):
        for item in os.listdir(import_dir):
            full_path = os.path.join(import_dir, item)
            if os.path.isdir(full_path):
                cities.append(item)

    recommender = RecommendationService()
    algorithms = list(recommender.algorithms.keys())

    print("\n=== EVALUATION SYSTEM ===")

    print("\n[ Choose the City ]")
    for i, c in enumerate(cities):
        print(f"  {i + 1}. {c}")
    
    try:
        sel_c = int(input("\n> Option: ")) - 1
        chosen_city = cities[sel_c]
    except (ValueError, IndexError):
        print("Invalid option. Exiting...")
        exit()

    print(f"\n[ Choose the Algorithm to evaluate for {chosen_city} ]")
    for i, a in enumerate(algorithms):
        print(f"  {i + 1}. {a.capitalize()}")
    
    try:
        sel_a = int(input("\n> Option: ")) - 1
        chosen_algorithm = algorithms[sel_a]
    except (ValueError, IndexError):
        print("Invalid option. Exiting...")
        exit()

    chosen_suffix = ""
    if chosen_algorithm == "markov_preferences":
        print("\n[ Weight Configuration ]")
        print("What balance do you want to evaluate? (e.g.: 20_80, 50_50, 70_30)")
        chosen_suffix = input("> Enter the suffix: ").strip()

    print("\n" + "="*50)
    try:
        evaluator = Evaluator(chosen_city, chosen_algorithm, chosen_suffix)
        evaluator.evaluate()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")