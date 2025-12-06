import os
import csv
from neo4j import GraphDatabase

class Predictor:
    def __init__(self, driver):
        self.driver = driver

        # creamos las carpetas para guardar los csv
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_predictions_path = os.path.join(base_dir, "predictions")
        self.test_folder = os.path.join(self.base_predictions_path, "test")
        self.predictions_folder = os.path.join(self.base_predictions_path, "predictions")

        for folder in [self.test_folder, self.predictions_folder]:
            os.makedirs(folder, exist_ok=True)

    #METODO PRINCIPAL
    def process_trail(self, user_id, trail_id):

        # obtenemos la información de la ruta de la BD
        trail_data = self._get_trail_data(user_id, trail_id)

        if not trail_data:
            print(f"[PREDICTOR]     No se encontraron datos para el trail {trail_id}")
            return

        # creamos los csv con los datos de las rutas
        self._save_test_csv(user_id, trail_id, trail_data)

        # creamos los csv con las predicciones
        self._save_predictions_csv(user_id, trail_id, trail_data)

    #OBTENCION DE DATOS DE LA BD
    def _get_trail_data(self, user_id, trail_id):
        # obtenemos las relaciones ordenadas por tiempo
        query = """
        MATCH (p1:POI)-[r:VISITED {trail_id: $trail_id, user_id: $user_id}]->(p2:POI)
        RETURN p1, r, p2
        ORDER BY r.p1_timestamp ASC
        """
        
        # lista para guardar los pois de la ruta
        trail_pois = []
        
        with self.driver.session() as session:
            results = session.run(query, trail_id=trail_id, user_id=user_id)
            # guardar resultados en una lista para poder iterar varias veces
            records = list(results)
            
            if not records:
                print(f"[PREDICTOR]     No se encontraron datos para el trail {trail_id}")
                return

            # vamos poi a poi guardándolo en trail_pois
            for i, record in enumerate(records):
                p1 = dict(record['p1'])
                p2 = dict(record['p2'])
                rel = dict(record['r'])

                # guardamos el poi con todos los datos de la relación en cada caso
                if i == 0:
                    first_poi = self._extract_visit_data(p1, rel, prefix='p1')
                    trail_pois.append(first_poi)
                
                # para los datos del contexto del poi debemos obtener la info de la relación según su prefijo
                next_poi = self._extract_visit_data(p2, rel, prefix='p2')
                trail_pois.append(next_poi)

        return trail_pois
    
    def _extract_visit_data(self, poi_node, relation_data, prefix):
        # extrar los datos dependiendo de si es el primero nodo o el resto
        return {
            'poi_id': poi_node.get('fsq_id'),
            'category': poi_node.get('category'),
            'timestamp': relation_data.get(f'{prefix}_timestamp'),
            'temp': relation_data.get(f'{prefix}_temp'),
            'precip': relation_data.get(f'{prefix}_precip'),
            'windspeed': relation_data.get(f'{prefix}_windspeed'),
            'preciptype': relation_data.get(f'{prefix}_preciptype'),
            'conditions': relation_data.get(f'{prefix}_conditions')
        }

    # CREACION CARPETA TEST
    def _save_test_csv(self, user_id, trail_id, trail_pois):
        filename = f"test_{trail_id}.csv"
        filepath = os.path.join(self.test_folder, filename)

        with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            # definimos las columnas del csv
            fieldnames = [
                'trail_id', 'num_poi', 'user_id', 'poi_id', 
                'timestamp', 'temp', 'precip', 
                'windspeed', 'preciptype', 'conditions'
            ]
            
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            #vamos poi a poi guardándolo en el csv
            for i,visit in enumerate(trail_pois):
                row = {
                    'trail_id': trail_id,
                    'user_id': user_id,
                    'num_poi': f'poi_{i+1}',
                    'poi_id': visit['poi_id'],
                    'timestamp': visit['timestamp'],
                    'temp': visit['temp'],
                    'precip': visit['precip'],
                    'windspeed': visit['windspeed'],
                    'preciptype': visit['preciptype'],
                    'conditions': visit['conditions']
                }
                writer.writerow(row)

    # CREACION CARPETA PREDICTIONS
    def _get_candidates_for_poi(self, poi_id):
        # busca todos los posibles destinos desde un POI y cuenta cuántas veces se ha hecho ese camino.
        
        query = """
        MATCH (start:POI {fsq_id: $start_id})-[r:VISITED]->(end:POI)
        RETURN end.fsq_id as candidate_id, count(r) as score
        ORDER BY score DESC
        """
        candidates = []
        with self.driver.session() as session:
            results = session.run(query, start_id=poi_id)

            # guardamos todos los poi candidatos de posibles siguientes de poi_id en una lista
            for record in results:
                candidates.append({
                    'poi_id': record['candidate_id'],
                    'prediction': record['score']
                })
        return candidates
    
    def _save_predictions_csv(self, user_id, trail_id, trail_pois):
        filename = f"prediction_{trail_id}.csv"
        filepath = os.path.join(self.predictions_folder, filename)
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['trail_id', 'num_poi', 'user_id', 'poi_id', 'prediction']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            # recorremos la ruta real y para cada punto siguiente, predecimos "a dónde podría ir después"
            # No calculamos predicciones para el primer punto porque la ruta empieza ahí
            for i, poi in enumerate(trail_pois[:-1]):
                current_poi_id = poi['poi_id']
                step_label = f"poi_{i+2}"

                # buscamos candidatos partiendo de este POI
                candidates = self._get_candidates_for_poi(current_poi_id)

                # guardamos cada candidato como una fila
                for candidate in candidates:
                    writer.writerow({
                        'trail_id': trail_id,
                        'num_poi': step_label,
                        'user_id': user_id,
                        'poi_id': candidate['poi_id'],
                        'prediction': candidate['prediction']
                    })