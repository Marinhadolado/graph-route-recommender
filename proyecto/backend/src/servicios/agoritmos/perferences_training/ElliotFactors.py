import pandas as pd
import os
from elliot.run import run_experiment

def preparar_dataset_elliot(city_name="Tokyo"):
    print(f"=== PREPARANDO DATOS PARA ELLIOT: {city_name} ===")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Subimos 4 niveles: perferences_training -> agoritmos -> servicios -> src -> backend
    input_csv = os.path.abspath(os.path.join(base_dir, '../../../../dataset/train.csv'))
    output_tsv = os.path.abspath(os.path.join(base_dir, '../../../../dataset/', f'elliot_train_{city_name}.tsv'))
    
    if not os.path.exists(input_csv):
        print(f"ERROR: No se encuentra el archivo original en {input_csv}")
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
        print(f" -> Procesadas {procesados} filas...", end='\r')

    print(f"\n=== COMPLETADO: {output_tsv} ===")

def main():
    # 1. Generar TSV
    preparar_dataset_elliot("Tokyo")

    # 2. Ejecutar Elliot
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Usamos el nombre que tienes en tu carpeta: ElliotTraining.yaml
    yaml_path = os.path.join(base_dir, 'ElliotTraining.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"ERROR: No se encuentra el archivo YAML en {yaml_path}")
        return

    print(f"=== INICIANDO ELLIOT CON {yaml_path} ===")
    run_experiment(yaml_path)
    print("=== EXPERIMENTO FINALIZADO ===")

if __name__ == "__main__":
    main()