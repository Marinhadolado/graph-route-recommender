from treelib import Tree
from POI import POI
from Trail import Trail, Step, Context

class TreeRoute:
    
    def __init__(self, initial_poi):
        """
        Inicializamos el árbol vacío con un POI como raiz 

        :param self: Descripción
        :param initial_poi: POI inicial
        """
        # comprobamos que root_poi sea de tipo POI
        if not isinstance(initial_poi, POI):
            raise TypeError("[TREE ROUTE] Root debe de ser de tipo POI")
        
        self.tree = Tree()
        self.root = initial_poi.getId()
        
        # establecemos el nodo raíz del árbol con el POI inicial
        self.tree.create_node(
            tag=f"{initial_poi.getCategory} ({initial_poi.getId()})",
            identifier=initial_poi.getId(),
            data={
                'poi': initial_poi,
                'edge_data': None
            }
        )

    #para hacer un print del arbol actual
    def __str__(self):
        return str(self.tree)

    def getRoot(self):
        return self.root

    def getTree(self):
        return self.tree
    
    def agregarPoi(self, poi_padre_id, nuevo_poi, datos_relacion):
        """
        Añade un nuevo POI como hijo de un nodo existente.

        :param self: Descripción
        :param poi_padre_id: Id del nodo padre
        :param nuevo_poi: POI hijo
        :param datos_relacion: Diccionario con info de la relación
        """
        
        if not isinstance(nuevo_poi, POI):
            print(f"[TreeRoute] Error: Se intentó añadir algo que no es un POI: {type(nuevo_poi)}")
            return False
        
        nuevo_poi_id = nuevo_poi.getId()

        # primero comprobamos si este nodo ya existe en el árbol
        if not self.tree.contains(nuevo_poi_id):
            
            # para evitar bucles buscamos si ya está en la ruta del padre
            path_to_parent = set(self.tree.rsearch(poi_padre_id))
            if nuevo_poi_id in path_to_parent:
                #vemos que hay un bucle y no lo añadimos
                return False

            # si no hay bucle, creamos el nuevo nodo
            self.tree.create_node(
                tag=f"{nuevo_poi.getCategory} ({nuevo_poi_id})",
                identifier=nuevo_poi_id,
                parent=poi_padre_id,
                data={
                    'poi': nuevo_poi,
                    'edge_data': datos_relacion
                }
            )
        
        return True
    
    def getAllPaths(self):
        """
        Obtenemos todas las rutas completas desde la raiz donde cada ruta es una lista de nodos
        
        :param self: Descripción
        """
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
            
            # Como la raíz no tiene 'edge_data', miramos el último nodo o el primer hijo para sacar el ID de la ruta real.
            trail_id = "unknown_trail"
            user_id = "unknown_user"
            
            edge_data_hoja = hoja.data.get('edge_data')
            if edge_data_hoja:
                trail_id = edge_data_hoja.get('trail_id', "unknown_trail")
                user_id = edge_data_hoja.get('user_id', "unknown_user")

            nueva_ruta = Trail(trail_id, user_id)
            
            # Obtenemos los objetos Nodo completos
            for nid in ids_en_ruta:
                nodo= self.tree.get_node(nid)
                poi = nodo.data['poi']
                edge_data = nodo.data['edge_data']

                if edge_data:
                    timestamp = edge_data.get('timestamp') # O como se llame en tu BD (p1_timestamp?)
                    
                    context = Context(
                        temp=edge_data.get('temp'),
                        conditions=edge_data.get('conditions'),
                        precip=edge_data.get('precip'),
                        windspeed=edge_data.get('windspeed'),
                        preciptype=edge_data.get('preciptype')
                    )
                else:
                    # Es la raíz asumimos contexto vacío o timestamp actual
                    pass
                
                step = Step(    
                    poi_origen=poi.getId(), # O pasa el objeto entero si cambias Step
                    timestamp=timestamp,
                    c=context
                )

                nueva_ruta.addStep(step)
    
            rutas.append(nueva_ruta)
            
        return rutas
    
    def getNumChildren(self, poi_id):
        """Devuelve el número de hijos directos de un nodo."""

        if self.tree.contains(poi_id):
            return len(self.tree.children(poi_id))
        
        return 0
