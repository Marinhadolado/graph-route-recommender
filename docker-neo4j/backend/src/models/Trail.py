from datetime import datetime

class Context:
    def __init__(self, temp=None, conditions=None, precip=None, windspeed=None, preciptype=None):
        if temp is not None:    
            self.temp= float(temp)  
        else: 
            self.temp= None

        if conditions:
            self.conditions = str(conditions) 
        else:
            self.conditions= None

        if precip is not None:
            self.precip = float(precip)  
        else:
            self.precip= 0.0

        if windspeed is not None:
            self.windspeed = float(windspeed) 
        else:
            self.windspeed= 0.0
        
        if preciptype is not None:
            self.preciptype = str(preciptype) 
        else:
            self.preciptype= None

    def __str__(self):
        return f"Context: {self.temp}°C, {self.conditions}"

class Step:
    def __init__(self, poi_id,timestamp, c: Context):
        self.venue_id= str(poi_id)

        #para guardar timestamp que es de tipo datetime debemos hacer lo siguiente
        if isinstance(timestamp, str):
            try:
                self.timestamp= datetime.fromisocalendar(timestamp)
            except ValueError:
                #si falla el formato lo guardamos tal cual
                self.timestamp=timestamp
        else:
            self.timestamp=timestamp

        if c:
            self.context= c
        else:
            self.context= Context()

    
    def __str__(self):
        return f"Step: {self.poi_id} ({self.timestamp})"

class Trail:

    def __init__(self, trail_id, user_id):
        self.trail_id= str(trail_id)
        self.user_id= str(user_id)
        # almacenará objetos tipo Step
        self.steps= []

    def __str__(self):
        return f"Trail {self.trail_id}, User: {self.user_id}, Steps: {len(self.steps)}"

    def __len__(self):
            return len(self.steps)

    def add_step(self, step: Step):
        """
        Añade un punto más a la ruta
        
        :param self
        :param step: poi con info que se añadirá a la ruta
        """
        if not isinstance(step, Step):
            raise TypeError(f"Se esperaba un Step, se recibió: {type(step)}") 
        
        self.steps.append(step)
        self.steps.sort(key=lambda x: x.timestamp)
    
    def get_duration(self):
        """
        Obtiene la duración de la ruta y la devuelte en minutos
        
        :param self
        """

        if len(self.steps)<2:
            return 0.0

        start_time= self.steps[0].timestamp
        end_time= self.steps[-1].timestamp  

        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            
            duration =end_time-start_time
            return duration.total_seconds()/60.0
        
        return 0.0
    
    def get_start(self):
        """
        Obtiene el primer punto de la ruta
        
        :param self
        """
        return self.steps[0].poi_id
    
    def get_poi_sequence(self):
        """
        Devuelve la lista de ids de los POIs en orden.

        :param self
        """
        pois=[]

        for step in self.steps:
            pois.append(step.poi_id)

        return pois

    


