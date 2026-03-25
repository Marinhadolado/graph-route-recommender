from .GTGraph import GTGraph
import graph_tool.all as gt
import os
from persistencia.Neo4jConnection import Neo4jConnection

class GraphRepository:
    """Clase que coge el grafo de memoria ya cargado y lo devuelve"""
    
    #variables de clase para mantener el grafo cargado en memoria
    _loaded_graph=None
    _is_loaded = False

    def __init__(self, city_name):
        self.city_name = city_name
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.graph_path = os.path.join(base_dir, "..","..", "..", "import", self.city_name, f"{self.city_name}.gt")


    def getGraph(self):
        """Trae los datos de Neo4j y construye el grafo en memoria."""
        
        if GraphRepository._is_loaded:
            return GraphRepository._loaded_graph
        
        if not os.path.exists(self.graph_path):
            raise FileNotFoundError(f"[GraphRepository] ERROR: No se encontró el grafo en {self.graph_path}. ¡Ejecuta GraphBuilder.py primero!")
        
        print(f"[GraphRepository] Cargando grafo desde {self.graph_path}...")
        
        # función de graphtool para cargar rápido el grafo de carpeta
        graph_lg = gt.load_graph(self.graph_path)
        
        # hacemos que sea de tipo GTGraph para ejecutar los algoritmos
        mi_gt_graph = GTGraph()
        mi_gt_graph.g = graph_lg
        
        # cargamos las variables del grafo de graphtool al de GTGraph
        mi_gt_graph.vp_fsq_id = graph_lg.vp["fsq_id"]
        mi_gt_graph.vp_lat = graph_lg.vp["latitude"]
        mi_gt_graph.vp_lon = graph_lg.vp["longitude"]
        mi_gt_graph.vp_category = graph_lg.vp["category"]
        mi_gt_graph.vp_price = graph_lg.vp["price"]
        mi_gt_graph.vp_rating = graph_lg.vp["rating"]
        mi_gt_graph.vp_total_ratings = graph_lg.vp["total_ratings"]
        mi_gt_graph.vp_total_tips = graph_lg.vp["total_tips"]
        mi_gt_graph.vp_category_lvlFs = graph_lg.vp["category_lvlFs"]
        mi_gt_graph.vp_city = graph_lg.vp["city"]

        mi_gt_graph.vp_wk_em = graph_lg.vp["Weekday_EarlyMorning"]
        mi_gt_graph.vp_wk_m = graph_lg.vp["Weekday_Morning"]
        mi_gt_graph.vp_wk_a = graph_lg.vp["Weekday_Afternoon"]
        mi_gt_graph.vp_wk_n = graph_lg.vp["Weekday_Night"]
        mi_gt_graph.vp_we_em = graph_lg.vp["Weekend_EarlyMorning"]
        mi_gt_graph.vp_we_m = graph_lg.vp["Weekend_Morning"]
        mi_gt_graph.vp_we_a = graph_lg.vp["Weekend_Afternoon"]
        mi_gt_graph.vp_we_n = graph_lg.vp["Weekend_Night"]
        
        mi_gt_graph.ep_user_id = graph_lg.ep["user_id"]
        mi_gt_graph.ep_trail_id = graph_lg.ep["trail_id"]

        mi_gt_graph.ep_p1_timestamp = graph_lg.ep["p1_timestamp"]
        mi_gt_graph.ep_p1_temp = graph_lg.ep["p1_temp"]
        mi_gt_graph.ep_p1_precip = graph_lg.ep["p1_precip"]
        mi_gt_graph.ep_p1_windspeed = graph_lg.ep["p1_windspeed"]
        mi_gt_graph.ep_p1_conditions = graph_lg.ep["p1_conditions"]
        mi_gt_graph.ep_p1_preciptype = graph_lg.ep["p1_preciptype"]

        mi_gt_graph.ep_p2_timestamp = graph_lg.ep["p2_timestamp"]
        mi_gt_graph.ep_p2_temp = graph_lg.ep["p2_temp"]
        mi_gt_graph.ep_p2_precip = graph_lg.ep["p2_precip"]
        mi_gt_graph.ep_p2_windspeed = graph_lg.ep["p2_windspeed"]
        mi_gt_graph.ep_p2_conditions = graph_lg.ep["p2_conditions"]
        mi_gt_graph.ep_p2_preciptype = graph_lg.ep["p2_preciptype"]

        mi_gt_graph.ep_time_diff = graph_lg.ep["time_diff"]
        
        # reconstruimos el diccionario id_map para getNeighbors más eficiente
        for v in mi_gt_graph.g.vertices():
            fsq_id = mi_gt_graph.vp_fsq_id[v]
            mi_gt_graph.id_map[fsq_id] = v

        # guardamos todo lo recuperado de la carpeta en una "caché"
        GraphRepository._loaded_graph = mi_gt_graph
        GraphRepository._is_loaded = True
        
        print("[GraphRepository] ¡Grafo listo!")
        return GraphRepository._loaded_graph
    

