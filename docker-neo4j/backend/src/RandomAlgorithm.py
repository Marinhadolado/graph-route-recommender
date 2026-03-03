from RecommendationAlgorithm import RecommendationAlgorithm
import random

class RandomAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, tree_route, context=None):
        """
        Para escoger el siguiente POI, se asigna un predictions aleatorio 
        y único a cada hijo del nodo del 0-num_opciones
        
        :param self: Descripción
        :param tree_route: Descripción
        :param context: Descripción
        """
        tree = tree_route.getTree()
        root_id = tree.root
        children = tree.children(root_id)
        
        candidates = []
        num_opciones = len(children)
        
        puntuaciones_azar = list(range(num_opciones))
        #desordenamos esta lista ordenada al azar
        random.shuffle(puntuaciones_azar)
        
        for i, child in enumerate(children):
            poi = child.data.get('poi')
            
            score = float(puntuaciones_azar[i])
            
            candidates.append({
                'poi': poi,
                'score': score
            })
            
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates
    