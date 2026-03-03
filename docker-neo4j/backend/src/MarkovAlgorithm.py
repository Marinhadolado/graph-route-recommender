from RecommendationAlgorithm import RecommendationAlgorithm
from POI import POI

class MarkovAlgorithm(RecommendationAlgorithm):

    def rankCandidates(self, tree_route, context=None):
        """
        Algoritmo basado en Cadenas de Markov. 
        Para clasificar a los candidatos de siguiente POI, calcula 
        la probabilidad de transición desde el nodo raíz hacia
        sus hijos basándose en la frecuencia de cuanta gente fue a 
        el hijo partiendo del padre.
        """
        tree = tree_route.getTree()
        root_id = tree.root
        
        # Obtenemos todos los viajes que salieron de este POI
        children = tree.children(root_id)
        
        # Si nadie ha salido de aquí, no hay recomendaciones
        total_transitions = len(children)
        if total_transitions == 0:
            return []
        
        candidates = []
            
        # para contear la frecuencia usamos un diccionario de tipo { 'poi_id_1': {'poi': ObjetoPOI, 'count': 5}, ... }
        transition_counts = {}
        for child in children:

            candidates.append({
                'poi': ,
                'score': score
            })
            
        # 3. ORDENAR
        # El destino con mayor probabilidad histórica va primero
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates