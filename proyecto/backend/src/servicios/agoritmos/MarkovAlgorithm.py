from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
#importamos la librería Counter para contar las repeticiones de cada vecino de forma rápida
from collections import Counter
import random
import os
import pickle
import numpy as np

class MarkovAlgorithm(RecommendationAlgorithm):

    def __init__(self, alpha=0.5):
        super().__init__()
        self.alpha = alpha
        self.matrices_cargadas = False
        
        # Cargamos el archivo unificado que creamos con el FLExtractor
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pkl_path = os.path.join(base_dir, "..", "..", "entrenamiento", "factores_latentes.pkl")
        
        try:
            with open(self.pkl_path, 'rb') as f:
                datos = pickle.load(f)
                self.u_mat = datos["usuarios_matriz"]
                self.i_mat = datos["pois_matriz"]
                self.u_map = datos["user_to_idx"]
                self.i_map = datos["poi_to_idx"]
                self.matrices_cargadas = True
                print("[FPMC] Matrices y diccionarios cargados para personalización.")
        except Exception as e:
            print(f"[FPMC] Aviso: No se pudieron cargar los factores latentes: {e}")

    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_evitar, context, k=50):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param user_id: ID del usuario
        :param graph: Grafo completo
        :param context: info de los filtros
        """
        #con graphtool tenemos la parte de que si el siguiente poi se visitó más de ua vez, aparece duplicado en los neighbours, por lo que el algoritmo de Markov se implementa contando las repeticiones de cada vecino y no solamente con la puntuación del vecino
        neighbors = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context)
        if not neighbors:
            return []
        
        print(f"[MarkovAlgorithm] Vecinos encontrados para el POI {current_poi_id}: {len(neighbors)}")
        
        #contamos las repeticiones de cada vecino y las transformamos en un diccionario con las frecuencias
        neighbors_freq=Counter(neighbors)

        #guardamos todas las relaciones del current poi con sus duplicaciones tb
        # se hace para calcular la probabilidad que hubo para ir del current poi a cada next poi
        total_relaciones = len(neighbors)

        if self.matrices_cargadas and user_id not in self.u_map:
            print(f"\n[FPMC AVISO] El usuario {user_id} NO ESTÁ en la IA. (Se usará solo Markov)")

        mf_scores = {}
        for poi_id in neighbors_freq.keys():
            score = 0.0
            if self.matrices_cargadas and user_id in self.u_map and poi_id in self.i_map:
                fila_u = self.u_map[user_id]
                fila_i = self.i_map[poi_id]
                
                # PARCHE DE SEGURIDAD: Comprobamos que Elliot no haya borrado este índice
                if fila_u < self.u_mat.shape[0] and fila_i < self.i_mat.shape[0]:
                    u_vec = self.u_mat[fila_u]
                    i_vec = self.i_mat[fila_i]
                    score = np.dot(u_vec, i_vec)
            mf_scores[poi_id] = max(0, score) # Evitamos negativos para la probabilidad

        # Normalizamos los scores de MF para que sumen 1 (como probabilidades)
        total_mf = sum(mf_scores.values()) if sum(mf_scores.values()) > 0 else 1
        
        porcentaje_vecinos = {}
        for poi_dest_id, num_visitas in neighbors_freq.items():
            p_markov = num_visitas / total_relaciones
            p_mf = mf_scores.get(poi_dest_id, 0) / total_mf
            # Mezclamos usando la variable self.alpha (que por defecto es 0.5)
            score_mezclado = (self.alpha * p_markov) + ((1 - self.alpha) * p_mf)
            porcentaje_vecinos[poi_dest_id] = score_mezclado
            
            # --- AÑADIMOS EL PRINT CHIVATO AQUÍ ---
            print(f" -> POI: {poi_dest_id} | Prob Markov: {p_markov:.4f} | Prob MF (Gustos): {p_mf:.4f} | SCORE FINAL: {score_mezclado:.4f}")

        suma_porcentajes = sum(porcentaje_vecinos.values())
        for p in porcentaje_vecinos:
            porcentaje_vecinos[p] /= suma_porcentajes

        candidates = []


        while len(candidates) < k and len(porcentaje_vecinos) > 0:
            #nmero random para escoger un poi
            random_num = random.random()

            poi_elegido = None
            acumulado = 0.0

            #vamos sumando las probabilidades acumuladas hasta que el número random 
            # sea menor o igual a la acumulada, entonces ese será el poi elegido
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

            #eliminamos el candidato de la lista
            del porcentaje_vecinos[poi_elegido]

            #tenemos que reajustar las probabilidades ahora que hemos perdido un poi
            if len(porcentaje_vecinos) > 0:
                total_porcentaje_restante = sum(porcentaje_vecinos.values())

                for poi_id in porcentaje_vecinos:
                    porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_porcentaje_restante

    
        return candidates