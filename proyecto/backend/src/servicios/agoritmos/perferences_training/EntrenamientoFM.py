import pandas as pd
from surprise import Dataset, Reader, NMF
import pickle
import os

def entrenar_nmf(city_name):
    print(f"=== INICIANDO ENTRENAMIENTO PARA {city_name} ===")
    
    # Rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_file = os.path.join(base_dir, '..', '..', '..', '..', 'dataset', 'train.csv')
    output_file = os.path.join(base_dir, '..', '..', '..', '..', 'dataset', f'fm_{city_name}.pkl')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print("[EntrenamientoFM] Leyendo train.csv...")

    # leemos el train.csv con pandas
    df = pd.read_csv(train_file, dtype=str)
    # si el usuario visitó el poi, le damos un suponemos que le gusta y le damos un rating de 1.0
    df['rating'] = 1.0 
    
    # creamos las 3 columnas para el archivo
    df_surprise = df[['user_id', 'poi_id', 'rating']]

    print("[EntrenamientoFM] Cargando datos en el formato de Surprise...")
    reader = Reader(rating_scale=(0, 1))
    data = Dataset.load_from_df(df_surprise, reader)
    trainset = data.build_full_trainset()

    # una vez cargados los datos, entrenamos el algoritmo NMF (Non-negative Matrix Factorization)
    print("[EntrenamientoFM] Entrenando modelo NMF (Esto puede tardar unos segundos/minutos)...")
    # suponemos un n 15
    # 10 50 100
    nmf = NMF(n_factors=192, random_state=42) 
    nmf.fit(trainset)

    # extraemos las matrices y los diccionarios traductores
    print("[EntrenamientoFM] Extrayendo matrices de factores latentes...")
    user_factors = nmf.pu  # Matriz Usuarios
    item_factors = nmf.qi  # Matriz POIs
    
    # Diccionarios para traducir el ID de Foursquare (String) a la fila de la matriz (Int)
    user_map = {trainset.to_raw_uid(i): i for i in trainset.all_users()}
    item_map = {trainset.to_raw_iid(i): i for i in trainset.all_items()}

    # Empaquetamos todo en un diccionario
    modelo_empaquetado = {
        'user_factors': user_factors,
        'item_factors': item_factors,
        'user_map': user_map,
        'item_map': item_map
    }

    # guardamos la matriz de factores latentes en un archivo
    with open(output_file, 'wb') as f:
        pickle.dump(modelo_empaquetado, f)
        
    print(f"=== ENTRENAMIENTO FINALIZADO. Modelo guardado en {output_file} ===")

if __name__ == "__main__":
    entrenar_nmf("Tokyo")