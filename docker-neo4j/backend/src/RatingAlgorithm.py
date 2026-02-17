from RecommendationAlgorithm import RecommendationAlgorithm

class RatingAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, tree_route, context=None):
        """
        Parte de un arbol de rutas para crear una lista de posibles candidatos a siguientes nodos del root
        
        :param self: Descripción
        :param tree_route: Descripción
        :param context: Descripción
        """
        # partimos del treeRoute para obtener el tree como tal y la raiz
        tree = tree_route.getTree()
        root_id = tree.root
        
        # obtenemos los hijos directos
        children = tree.children(root_id)
        
        candidates = []
        
        for child in children:
            poi_obj = child.data.get('poi')
            
            if poi_obj.getRating() is not None:
                score = float(poi_obj.getRating()) 
            else:
                score = 0.0
            
            candidates.append({
                'poi': poi_obj,
                'score': score
            })
            
        # ordenamos los candidatos segun el rating de mayor a menor
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates