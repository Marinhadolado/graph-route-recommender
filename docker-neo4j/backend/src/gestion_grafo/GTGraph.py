from graph_tool.all import Graph

class GTGraph:
    def __init__(self):
        self.g = Graph(directed=True)
        
        # declaramos una propiedad de vértice para almacenar el fsq_id de cada POI
        self.fsq_ids = self.g.new_vertex_property("string")
        self.g.vertex_properties["fsq_id"] = self.fsq_ids
        
        # Mapas para traducción rápida (O(1)) entre fsq_id y vértices
        self.id_map = {} 
        
    def addNode(self, fsq_id, properties=None):
        """Añade un nodo al grafo si no existe."""
        if fsq_id not in self.id_map:
            v = self.g.add_vertex()
            self.id_map[fsq_id] = v
            self.fsq_ids[v] = fsq_id
            return v
        return self.id_map[fsq_id]

    def addEdge(self, from_id, to_id):
        """Crea una conexión entre dos POIs."""
        if from_id in self.id_map and to_id in self.id_map:
            self.g.add_edge(self.id_map[from_id], self.id_map[to_id])

    def getNeighbors(self, fsq_id):
        """Retorna una lista de fsq_id vecinos."""
        if fsq_id not in self.id_map: return []
        v = self.id_map[fsq_id]
        return [self.fsq_ids[n] for n in v.out_neighbors()]
    
    def getShortestPath(self, start_id, end_id):
        """Calcula el camino más corto."""
        from graph_tool.all import shortest_path
        if start_id not in self.id_map or end_id not in self.id_map:
            return []
        
        path, _ = shortest_path(self.g, source=self.id_map[start_id], 
                                target=self.id_map[end_id])
        return [self.fsq_ids[v] for v in path]