import pandas as pd
import os

def preparar_dataset_elliot(city_name="Tokyo"):
    print(f"=== PREPARANDO DATOS PARA ELLIOT: {city_name} ===")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, '..', '..', '..', '..', 'dataset', 'train.csv')
    output_tsv = os.path.join(base_dir, '..', '..', '..', '..', 'dataset', f'elliot_train_{city_name}.tsv')
    
    #tamaño del bloque: lee de 100.000 en 100.000 filas
    chunk_size = 100000 
    
    #si el archivo ya existe, lo borramos para no añadir duplicados
    if os.path.exists(output_tsv):
        os.remove(output_tsv)
        
    procesados = 0
    print(f"Leyendo de: {input_csv}\nEscribiendo en: {output_tsv}")

    #leemos en chunks indicando solo las columnas que necesitamos para no malgastar memoria
    for chunk in pd.read_csv(input_csv, dtype=str, usecols=['user_id', 'poi_id', 'timestamp'], chunksize=chunk_size):
        
        df_elliot = pd.DataFrame()
        df_elliot['user_id'] = chunk['user_id']
        df_elliot['item_id'] = chunk['poi_id']
        
        #forzamos el rating a 1.0
        df_elliot['rating'] = 1.0
        
        #convertimos el timestamp ISO (2018-06-19T21:29:00) a UNIX Epoch (entero numérico)
        fechas = pd.to_datetime(chunk['timestamp'], errors='coerce')
        df_elliot['timestamp'] = fechas.astype('int64') // 10**9 
        
        # Guardamos el trozo en el tsv, sin encabezado y sin índice
        df_elliot.to_csv(output_tsv, sep='\t', index=False, header=False, mode='a')
        
        procesados += len(chunk)
        print(f" -> Procesadas {procesados} filas...", end='\r')

    print(f"\n=== COMPLETADO. Dataset listo para Elliot ===")

if __name__ == "__main__":
    preparar_dataset_elliot("Tokyo")