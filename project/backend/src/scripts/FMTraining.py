import pandas as pd
from surprise import Dataset, Reader, NMF
import pickle
import os

def entrenar_nmf(city_name):
    print(f"=== STARTING TRAINING FOR {city_name} ===")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_file = os.path.join(base_dir, '..', '..', 'dataset', 'train.csv')
    output_file = os.path.join(base_dir, '..', '..', 'dataset', f'fm_{city_name}.pkl')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print("[FMTraining] Reading train.csv...")

    df = pd.read_csv(train_file, dtype=str)
    df['rating'] = 1.0 
    
    df_surprise = df[['user_id', 'poi_id', 'rating']]

    print("[FMTraining] Loading data in Surprise format...")
    reader = Reader(rating_scale=(0, 1))
    data = Dataset.load_from_df(df_surprise, reader)
    trainset = data.build_full_trainset()

    print("[FMTraining] Training NMF model (This may take a few seconds/minutes)...")
    nmf = NMF(n_factors=192, random_state=42) 
    nmf.fit(trainset)

    print("[FMTraining] Extracting latent factor matrices...")
    user_factors = nmf.pu
    item_factors = nmf.qi    

    user_map = {trainset.to_raw_uid(i): i for i in trainset.all_users()}
    item_map = {trainset.to_raw_iid(i): i for i in trainset.all_items()}

    modelo_empaquetado = {
        'user_factors': user_factors,
        'item_factors': item_factors,
        'user_map': user_map,
        'item_map': item_map
    }

    with open(output_file, 'wb') as f:
        pickle.dump(modelo_empaquetado, f)
        
    print(f"=== TRAINING COMPLETED. Model saved in {output_file} ===")

if __name__ == "__main__":
    entrenar_nmf("Tokyo")