from treelib import Tree

class TreeRoute:
    
    def __init__(self, poi_inicial):
        # creamos el arbol vacío y ponemos el POI inicial como raíz en nuestro caso el POI
        # con id fsq_id= 4abe7f9ef964a520068e20e3
        
        # primero establecemos los argumentos de treeroute siendo estos el propio árbol
        self.tree = Tree()
        # luego inicializamos el historial de nodos visitados como un conjunto vacío
        # history se crea para evitar bucles en la ruta
        self.history = set()
        
        # establecemos el nodo raíz del árbol con el POI inicial
        self.tree.create_node(
            tag=f"{poi_inicial['category']} ({poi_inicial['fsq_id']})", # Ej: "Retail (3fd66...)"
            identifier=poi_inicial['fsq_id'],
            data=poi_inicial # Guarda toda la info del POI (lat, lon, rating...)
        )
        self.history.add(poi_inicial['fsq_id'])

    #para hacer un print del arbol actual
    def __str__(self):
        return str(self.tree)
    
    def get_tree(self):
        return self.tree
    
    def get_history(self):
        return self.history
    
    def agregarPoi(self, poi_padre_id, nuevo_poi, datos_relacion):
        
        nuevo_poi_id = nuevo_poi['fsq_id']

        # primero comprobamos si este nodo ya existe en el árbol
        if not self.tree.contains(nuevo_poi_id):
            
            # para evitar bucles buscamos si ya está en la ruta del padre
            path_to_parent = set(self.tree.rsearch(poi_padre_id))
            if nuevo_poi_id in path_to_parent:
                return False

            # si no hay bucle, creamos el nuevo nodo
            self.tree.create_node(
                tag=f"{nuevo_poi['category']} ({nuevo_poi_id})",
                identifier=nuevo_poi_id,
                parent=poi_padre_id,
                data={
                    'poi_data': nuevo_poi,
                    'edge_data': datos_relacion
                }
            )
        
        return True
    
    def get_all_paths(self):
        # devuelve todas las rutas desde la raíz hasta las hojas
        rutas = []
        # 'leaves()' nos da todos los nodos que son finales de un camino
        for hoja in self.tree.leaves():
            # Ignora si el árbol solo tiene la raíz
            if hoja.is_root():
                continue
                
            # 'rsearch(hoja.identifier)' nos da la lista de IDs desde la hoja hasta la raíz
            ids_en_ruta = list(self.tree.rsearch(hoja.identifier))
            ids_en_ruta.reverse() # Le damos la vuelta para tener [inicio, p1, p2, final]
            
            # Obtenemos los objetos Nodo completos
            nodos_en_ruta = [self.tree.get_node(nid) for nid in ids_en_ruta]
            rutas.append(nodos_en_ruta)
            
        return rutas
