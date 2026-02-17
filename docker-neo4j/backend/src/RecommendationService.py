from RouteGenerator import RouteGenerator
from RatingAlgorithm import RatingAlgorithm

class RecommendationService:

    def __init__(self, generator):
        if not isinstance(generator, RouteGenerator):
            raise TypeError("[RECOMMENDATION SERVICE] Generator debe de ser de tipo RouteGenerator")

        self.generator= generator

        self.algorithms= {  
            "ratings": RatingAlgorithm()
        }

        self.algorithms
    
    def getCandidates(self, user_id, lat, lon, context, steps, algorithm_name):
        """
        Crea una lista de diccionarios con los candidatos pois inmediatos para que el predictor los evalue
        
        :param self: Descripción
        :param user_id: Descripción
        :param lat: Descripción
        :param lon: Descripción
        :param context: Descripción
        :param steps: Descripción
        :param algorithm_name: Descripción
        """

        #buscamos el algoritmo entre los disponibles del sistema
        algorithm = self.algorithms.get(algorithm_name.lower())
        if not algorithm:
            print(f"[SERVICE] Error: Estrategia '{algorithm_name}' no encontrada.")
            return []
            
        #primero generamos el arbol de posibles rutas partiendo del punto solicitado
        candidate_tree = self.generator.getRoutes(lat, lon, steps)
        
        if not candidate_tree:
            return []

        # AQUÍ SE PODRIA PONER UN FILTRADO DE HISTORIAL, CONTEXTO... y así usar el user_id

        # llamamos al algoritmo para que ordene los posibles siguientes pois segun su predictor
        # devuelve [{'poi': POI_Obj, 'score': float}, ...] ordenado
        ranked_data = algorithm.rankCandidates(candidate_tree, context)
        
        # convertimos los objetos POI a diccionarios simples
        final_candidates = []
        
        for item in ranked_data:
            poi_candidate = item['poi']
            score = item['score']
            
            final_candidates.append({
                'poi_id': poi_candidate.getId(),
                'score': score
            })
            
        return final_candidates