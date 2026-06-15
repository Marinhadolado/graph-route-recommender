from graph_tool.all import Graph, GraphView
from datetime import datetime
from graph_tool.util import find_edge
import time

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
        self.ep_p1_time_segment = self.g.new_edge_property("string")
        self.g.ep["p1_time_segment"] = self.ep_p1_time_segment

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
        self.tiempo_prefiltrado = 0.0
        self.n_prefiltrado = 0

    def reset_prefilter_timer(self):
        self.tiempo_prefiltrado = 0.0
        self.n_prefiltrado = 0
        
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
            self.ep_p1_time_segment[e] = str(rel_data.get('p1_time_segment', ''))

            self.ep_p2_temp[e] = float(rel_data.get('p2_temp', 0.0))
            self.ep_p2_precip[e] = float(rel_data.get('p2_precip', 0.0))
            self.ep_p2_windspeed[e] = float(rel_data.get('p2_windspeed', 0.0))
            self.ep_p2_conditions[e] = str(rel_data.get('p2_conditions', ''))
            self.ep_p2_preciptype[e] = str(rel_data.get('p2_preciptype', ''))
            self.ep_time_diff[e] = float(rel_data.get('time_diff', 0.0))

            return True
        print(f"[GTGraph] The relationship from {from_id} to {to_id} could not be added because one of the nodes does not exist in the graph.")
        if from_id not in self.id_map:
            print(f" - Source node not found: {from_id}")
        if to_id not in self.id_map:
            print(f" - Destination node not found: {to_id}")
        return False
    
    def getFilteredNeighbors(self, fsq_id, pois_avoid, context):
        """ Returns a list of neighboring POIs (fsq_id) for a given POI, applying filters to exclude certain POIs and/or relationships based on the provided context. """
        t0 = time.perf_counter()
        try:
            if fsq_id not in self.id_map:
                return []

            current_v = self.id_map[fsq_id]

            v_filter = self.g.new_vertex_property("bool", val=True)
            if pois_avoid:
                for poi_id in pois_avoid:
                    if poi_id in self.id_map:
                        v_filter[self.id_map[poi_id]] = False

            if context and 'time_segment' in context:
                franja_a_vp = {
                    "Weekday_EarlyMorning": self.vp_wk_em, "Weekday_Morning": self.vp_wk_m,
                    "Weekday_Afternoon":    self.vp_wk_a,  "Weekday_Night":   self.vp_wk_n,
                    "Weekend_EarlyMorning": self.vp_we_em, "Weekend_Morning": self.vp_we_m,
                    "Weekend_Afternoon":    self.vp_we_a,  "Weekend_Night":   self.vp_we_n,
                }
                vp_franja = franja_a_vp.get(str(context['time_segment']))
                if vp_franja is not None:
                    for n in current_v.out_neighbors():
                        if vp_franja[n] == 0:
                            v_filter[n] = False

            v_filter[current_v] = True
        
            e_filter = self.g.new_edge_property("bool", val=True)
            if context:
                for e in current_v.out_edges():
                    is_valid_rel = True

                    if 'conditions' in context and self.ep_p1_conditions[e] != str(context['conditions']):
                        is_valid_rel = False
                        
                    if 'preciptype' in context and self.ep_p1_preciptype[e] != str(context['preciptype']):
                        is_valid_rel = False
                        
                    if 'temp' in context and self.ep_p1_temp[e] != float(context['temp']):
                        is_valid_rel = False
                        
                    if 'precip' in context and self.ep_p1_precip[e] != float(context['precip']):
                        is_valid_rel = False
                        
                    if 'windspeed' in context and self.ep_p1_windspeed[e] != float(context['windspeed']):
                        is_valid_rel = False

                    e_filter[e] = is_valid_rel

            subgrafo = GraphView(self.g, vfilt=v_filter, efilt=e_filter)

            neighbors = []
            v_subgrafo = subgrafo.vertex(current_v)
            
            for n in v_subgrafo.out_neighbors():
                neighbors.append(self.vp_fsq_id[n])

            return neighbors
        finally:
            self.tiempo_prefiltrado += (time.perf_counter() - t0)
            self.n_prefiltrado += 1
    
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