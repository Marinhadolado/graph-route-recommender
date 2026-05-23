from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph
import os
import pickle
import random
import numpy as np 

class PreferencesAlgorithm(RecommendationAlgorithm):
    def __init__(self, city_name="Tokyo"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'dataset', f'fm_{city_name}.pkl'))

        try:
            with open(model_path, 'rb') as f:
                self.modelo_nmf = pickle.load(f)
            print(f"[PreferencesAlgorithm] Modelo NMF cargado correctamente.")
        except FileNotFoundError:
            print(f"[PreferencesAlgorithm] ERROR: No se encontró el modelo en {model_path}.")
            self.modelo_nmf = None

    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_evitar, context, k=50):
        """
        Este recomendador basa su decisión en las preferencias históricas del usuario (NMF).
        """
        # 1. Obtenemos los vecinos accesibles desde el POI actual
        # Usamos set() para eliminar duplicados, ya que aquí NO nos importan las frecuencias de paso
        neighbors_no_context = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context=None)
        if not neighbors_no_context:
            return []
            
        unique_candidates = list(set(neighbors_no_context))
        
        # 2. Extraer datos del modelo NMF
        user_matrix_idx = None
        item_map_local = None
        item_factors_local = None
        user_factors = None
        
        if self.modelo_nmf:
            user_map = self.modelo_nmf['user_map']
            user_matrix_idx = user_map.get(str(user_id))
            item_map_local = self.modelo_nmf['item_map']
            item_factors_local = self.modelo_nmf['item_factors']
            user_factors = self.modelo_nmf['user_factors']

        # 3. Calcular la puntuación de afinidad (NMF) para cada candidato
        porcentaje_vecinos = {}
        suma_nmf = 0.0
        
        for poi_dest_id in unique_candidates:
            p_nmf = 0.0
            
            # Si el modelo cargó bien y tanto usuario como POI existen en la matriz
            if user_matrix_idx is not None and item_map_local is not None:
                item_matrix_idx = item_map_local.get(str(poi_dest_id))
                
                if item_matrix_idx is not None:
                    vector_usuario = user_factors[user_matrix_idx]
                    vector_poi = item_factors_local[item_matrix_idx]
                    
                    # Producto escalar para obtener la afinidad pura
                    p_nmf = np.dot(vector_usuario, vector_poi)
                    
                    # NMF no debería dar negativos, pero por seguridad matemática:
                    if p_nmf < 0:
                        p_nmf = 0.0
            
            porcentaje_vecinos[poi_dest_id] = p_nmf
            suma_nmf += p_nmf

        # 4. Normalizar las puntuaciones para convertirlas en probabilidades (0.0 a 1.0)
        if suma_nmf > 0:
            for poi_id in porcentaje_vecinos:
                porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / suma_nmf
        else:
            # COLD START: Si la suma es 0 (usuario nuevo o POIs nuevos), 
            # repartimos la probabilidad equitativamente
            prob_igual = 1.0 / len(unique_candidates)
            for poi_id in porcentaje_vecinos:
                porcentaje_vecinos[poi_id] = prob_igual

        # 5. Generar ranking de candidatos mediante selección de ruleta probabilística
        candidates = []
        
        while len(candidates) < k and len(porcentaje_vecinos) > 0:
            random_num = random.random()
            poi_elegido = None
            acumulado = 0.0

            for poi_id, porcentaje in porcentaje_vecinos.items():
                acumulado += porcentaje
                if random_num <= acumulado:
                    poi_elegido = poi_id
                    break

            if poi_elegido is None:
                poi_elegido = random.choice(list(porcentaje_vecinos.keys()))

            prediction_orden = k - len(candidates)
            candidates.append({
                'poi_id': poi_elegido, 
                'prediction': prediction_orden
            })

            # Eliminamos el candidato elegido para no volver a recomendarlo
            del porcentaje_vecinos[poi_elegido]

            # Reajustar las probabilidades al 100% tras perder un candidato
            if len(porcentaje_vecinos) > 0:
                total_restante = sum(porcentaje_vecinos.values())
                if total_restante > 0:
                    for poi_id in porcentaje_vecinos:
                        porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_restante
                else:
                    # Fallback de seguridad
                    prob_igual = 1.0 / len(porcentaje_vecinos)
                    for poi_id in porcentaje_vecinos:
                        porcentaje_vecinos[poi_id] = prob_igual

        return candidates