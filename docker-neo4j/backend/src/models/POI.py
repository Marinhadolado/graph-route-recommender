class POI:

    def __init__(self,fsq_id, latitude, longitude, category=None, 
                 category_lvlFs=None, price=None, rating=None, 
                 total_ratings=None, total_tips=None, **kwargs):
        self.id= str(fsq_id)

        if latitude is not None and str(latitude) != "":
            self.latitude = float(latitude)
        else:
            self.latitude = 0.0

        if longitude is not None and str(longitude) != "":
            self.longitude = float(longitude)
        else:
            self.longitude = 0.0

        if category is not None:
            self.category = str(category)
        else:
            self.category = "Unknown"

        if category_lvlFs is not None:
            self.category_lvlFs = str(category_lvlFs)
        else:
            self.category_lvlFs = ""

        if price is not None and str(price) != "":
            self.price = int(price)
        else:
            self.price = None

        if rating is not None and str(rating) != "" and float(rating) != -1.0:
            self.rating = float(rating)
        else:
            self.rating = None

        if total_ratings is not None and str(total_ratings) != "":
            self.total_ratings = int(total_ratings)
        else:
            self.total_ratings = 0

        if total_tips is not None and str(total_tips) != "":
            self.total_tips = int(total_tips)
        else:
            self.total_tips = 0

        self.schedule = {
            "Weekday": {},
            "Weekend": {}
        }

        # para el horario
        # Weekday
        val_w_em = kwargs.get('Weekday_EarlyMorning')
        if val_w_em is not None and str(val_w_em) != "":
            self.schedule["Weekday"]["EarlyMorning"] = int(val_w_em)
        else:
            self.schedule["Weekday"]["EarlyMorning"] = 0

        val_w_m = kwargs.get('Weekday_Morning')
        if val_w_m is not None and str(val_w_m) != "":
            self.schedule["Weekday"]["Morning"] = int(val_w_m)
        else:
            self.schedule["Weekday"]["Morning"] = 0

        val_w_a = kwargs.get('Weekday_Afternoon')
        if val_w_a is not None and str(val_w_a) != "":
            self.schedule["Weekday"]["Afternoon"] = int(val_w_a)
        else:
            self.schedule["Weekday"]["Afternoon"] = 0

        val_w_n = kwargs.get('Weekday_Night')
        if val_w_n is not None and str(val_w_n) != "":
            self.schedule["Weekday"]["Night"] = int(val_w_n)
        else:
            self.schedule["Weekday"]["Night"] = 0

        # Weekend
        val_we_em = kwargs.get('Weekend_EarlyMorning')
        if val_we_em is not None and str(val_we_em) != "":
            self.schedule["Weekend"]["EarlyMorning"] = int(val_we_em)
        else:
            self.schedule["Weekend"]["EarlyMorning"] = 0

        val_we_m = kwargs.get('Weekend_Morning')
        if val_we_m is not None and str(val_we_m) != "":
            self.schedule["Weekend"]["Morning"] = int(val_we_m)
        else:
            self.schedule["Weekend"]["Morning"] = 0

        val_we_a = kwargs.get('Weekend_Afternoon')
        if val_we_a is not None and str(val_we_a) != "":
            self.schedule["Weekend"]["Afternoon"] = int(val_we_a)
        else:
            self.schedule["Weekend"]["Afternoon"] = 0

        val_we_n = kwargs.get('Weekend_Night')
        if val_we_n is not None and str(val_we_n) != "":
            self.schedule["Weekend"]["Night"] = int(val_we_n)
        else:
            self.schedule["Weekend"]["Night"] = 0
    
    def __str__(self):
        return f"POI: {self.category} ({self.id})"

    @staticmethod
    def nodeToPOI(node):
        """
        Método de fábrica para crear un POI directamente desde un nodo de Neo4j.
        """
        props = dict(node)
        
        return POI(
            fsq_id=props.get('fsq_id'),
            latitude=props.get('latitude'),
            longitude=props.get('longitude'),
            category=props.get('category'),
            category_lvlFs=props.get('category_lvlFs'),
            price=props.get('price'),
            rating=props.get('rating'),
            total_ratings=props.get('total_ratings'),
            total_tips=props.get('total_tips'),
            **props 
        )  
    
    def getLocation(self):
        return (self.latitude, self.longitude)

