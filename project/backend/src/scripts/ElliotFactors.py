import pandas as pd
import os
from elliot.run import run_experiment

def preparar_dataset_elliot(city_name="Tokyo"):
    print(f"=== PREPARING DATA FOR ELLIOT: {city_name} ===")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.abspath(os.path.join(base_dir, '../../dataset/train.csv'))
    output_tsv = os.path.abspath(os.path.join(base_dir, '../../dataset/', f'elliot_train_{city_name}.tsv'))
    
    if not os.path.exists(input_csv):
        print(f"ERROR: File not found {input_csv}")
        return

    chunk_size = 100000 
    if os.path.exists(output_tsv):
        os.remove(output_tsv)
        
    procesados = 0
    for chunk in pd.read_csv(input_csv, dtype=str, usecols=['user_id', 'poi_id', 'timestamp'], chunksize=chunk_size):
        df_elliot = pd.DataFrame()
        df_elliot['user_id'] = chunk['user_id']
        df_elliot['item_id'] = chunk['poi_id']
        df_elliot['rating'] = 1.0
        
        fechas = pd.to_datetime(chunk['timestamp'], errors='coerce')
        df_elliot['timestamp'] = fechas.astype('int64') // 10**9 
        
        df_elliot.to_csv(output_tsv, sep='\t', index=False, header=False, mode='a')
        procesados += len(chunk)
        print(f" -> Processed {procesados} rows...", end='\r')

    print(f"\n=== DONE: {output_tsv} ===")

def main():
    preparar_dataset_elliot("Tokyo")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(base_dir, 'ElliotTraining.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"ERROR: File not found {yaml_path}")
        return

    print(f"=== STARTING ELLIOT WITH {yaml_path} ===")
    run_experiment(yaml_path)
    print("=== EXPERIMENT COMPLETED ===")

if __name__ == "__main__":
    main()