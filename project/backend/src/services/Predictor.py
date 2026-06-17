import sys
import os
import csv
import json
from datetime import datetime
import random
from graph.GraphRepository import GraphRepository
from services.RecommendationService import RecommendationService
from persistence.Neo4jConnection import Neo4jConnection

class Predictor:

    def __init__(self, city_name):

        self.base_dir=os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir=os.path.join(self.base_dir,'..','..', 'dataset')
        self.city_name = city_name

        self.output_dir=os.path.join(self.base_dir,'..','..','predictions')
        os.makedirs(self.output_dir, exist_ok=True) 

        try:
            self.neo4j_client = Neo4jConnection()
            self.graph_repository = GraphRepository(city_name)
            self.recommender = RecommendationService()            
           
            print("[PREDICTOR] Successfully connected to the Neo4j database and initialized services.")

        except Exception as e:
            print(f"[PREDICTOR] Error: {e}")
            raise
    
    def __str__(self):
        return "Predictor configured for " + self.city_name
    
    def close(self):
        if self.neo4j_client:
            self.neo4j_client.close()

    def _load_routes_from_csv(self, filepath):

        if not os.path.exists(filepath):
            print(f"[PREDICTOR] The file {filepath} does not exist.")
            return None
        
        routes = {}

        with open(filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                
                trail_id = row['trail_id']

                if trail_id not in routes:
                    routes[trail_id] = []
                    
                routes[trail_id].append(row)

        return routes
            
    def generate_predictions(self, user_id, context, algorithm, suffix=""):
        print("[PREDICTOR] Generating predictions with algorithm:", algorithm)

        graph = self.graph_repository.get_graph()
        self.recommender.reset_timers()

        test_file=os.path.join(self.dataset_dir,'test.csv')

        with open(test_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                    if row['poi_id'] not in graph.id_map:
                        print(f"[PREDICTOR] ERROR: The file {test_file} contains data from city {row['city']} but expected {self.city_name}.")
                        return
                    break 
                
        print(f"[PREDICTOR] Loading routes from {test_file}...")
        routes = self._load_routes_from_csv(test_file)

        if not routes:
            print(f"[PREDICTOR] No routes found in the file {test_file}.")
            return
        
        history = graph.getUserHistory(user_id)
        if not history:
            print(f"[PREDICTOR] The user {user_id} has no history in the graph. No predictions can be generated.")
            return
        
        print(f"[PREDICTOR] Processing {len(routes)} routes for prediction...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if suffix:
            filename= f"{self.city_name}_{algorithm}_{suffix}_{timestamp}.csv"
        else:
            filename = f"{self.city_name}_{algorithm}_{timestamp}.csv"
        output_file = os.path.join(self.output_dir, filename)

        print(f"[PREDICTOR] The result will be saved in: {filename}")
        
        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(["trail_id", "step", "candidate_rank", "poi_id", "prediction"])

            n_con_candidatos = 0
            n_vacios = 0

            for trail_id, trail_steps in routes.items():
                if not trail_steps:
                    continue

                recommended_in_route = set()
                
                for i in range(len(trail_steps)-1):
                    current_step = trail_steps[i]
                    poi_id= current_step['poi_id']

                    if poi_id not in graph.id_map:
                        continue

                    pois_to_avoid= set(history).union(recommended_in_route)

                    candidates = self.recommender.getCandidates(
                        current_poi_id=poi_id,
                        user_id=user_id,
                        context=context,
                        algorithm_name=algorithm,
                        pois_to_avoid=pois_to_avoid,
                        graph=graph
                    )

                    if not candidates:
                        n_vacios += 1
                        continue

                    n_con_candidatos += 1

                    for c in candidates:
                        recommended_in_route.add(c['poi_id'])

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
        print(f"[PREDICTOR] Saved predictions to {output_file}.")

        total_steps = n_con_candidatos + n_vacios
        if total_steps > 0:
            cobertura = 100.0 * n_con_candidatos / total_steps
            print(f"[PREDICTOR] Coverage: {n_con_candidatos}/{total_steps} steps with candidates "
                  f"({cobertura:.1f}%) | empty: {n_vacios}")

        stats = self.recommender.get_timing_stats()
        if stats['n_ranking'] > 0:
            print(f"[PREDICTOR] Average ranking time (total) per query: {stats['tiempo_medio_ms']:.3f} ms "
                f"(sobre {stats['n_ranking']} consultas)")
            print(f"[PREDICTOR] Average ranking time (without pre-filtering) per query: {stats['tiempo_medio_puro_ms']:.3f} ms")
            print(f"[PREDICTOR] Total ranking time (total): {stats['tiempo_ranking_total_s']:.2f} s")
            print(f"[PREDICTOR] Total ranking time (without pre-filtering): {stats['tiempo_ranking_puro_total_s']:.2f} s")
        else:
            print("[PREDICTOR] No timing measurement (algorithm excluded from efficiency comparison).")                 
                    
if __name__ == "__main__":

    try:
        if len(sys.argv) != 5:
            print("Usage: python Predictor.py <user_id> <context> <algorithm> <city_name>")
            print("If no context is provided, default values will be used.")
            sys.exit(1)
        user_id = sys.argv[1]
        context_arg = sys.argv[2] 
        algorithm = sys.argv[3]
        city_name = sys.argv[4]

        if context_arg=="None":
            context=None
        else:
            try:
                context = json.loads(context_arg)
            except json.JSONDecodeError:
                print(f"\n [PREDICTOR] ERROR: The provided context is not a valid JSON.")
                print(f"Example: '{{\"conditions\": \"Clear\", \"rating\": 8.0}}'\n")
                sys.exit(1)

        random.seed(42)
        predictor= Predictor(city_name)
        print(f"[PREDICTOR] Starting predictions for user: {user_id}")

        predictor.generate_predictions(user_id, context, algorithm)
        if predictor:
            predictor.close()
    except Exception as e:
        print(f"[PREDICTOR] ¡ERROR FATAL!: {e}")