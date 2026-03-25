from graph_tool.all import Graph, GraphView
from datetime import datetime
from graph_tool.util import find_edge

class GTGraph:
    def __init__(self):
        self.g = Graph(directed=True)
        

        # vertice poi
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

        # (horario datos)
        self.vp_wk_em = self.g.new_vertex_property("int") # Weekday EarlyMorning
        self.g.vp["Weekday_EarlyMorning"] = self.vp_wk_em

        self.vp_wk_m = self.g.new_vertex_property("int")  # Weekday Morning
        self.g.vp["Weekday_Morning"] = self.vp_wk_m

        self.vp_wk_a = self.g.new_vertex_property("int")  # Weekday Afternoon
        self.g.vp["Weekday_Afternoon"] = self.vp_wk_a

        self.vp_wk_n = self.g.new_vertex_property("int")  # Weekday Night
        self.g.vp["Weekday_Night"] = self.vp_wk_n

        self.vp_we_em = self.g.new_vertex_property("int") # Weekend EarlyMorning
        self.g.vp["Weekend_EarlyMorning"] = self.vp_we_em

        self.vp_we_m = self.g.new_vertex_property("int")  # Weekend Morning
        self.g.vp["Weekend_Morning"] = self.vp_we_m

        self.vp_we_a = self.g.new_vertex_property("int")  # Weekend Afternoon
        self.g.vp["Weekend_Afternoon"] = self.vp_we_a

        self.vp_we_n = self.g.new_vertex_property("int")  # Weekend Night
        self.g.vp["Weekend_Night"] = self.vp_we_n
        
        # aristas datos
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

        # Mapas para traducción rápida (O(1)) entre fsq_id y vértices
        self.id_map = {} 
        
    def _parse_date(self, date_str):
        if not date_str or date_str == 'None' or date_str == '':
            return 0.0
        try:
            # Convierte '2018-07-30T20:03:00' a objeto datetime y luego a timestamp
            dt = datetime.fromisoformat(str(date_str).replace('Z', ''))
            return float(dt.timestamp())
        except ValueError:
            return 0.0
        
    def addNode(self, poi_data):
        """Añade un nodo al grafo si no existe."""
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
        """Crea una conexión entre dos POIs."""
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
            self.ep_p2_conditions[e] = str(rel_data.get('p2_conditions', ''))
            self.ep_p2_preciptype[e] = str(rel_data.get('p2_preciptype', ''))

            self.ep_time_diff[e] = float(rel_data.get('time_diff', 0.0))
    
    #def getNeighbors(self, fsq_id):
    #    """Devuelve una lista de fsq_id de los vecinos del nodo dado por fsq_id."""
    #    if fsq_id not in self.id_map: 
    #        return []
    #    v = self.id_map[fsq_id]
#
    #    neighbors=[]
#
    #    for n in v.out_neighbors():
    #        neighbors.append(self.vp_fsq_id[n])
#
    #    return neighbors
    
    def getFilteredNeighbors(self, fsq_id, pois_evitar, context):
        """
        Devuelve vecinos filtrados por historial y contexto usando GraphView en O(1).
        """
        if fsq_id not in self.id_map:
            return []

        v_actual = self.id_map[fsq_id]

        # primero los pois que querramos evitar los ocultamos con un filtro bool
        v_filter = self.g.new_vertex_property("bool", val=True)
        if pois_evitar:
            for poi_id in pois_evitar:
                if poi_id in self.id_map:
                    v_filter[self.id_map[poi_id]] = False

        v_filter[v_actual] = True

        # ahora si tenemos contexto de condiciones meteorológicas, ocultamos también las aristas que no cumplan la condición
        e_filter = self.g.new_edge_property("bool", val=True)
        if context:
            for e in v_actual.out_edges():
                es_arista_valida = True
                
                # Comprobamos todos los posibles filtros dinámicamente
                if 'conditions' in context and self.ep_p1_conditions[e] != str(context['conditions']):
                    es_arista_valida = False
                    
                if 'preciptype' in context and self.ep_p1_preciptype[e] != str(context['preciptype']):
                    es_arista_valida = False
                    
                if 'temp' in context and self.ep_p1_temp[e] != float(context['temp']):
                    es_arista_valida = False
                    
                if 'precip' in context and self.ep_p1_precip[e] != float(context['precip']):
                    es_arista_valida = False
                    
                if 'windspeed' in context and self.ep_p1_windspeed[e] != float(context['windspeed']):
                    es_arista_valida = False

                # Si falla cualquiera de las condiciones, ocultamos la ruta
                e_filter[e] = es_arista_valida

        # hacemos la vista del grafo con los filtros aplicados(elimina los vertices sin afectar a los índices originales)
        subgrafo = GraphView(self.g, vfilt=v_filter, efilt=e_filter)

        # obtenemos los vecinos del nodo actual en el subgrafo
        neighbors = []
        v_subgrafo = subgrafo.vertex(v_actual)
        
        for n in v_subgrafo.out_neighbors():
            neighbors.append(self.vp_fsq_id[n])

        return neighbors
    
    def getCityName(self):
        """Devuelve el nombre de la ciudad leyendo el primer nodo del grafo"""
        if self.g.num_vertices() > 0:
            primer_vertice = self.g.vertex(0)
            return self.vp_city[primer_vertice]
        return "NOCITY"
    
    def getUserHistory(self, user_id):
        """Devuelve una lista de fsq_id que el usuario ya ha visitado históricamente."""
        
        # Busca todas las relaciones que pertenecen a este usuario
        rutas_user_id = find_edge(self.g, self.ep_user_id, str(user_id))
        
        historial = set()
        for ruta in rutas_user_id:
            historial.add(self.vp_fsq_id[ruta.source()])
            historial.add(self.vp_fsq_id[ruta.target()])
            
        return list(historial)