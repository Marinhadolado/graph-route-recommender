import os
import sys
import pandas as pd

from RouteGenerator import RouteGenerator

class LoadData:

    def __init__(self):
        self.db = RouteGenerator()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.import_path= os.path.join(base_dir, "../../import")

    def clearDB(self):
        """
        Vacia la base de datos
        
        :param self
        """
        print("[LoadData] Limpiando la base de datos...")
        driver= self.db.driver
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n;")

    def listCities(self):
        """
        Lista las carpetas disponibles
        """
        if not os.path.exists(self.import_path):
            os.makedirs(self.import_path)
            return []
        
        cities= []
        
        all_cities = os.listdir(self.import_path)

        for city in all_cities:
            full_path= os.path.join(self.import_path, city) 

            if os.path.isdir(full_path):
                cities.append(city)

        return cities

    def loadPOIs(self, filepath, city_name):
        """
        Carga los POIs a la base de datos.
        Usamos el método de batch para cargar los datos para que se más eficiente
        y menos rígido que la instruccion LOAD CSV. De esta forma procesamos los 
        datos por lotes de 2000 filas
        
        :param self
        :param filepath: archivo csv donde se encuentra toda la información 
        de los pois
        :param city_name: nombre de la ciudad cuyos pois se quieren poblar
        """

        # usamos la librería pandas para leer el csv más fácilmente como strings
        f = pd.read_csv(filepath, dtype=str)

        #antes de nada reemplazamos vacios por None
        data = f.fillna("").to_dict('records')

        query = """
        UNWIND $batch AS row

        CALL {
            WITH row
            WITH row WHERE row.fsq_id IS NOT NULL AND toFloat(row.latitude) <> -1.0 AND toFloat(row.longitude) <> -1.0
            MERGE (p:POI {fsq_id: row.fsq_id})
            SET
                p.latitude = CASE WHEN row.latitude <> '' THEN toFloat(row.latitude) END,
                p.longitude = CASE WHEN row.longitude <> '' THEN toFloat(row.longitude) END,
                p.category = row.category,
                p.price = CASE WHEN row.price <> '' THEN toInteger(row.price) END,
                p.rating = CASE WHEN row.rating <> '' THEN toFloat(row.rating) END,
                p.total_ratings = CASE WHEN row.total_ratings <> '' THEN toInteger(row.total_ratings) END,
                p.total_tips = CASE WHEN row.total_tips <> '' THEN toInteger(row.total_tips) END,
                p.Weekday_EarlyMorning = CASE WHEN row.Weekday_EarlyMorning <> '' THEN toInteger(row.Weekday_EarlyMorning) END,
                p.Weekday_Morning = CASE WHEN row.Weekday_Morning <> '' THEN toInteger(row.Weekday_Morning) END,
                p.Weekday_Afternoon = CASE WHEN row.Weekday_Afternoon <> '' THEN toInteger(row.Weekday_Afternoon) END,
                p.Weekday_Night = CASE WHEN row.Weekday_Night <> '' THEN toInteger(row.Weekday_Night) END,
                p.Weekend_EarlyMorning = CASE WHEN row.Weekend_EarlyMorning <> '' THEN toInteger(row.Weekend_EarlyMorning) END,
                p.Weekend_Morning = CASE WHEN row.Weekend_Morning <> '' THEN toInteger(row.Weekend_Morning) END,
                p.Weekend_Afternoon = CASE WHEN row.Weekend_Afternoon <> '' THEN toInteger(row.Weekend_Afternoon) END,
                p.Weekend_Night = CASE WHEN row.Weekend_Night <> '' THEN toInteger(row.Weekend_Night) END,
                p.category_lvlFs = row.category_lvlFs,
                p.city = 'NYC'
        } IN TRANSACTIONS;
        """

        print(f"    Procesando {len(data)} POIs...")
        # al ser archivos grandes con millones de datos vamos a ir leyendo por
        # filas de 10.000 en 10.000
        chunck_size= 10000 
        processed= 0

        with pd.read_csv(filepath, dtype=str, chunksize=chunck_size) as reader:
            driver= self.db.driver
            with driver.session() as session:

                for chunck in reader:
                    chunck = chunck.fillna("")

                    batch_data = chunck.to_dict('records')

                    session.run(query, batch=batch_data, cityName=city_name)

                    processed+= len(batch_data)

                    print(f"   -> Procesados {processed} POIs...", end='\r')

    def loadTrails(self, filepath, city_name):
        """
        Carga las relaciones a la base de datos

        :param self: Descripción
        :param filepath: archivo csv donde se encuentra toda la información 
        de las rutas y relaciones
        :param city_name: nombre de la ciudad cuyos pois se quieren poblar
        """  
        
        # 1. Leemos todo como String inicialmente para seguridad
        df = pd.read_csv(filepath, sep=';', dtype=str)
        
        print(f"   -> Archivo leído ({len(df)} filas). Preparando lógica de enlaces...")

        # 2. Convertimos Fechas a UTC (Vital para evitar el error de Mixed Timezones)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        # Convertimos números
        numeric_cols = ['temp', 'precip', 'windspeed']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # 3. Lógica de 'Siguiente Paso' (Python hace el trabajo duro)
        # Esto pone el destino en la misma fila que el origen.
        df['next_venue_id'] = df['venue_id'].shift(-1)
        df['next_timestamp'] = df['timestamp'].shift(-1)
        df['next_user_id'] = df['user_id'].shift(-1)
        df['next_trail_id'] = df['trail_id'].shift(-1)

        cols_props = ['temp', 'precip', 'windspeed', 'conditions', 'preciptype']
        for col in cols_props:
            if col in df.columns:
                df[f'next_{col}'] = df[col].shift(-1)

        # 4. Filtrado: Solo mantenemos filas donde el "siguiente" pertenece al mismo user/trail
        valid_rows = (df['user_id'] == df['next_user_id']) & \
                     (df['trail_id'] == df['next_trail_id']) & \
                     (df['venue_id'] != df['next_venue_id']) 

        df = df[valid_rows].copy()

        # 5. Calculamos duración en minutos
        df['time_diff_min'] = (df['next_timestamp'] - df['timestamp']).dt.total_seconds() / 60.0

        # Formato de Fechas para Neo4j (ISO String)
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        df['next_timestamp'] = df['next_timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Limpieza de nulos (Pandas NaN -> Python None)
        df = df.where(pd.notnull(df), None)

        # 6. Query SIMPLE. Como Python ya ha unido A con B en la misma fila,
        # la query no necesita hacer ordenaciones ni collect complejos.
        query = """
        UNWIND $batch AS row
        
        MATCH (p1:POI {fsq_id: row.venue_id})
        MATCH (p2:POI {fsq_id: row.next_venue_id})
        
        MERGE (u:User {user_id: toString(row.user_id)})
        
        CREATE (p1)-[v:VISITED {
            user_id: toString(row.user_id),
            trail_id: toString(row.trail_id),
            
            p1_timestamp: row.timestamp,
            p1_temp: toFloat(row.temp),
            p1_precip: toFloat(row.precip),
            p1_windspeed: toFloat(row.windspeed),
            p1_conditions: row.conditions,
            p1_preciptype: CASE WHEN row.preciptype IS NULL THEN '' ELSE toString(row.preciptype) END,

            p2_timestamp: row.next_timestamp,
            p2_temp: toFloat(row.next_temp),
            p2_precip: toFloat(row.next_precip),
            p2_windspeed: toFloat(row.next_windspeed),
            p2_conditions: row.next_conditions,
            p2_preciptype: CASE WHEN row.next_preciptype IS NULL THEN '' ELSE toString(row.next_preciptype) END,
            
            time_diff_min: toFloat(row.time_diff_min)
        }]->(p2)
        """

        batch_size = 5000
        total = len(df)
        print(f"    Procesando {total} relaciones...")

        driver= self.db.driver
        with driver.session() as session:
            for start in range(0, total, batch_size):
                end = start + batch_size
                batch = df.iloc[start:end].to_dict('records')
                session.run(query, batch=batch)
                print(f"      Progreso: {end}/{total}", end='\r')

        print("")

    def loadCity(self, city_name):
        print(f"[LoadData] --------- Loading data from city {city_name}---------")

        city_dir = os.path.join(self.import_path, city_name)
        if not os.path.exists(city_dir):
            print(f"[LoadData] ERROR no existe directorio: {city_dir}")
            return

        # una vez dentro de la carpeta de la ciudad obtenemos los csv
        city_files= os.listdir(city_dir)
        pois_file=None
        trail_file=None
        
        for file in city_files:

            if file == "pois.csv":
                pois_file= file
            elif file== "trail_train.csv":
                trail_file= file
            
        if pois_file is None or trail_file is None:
            print(f"[LoadData] ERROR: faltan archivos de la ciudad {city_name}")
            print("       Se requiere: 'pois.csv' y 'trail_train.csv'")
            return
        
        # antes de nada limpiar la base de datos
        self.clearDB()

        # ahora cargamos los POIS
        print("[LoadData] Cargando nodos...")
        self.loadPOIs(os.path.join(city_dir, pois_file), city_name)

        # ahora cargamos las relaciones
        print("[LoadData] Cargando relaciones...")
        self.loadTrails(os.path.join(city_dir, trail_file), city_name)

        print("[LoadData] DB POBLADA")

if __name__ == "__main__":
    ld= LoadData()
    cities= ld.listCities()

    if not cities:
        print(f"No se encontraron archivos para la carga de datos en {ld.import_path}")
        exit()

    print("\n=== SELECTOR DE CIUDAD ===")
    for i, city in enumerate(cities):
        print(f"{i + 1}. {city}")

    try:
        seleccion = int(input("\n> Elige una opción: ")) - 1
        if 0 <= seleccion < len(cities):
            ld.loadCity(cities[seleccion])
        else:
            print(" Opción no válida.")
    except ValueError:
        print("Por favor, introduce un número.")


