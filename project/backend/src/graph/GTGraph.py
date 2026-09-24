from graph_tool.all import Graph, GraphView
from datetime import datetime
from graph_tool.util import find_edge
import time
from collections import Counter

class GTGraph:
    def __init__(self):
        self.g = Graph(directed=True)

        self.vp_fsq_id = self.g.new_vertex_property("string")
        self.g.vp["fsq_id"] = self.vp_fsq_id

        self.vp_lat = self.g.new_vertex_property("double")
        self.g.vp["latitude"] = self.vp_lat

        self.vp_lon = self.g.new_vertex_property("double")
        self.g.vp["longitude"] = self.vp_lon

        self.vp_category = self.g.new_vertex_property("string")
        self.g.vp["category"] = self.vp_category

        self.vp_price = self.g.new_vertex_property("int")
        self.g.vp["price"] = self.vp_price

        self.vp_rating = self.g.new_vertex_property("double")
        self.g.vp["rating"] = self.vp_rating

        self.vp_total_ratings = self.g.new_vertex_property("int")
        self.g.vp["total_ratings"] = self.vp_total_ratings

        self.vp_total_tips = self.g.new_vertex_property("int")
        self.g.vp["total_tips"] = self.vp_total_tips

        self.vp_category_lvlFs = self.g.new_vertex_property("string")
        self.g.vp["category_lvlFs"] = self.vp_category_lvlFs

        self.vp_city = self.g.new_vertex_property("string")
        self.g.vp["city"] = self.vp_city

        # scheduling
        self.vp_wk_em = self.g.new_vertex_property("int")
        self.g.vp["Weekday_EarlyMorning"] = self.vp_wk_em

        self.vp_wk_m = self.g.new_vertex_property("int")
        self.g.vp["Weekday_Morning"] = self.vp_wk_m

        self.vp_wk_a = self.g.new_vertex_property("int")
        self.g.vp["Weekday_Afternoon"] = self.vp_wk_a

        self.vp_wk_n = self.g.new_vertex_property("int")
        self.g.vp["Weekday_Night"] = self.vp_wk_n

        self.vp_we_em = self.g.new_vertex_property("int")
        self.g.vp["Weekend_EarlyMorning"] = self.vp_we_em

        self.vp_we_m = self.g.new_vertex_property("int")
        self.g.vp["Weekend_Morning"] = self.vp_we_m

        self.vp_we_a = self.g.new_vertex_property("int")
        self.g.vp["Weekend_Afternoon"] = self.vp_we_a

        self.vp_we_n = self.g.new_vertex_property("int")
        self.g.vp["Weekend_Night"] = self.vp_we_n
        
        self.ep_user_id = self.g.new_edge_property("string")
        self.g.ep["user_id"] = self.ep_user_id
        self.ep_trail_id = self.g.new_edge_property("string")
        self.g.ep["trail_id"] = self.ep_trail_id

        self.ep_p1_timestamp = self.g.new_edge_property("double")
        self.g.ep["p1_timestamp"] = self.ep_p1_timestamp
        self.ep_p1_temp = self.g.new_edge_property("double")
        self.g.ep["p1_temp"] = self.ep_p1_temp
        self.ep_p1_precip = self.g.new_edge_property("double")
        self.g.ep["p1_precip"] = self.ep_p1_precip
        self.ep_p1_windspeed = self.g.new_edge_property("double")
        self.g.ep["p1_windspeed"] = self.ep_p1_windspeed
        self.ep_p1_conditions = self.g.new_edge_property("string")
        self.g.ep["p1_conditions"] = self.ep_p1_conditions
        self.ep_p1_preciptype = self.g.new_edge_property("string")
        self.g.ep["p1_preciptype"] = self.ep_p1_preciptype

        self.ep_p2_timestamp = self.g.new_edge_property("double")
        self.g.ep["p2_timestamp"] = self.ep_p2_timestamp
        self.ep_p2_temp = self.g.new_edge_property("double")
        self.g.ep["p2_temp"] = self.ep_p2_temp
        self.ep_p2_precip = self.g.new_edge_property("double")
        self.g.ep["p2_precip"] = self.ep_p2_precip
        self.ep_p2_windspeed = self.g.new_edge_property("double")
        self.g.ep["p2_windspeed"] = self.ep_p2_windspeed
        self.ep_p2_conditions = self.g.new_edge_property("string")
        self.g.ep["p2_conditions"] = self.ep_p2_conditions
        self.ep_p2_preciptype = self.g.new_edge_property("string")
        self.g.ep["p2_preciptype"] = self.ep_p2_preciptype
        
        self.ep_time_diff = self.g.new_edge_property("double")
        self.g.ep["time_diff"] = self.ep_time_diff

        self.id_map = {} 
        self.prefilter_time = 0.0
        self.n_prefilter = 0

    def reset_prefilter_timer(self):
        self.prefilter_time = 0.0
        self.n_prefilter = 0
        
    def _parse_date(self, date_str):
        """ Converts an ISO date string to a timestamp. """
        if not date_str or date_str == 'None' or date_str == '':
            return 0.0
        try:
            dt = datetime.fromisoformat(str(date_str).replace('Z', ''))
            return float(dt.timestamp())
        except ValueError:
            return 0.0
        
    def addNode(self, poi_data):
        """Add a node in the graph."""
        fsq_id = poi_data.get('fsq_id')
        if fsq_id not in self.id_map:
            v = self.g.add_vertex()
            self.id_map[fsq_id] = v
            
            self.vp_fsq_id[v] = fsq_id
            self.vp_lat[v] = float(poi_data.get('latitude') or 0.0)
            self.vp_lon[v] = float(poi_data.get('longitude') or 0.0)
            self.vp_category[v] = str(poi_data.get('category') or "")
            self.vp_price[v] = int(poi_data.get('price') or 0)
            self.vp_rating[v] = float(poi_data.get('rating') or 0.0)
            self.vp_total_ratings[v] = int(poi_data.get('total_ratings') or 0)
            self.vp_total_tips[v] = int(poi_data.get('total_tips') or 0)
            self.vp_category_lvlFs[v] = str(poi_data.get('category_lvlFs') or "")
            self.vp_city[v] = str(poi_data.get('city') or "")

            self.vp_wk_em[v] = int(poi_data.get('Weekday_EarlyMorning') or 0)
            self.vp_wk_m[v] = int(poi_data.get('Weekday_Morning') or 0)
            self.vp_wk_a[v] = int(poi_data.get('Weekday_Afternoon') or 0)
            self.vp_wk_n[v] = int(poi_data.get('Weekday_Night') or 0)
            self.vp_we_em[v] = int(poi_data.get('Weekend_EarlyMorning') or 0)
            self.vp_we_m[v] = int(poi_data.get('Weekend_Morning') or 0)
            self.vp_we_a[v] = int(poi_data.get('Weekend_Afternoon') or 0)
            self.vp_we_n[v] = int(poi_data.get('Weekend_Night') or 0)

            return v
        return self.id_map[fsq_id]

    def addEdge(self, from_id, to_id, rel_data):
        """Creates a connection between two POIs."""
        if from_id in self.id_map and to_id in self.id_map:
            e = self.g.add_edge(self.id_map[from_id], self.id_map[to_id])
            
            self.ep_user_id[e] = str(rel_data.get('user_id', ''))
            self.ep_trail_id[e] = str(rel_data.get('trail_id', ''))

            self.ep_p1_timestamp[e] = self._parse_date(rel_data.get('p1_timestamp'))
            self.ep_p2_timestamp[e] = self._parse_date(rel_data.get('p2_timestamp'))
            
            self.ep_p1_temp[e] = float(rel_data.get('p1_temp', 0.0))
            self.ep_p1_precip[e] = float(rel_data.get('p1_precip', 0.0))
            self.ep_p1_windspeed[e] = float(rel_data.get('p1_windspeed', 0.0))
            self.ep_p1_conditions[e] = str(rel_data.get('p1_conditions', ''))
            self.ep_p1_preciptype[e] = str(rel_data.get('p1_preciptype', ''))

            self.ep_p2_temp[e] = float(rel_data.get('p2_temp', 0.0))
            self.ep_p2_precip[e] = float(rel_data.get('p2_precip', 0.0))
            self.ep_p2_windspeed[e] = float(rel_data.get('p2_windspeed', 0.0))
            self.ep_p2_conditions[e] = str(rel_data.get('p2_conditions') or '')
            self.ep_p2_preciptype[e] = str(rel_data.get('p2_preciptype') or '')
            self.ep_time_diff[e] = float(rel_data.get('time_diff', 0.0))

            return True
        
        print(f"[GTGraph] The relationship from {from_id} to {to_id} could not be added because one of the nodes does not exist in the graph.")
        
        if from_id not in self.id_map:
            print(f" - Source node not found: {from_id}")
        
        if to_id not in self.id_map:
            print(f" - Destination node not found: {to_id}")
        return False
    
    def _get_segment_vp(self, time_segment):
        franja_a_vp = {
            "Weekday_EarlyMorning": self.vp_wk_em, "Weekday_Morning": self.vp_wk_m,
            "Weekday_Afternoon":    self.vp_wk_a,  "Weekday_Night":   self.vp_wk_n,
            "Weekend_EarlyMorning": self.vp_we_em, "Weekend_Morning": self.vp_we_m,
            "Weekend_Afternoon":    self.vp_we_a,  "Weekend_Night":   self.vp_we_n,
        }
        return franja_a_vp.get(str(time_segment))

    def _get_direct_transition_probs(self, fsq_id, pois_avoid, context):
        """
        Probabilidad empírica de transición desde fsq_id a cada vecino directo.
        """
        vecinos = self._getDirectFilteredNeighbors(fsq_id, pois_avoid, context)
        if not vecinos:
            return {}

        total = len(vecinos)
        freq = Counter(vecinos)

        return {poi: count / total for poi, count in freq.items()}

    def getNStepTransitionProbabilities(self, fsq_id, pois_to_avoid, context_chain, hops=1):
        """
        Calcula las probabilidades de transición a N saltos (Markov) sumando
        los diferentes caminos posibles, evitando ciclos.
        Devuelve un diccionario {poi_id: probabilidad}.
        """
        if hops < 1:
            return {}

        if pois_to_avoid:
            pois_to_avoid = set(pois_to_avoid)
        else:
            pois_to_avoid = set()

        # Usamos una lista para explorar caminos. 
        # (nodo_actual, probabilidad_acumulada_del_camino, set_nodos_visitados_en_este_camino)
        active_paths = [(fsq_id, 1.0, {fsq_id} | pois_to_avoid)]
        final_probs = {}

        #vamos nivel a nivel de profundidad mirando los vecinos directos y acumulando las probabilidades
        for level in range(1, hops + 1):
            if context_chain:
                level_context = context_chain[level - 1] 
            else:
                level_context = None
            
            next_paths = []
            transition_cache = {}

            # en cada nivel vamos nodo a nodo de la capa de profundidad en la que estemos 
            # y obtenemos los vecinos directos
            for current_node, prob_acumulada, path_visited in active_paths:
                if current_node not in transition_cache:
                    # obtenemos las probabilidades de transición directa desde current_node a sus vecinos filtrados
                    transition_cache[current_node] = self._get_direct_transition_probs(current_node, pois_to_avoid, level_context)
                    #en caso de A saldrá ['B','C','C','D'] con el counter de la funcion: {B:1, C:2, D:1}
                
                step_probs = transition_cache[current_node]

                #despues voy calculando la probabilidad acumulada de cada nodo vecino
                #  y si no es el último nivel, lo añado a la lista de caminos activos para 
                # el siguiente nivel
                for dest_id, p in step_probs.items():
                    if dest_id in path_visited:
                        continue
                    
                    path_prob = prob_acumulada * p

                    if level == hops:
                        # Si es el salto final, lo guardamos como candidato.
                        final_probs[dest_id] = final_probs.get(dest_id, 0.0) + path_prob

                    else:
                        # Si es un salto intermedio, NO lo guardamos. 
                        # Solo le pasamos la probabilidad a la mochila para el siguiente salto.
                        #en la primera iteracion de nivel 1, path_visited = {A} y se añade (B, p(B|A), {A,B}) y (C, p(C|A), {A,C})
                        next_paths.append((dest_id, path_prob, path_visited | {dest_id}))

            #active_paths = [('B',0.25,{A,B}), ('C',0.5,{A,C}), ('D',0.25,{A,D})]
            active_paths = next_paths
            if not active_paths:
                        break

        # Control de seguridad (Probabilidad máxima = 1)
        for poi_id in final_probs:
            if final_probs[poi_id] > 1.0:
                if final_probs[poi_id] > 1.000001:
                    raise ValueError(f"[GTGraph] Probabilidad inválida para {poi_id}: {final_probs[poi_id]:.4f} > 1")
                final_probs[poi_id] = 1.0

        return final_probs

    def _getDirectFilteredNeighbors(self, fsq_id, pois_avoid, context):
        t0 = time.perf_counter()

        try:
            current_v = self.id_map.get(fsq_id)
            if current_v is None:
                return []

            pois_avoid = pois_avoid or set()

            #primero creamos las variables de filtrado
            #ej: context = {"time_segment": "Weekday_Morning", "conditions": "Clear", "temp": 20.0, "precip": 0.0, "windspeed": 5.0}
            # y hacemos que vp_franja= Weekday_Morning
            vp_franja = None
            f_conditions = f_preciptype = None
            f_temp = f_precip = f_windspeed = None
            if context:
                if 'time_segment' in context:
                    vp_franja = self._get_segment_vp(context['time_segment'])
                if 'conditions' in context:
                    f_conditions = str(context['conditions'])
                if 'preciptype' in context:
                    f_preciptype = str(context['preciptype'])
                if 'temp' in context:
                    f_temp = float(context['temp'])
                if 'precip' in context:
                    f_precip = float(context['precip'])
                if 'windspeed' in context:
                    f_windspeed = float(context['windspeed'])

            neighbors = []
            for e in current_v.out_edges():
                n = e.target()
                n_id = self.vp_fsq_id[n]

                if n_id in pois_avoid:
                    continue
                # si el nodo vecino no tiene visitas en la franja horaria, lo descartamos
                if vp_franja is not None and vp_franja[n] == 0:
                    continue

                if f_conditions is not None:
                    # Separamos las condiciones de la arista por coma para hacer una búsqueda exacta de la palabra
                    edge_conditions = [c.strip() for c in self.ep_p2_conditions[e].split(',')]
                    if f_conditions not in edge_conditions:
                        continue
                
                if f_preciptype is not None:
                    edge_preciptypes = [p.strip() for p in self.ep_p2_preciptype[e].split(',')]
                    if f_preciptype not in edge_preciptypes:
                        continue
                if f_temp is not None and self.ep_p2_temp[e] != f_temp:
                    continue
                if f_precip is not None and self.ep_p2_precip[e] != f_precip:
                    continue
                if f_windspeed is not None and self.ep_p2_windspeed[e] != f_windspeed:
                    continue

                neighbors.append(n_id)

            return neighbors
        finally:
            self.prefilter_time += (time.perf_counter() - t0)
            self.n_prefilter += 1


    def getFilteredNeighbors(self, fsq_id, pois_avoid, context_chain, hops=1):
        if hops < 1:
            return []

        pois_avoid = pois_avoid or set()

        # primero creamos un conjunto de nodos visitados, que incluye los nodos a evitar y el nodo actual
        visited = set(pois_avoid) | {fsq_id}
        frontier = {fsq_id}

        # recorremos cada nivel de profundidad de 1 a hops.
        # el contexto (time_segment/conditions) SOLO se exige en el último salto,
        # el que aterriza en el candidato final; los saltos intermedios se expanden libres.
        for level in range(1, hops + 1):
            level_context = context_chain[level - 1] if context_chain else None

            next_frontier = set()
            #vamos nodo a nodo de la capa de profundidad en la que estemos y obtenemos los vecinos directos
            for node_id in frontier:
                vecinos = self._getDirectFilteredNeighbors(node_id, visited, level_context)
                next_frontier |= set(vecinos)
            #actualizamos los nodos vistos en esta capa para si hay otra iteracción
            visited |= next_frontier
            # guardamos ya los nuevos vecinos del fsqid(poi origen) con distancia hop
            frontier = next_frontier
            #si no hay profundidad suficiente no existen candidatos y salimos
            if not frontier:
                break

        #devolvemos los candidatos obtenidos en el bucle sin los nodos a evitar que ya salieron en anteriores capas
        return list(frontier)

    
    def getCityName(self):
        """ Returns the name of the city by reading the first node of the graph """
        if self.g.num_vertices() > 0:
            first_vertex = self.g.vertex(0)
            return self.vp_city[first_vertex]
        return "NOCITY"
    
    def getUserHistory(self, user_id):
        """ Returns a list of fsq_id that the user has already visited historically. """
        routes_user_id = find_edge(self.g, self.ep_user_id, str(user_id))
        
        history = set()
        for route in routes_user_id:
            history.add(self.vp_fsq_id[route.source()])
            history.add(self.vp_fsq_id[route.target()])
            
        return list(history)
    
    def get_prefilter_time(self):
        return self.prefilter_time

    def get_category_stats(self):
        if not hasattr(self, '_category_stats'):
            categorias = set()
            for v in self.g.vertices():
                categorias.add(self.vp_category[v])
            self._category_stats = {
                'total_pois': self.g.num_vertices(),
                'total_categorias': len(categorias),
            }
        return self._category_stats