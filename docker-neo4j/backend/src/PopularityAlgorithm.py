from RecommendationAlgorithm import RecommendationAlgorithm
from POI import POI

class PopularityAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, tree_route, context=None):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
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
            poi = child.data.get('poi')

            if not isinstance(poi, POI):
                continue

            #obtenemos los campos necesarios 
            if poi.getRating() is not None:
                rating = poi.getRating()
            else:
                rating = 0.0

            if poi.getTotalRatings() is not None:
                total_ratings = poi.getTotalRatings()
            else:
                total_ratings = 0
            
            if poi.getTotalTips() is not None:
                total_tips = poi.getTotalTips()
            else:
                total_tips = 0

            #lo pasamos a escala de 0 a 1 (dividimos por 10)
            norm_rating_stars = rating / 10.0
            
            # 50% importa el rating, 40% total_ratings, 10% tips
            score = (norm_rating_stars * 0.5) + (total_ratings * 0.4) + (total_tips * 0.1)

            final_score = score*100

            candidates.append({
                'poi': poi,
                'score': final_score
            })
            
            
            
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates