from RouteGenerator import RouteGenerator
from Recommender import Recommender
from TreeRoute import TreeRoute
import csv
#para manejo de archivos
import os

class Evaluator:

    def __init__(self, route_generator:RouteGenerator):
        self.route_generator = route_generator
        self.recommender = Recommender(route_generator)
        self.results_folder = "results"

        # crear una carpeta para guardar los resultados
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder, exist_ok=True)

    def evaluate(self, test_cases, csv_file_name="evaluation_results.csv"):
        # primero creamos el archivo CSV para guardar los resultados
        csv_filepath = os.path.join(self.results_folder, csv_file_name)

        print(f"\n[EVALUATOR] Iniciando evaluación de {len(test_cases)} casos...")
        
        # abrir el archivo en modo escritura para ir guardando los pois
        with open(csv_filepath, mode='w', newline='') as csv_file:
            fieldnames = [
                'user_id',
                'num_poi_route',  # ej: poi_1, poi_2, ... 
                'poi_id', 
                'k',              # num de posibles pois para siguiente paso
                'context',
                'category'        # se añade la categoría para que sea más útil leerlo
            ]

            # creamos el escritor del CSV
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for i, case in enumerate(test_cases):
                user_id = case['user_id']
                lat = case['lat']
                lon = case['lon']
                steps = case['steps']
                context = case.get('context', None)

                print(f"\n[EVALUATOR] Evaluando caso {i+1}/{len(test_cases)}: user_id={user_id}, location=({lat},{lon}), steps={steps}, context={context}")

                recommended_tree = self.recommender.recommend_simple(
                    user_id=user_id,
                    lat=lat,
                    lon=lon,
                    context=context,
                    steps=steps
                )

                if not recommended_tree:
                    print(f"[EVALUATOR] No se encontró ruta recomendada para el caso {i+1}.")
                    continue

                # obtenemos todas las rutas válidas del árbol recomendado
                # path_nodes = poi1, poi2, poi3, poi4
                path_nodes = recommended_tree.get_all_paths()[0]

                # obtenemos el arbol con todas las posibles opciones para los valores de k
                final_tree = self.recommender.get_final_tree(
                    user_id=user_id,
                    lat=lat,
                    lon=lon,
                    context=context,
                    steps=steps
                )

                # Guardamos cada nodo de la ruta como una línea en el CSV
                for step_idx, node in enumerate(path_nodes):

                    # Datos del POI actual
                    if node.is_root():
                        poi_data = node.data
                        current_id = node.identifier
                        # Para la raíz, k es el número de hijos que tiene la raíz
                        ##imprimimos los hijos del nodo actual
                        #for i, child in enumerate(final_tree.tree.children(current_id)):
                        #    print(f"[EVALUATOR] Hijo {i} de la raíz: {child}")
                        #    pass
                        k_value = len(final_tree.tree.children(current_id))
                    else:
                        poi_data = node.data.get('poi_data', {})
                        current_id = node.identifier
                        
                        # Si estamos en un nodo intermedio, 'k' es cuántas opciones
                        # tenemos para CONTINUAR desde aquí.
                        k_value = len(final_tree.tree.children(current_id))
                        
                    writer.writerow({
                        'user_id': user_id,
                        'num_poi_route': f"poi_{step_idx+1}", # 0 es el inicio, 1 el primer salto...
                        'poi_id': poi_data.get('fsq_id', 'unknown'),
                        'k': k_value,
                        'context': str(context), # Convertimos el dict a string
                        'category': poi_data.get('category', 'unknown')
                    })
                    
            else:
                print(f"[EVALUATOR] No se encontró ruta para el caso {i+1}")
                # Opcional: Escribir una línea de error en el CSV
    
        print(f"\n[EVALUATOR] Evaluación completada. Resultados guardados en: {csv_filepath}")
        return csv_filepath