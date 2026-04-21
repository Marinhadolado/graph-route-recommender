import os
import glob
import pickle
import numpy as np
import csv

class ExtractorPesos:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Ruta a la carpeta de pesos generada por Elliot
        self.weights_dir = os.path.join(self.base_dir, "results")
        # Ruta a tu dataset original (para sacar los IDs)
        self.dataset_file = os.path.join(self.base_dir, "..", "..", "dataset", "dataset_elliot.tsv")
        # El súper archivo que contendrá todo
        self.output_file = os.path.join(self.base_dir, "factores_latentes.pkl")

    def extraer(self):
        print("\n=== SÚPER EXTRACTOR ELLIOT (MATRICES + DICCIONARIOS) ===")
        
        # ---------------------------------------------------------
        # FASE 1: EXTRAER DICCIONARIO DEL DATASET
        # ---------------------------------------------------------
        print("\n[Fase 1] Generando diccionarios de traducción desde el TSV...")
        if not os.path.exists(self.dataset_file):
            print(f"[ERROR] No se encuentra el dataset en: {self.dataset_file}")
            return
            
        user_to_idx = {}
        poi_to_idx = {}
        u_idx, i_idx = 0, 0
        
        with open(self.dataset_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 2: continue
                u, i = row[0], row[1]
                
                if u not in user_to_idx:
                    user_to_idx[u] = u_idx
                    u_idx += 1
                if i not in poi_to_idx:
                    poi_to_idx[i] = i_idx
                    i_idx += 1
                    
        print(f"   -> Encontrados {len(user_to_idx)} Usuarios y {len(poi_to_idx)} POIs reales.")

        # ---------------------------------------------------------
        # FASE 2: EXTRAER MATRICES NUMÉRICAS DE ELLIOT
        # ---------------------------------------------------------
        print("\n[Fase 2] Extrayendo matrices numéricas de Elliot...")
        search_pattern = os.path.join(self.weights_dir, "**", "best-weights*")
        archivos = [f for f in glob.glob(search_pattern, recursive=True) if not f.endswith('.index')]
        
        if not archivos:
            print("[ERROR] No se encontraron pesos.")
            return

        latest_file = max(archivos, key=os.path.getctime)
        print(f"   -> Archivo base: {os.path.basename(latest_file)}")

        matriz_usuarios = None
        matriz_pois = None

        try:
            with open(latest_file, 'rb') as f:
                datos = pickle.load(f)
                if isinstance(datos, dict):
                    for k, v in datos.items():
                        if isinstance(v, (list, np.ndarray)):
                            if 'user' in k.lower() or k == 'Gu': matriz_usuarios = v
                            elif 'item' in k.lower() or 'poi' in k.lower() or k == 'Gi': matriz_pois = v
                    if matriz_usuarios is None and matriz_pois is None and len(datos) == 2:
                        claves = list(datos.keys())
                        matriz_usuarios = datos[claves[0]]
                        matriz_pois = datos[claves[1]]
                elif isinstance(datos, (list, tuple)) and len(datos) >= 2:
                    matriz_usuarios = datos[0]
                    matriz_pois = datos[1]
        except Exception as e:
            print(f"[ERROR] Al leer el archivo de Elliot: {e}")
            return

        if matriz_usuarios is not None and matriz_pois is not None:
            print(f"   -> Matrices capturadas con éxito.")
            
            # ---------------------------------------------------------
            # FASE 3: EMPAQUETAR Y GUARDAR TODO JUNTO
            # ---------------------------------------------------------
            print("\n[Fase 3] Empaquetando 'El Cerebro' para tu algoritmo FPMC...")
            
            datos_a_guardar = {
                "usuarios_matriz": np.array(matriz_usuarios),
                "pois_matriz": np.array(matriz_pois),
                "user_to_idx": user_to_idx,          # Para pasar de 'U101' a fila 5
                "poi_to_idx": poi_to_idx,            # Para pasar de 'ChIJ...' a fila 12
                "idx_to_user": {v: k for k, v in user_to_idx.items()}, # Para recuperar el nombre real luego
                "idx_to_poi": {v: k for k, v in poi_to_idx.items()}    # Para recuperar el nombre del POI luego
            }

            with open(self.output_file, 'wb') as f:
                pickle.dump(datos_a_guardar, f)

            print(f"\n [ÉXITO TOTAL] ¡Matrices y Diccionarios unificados en un solo archivo!")
            print(f"   Ubicación: {self.output_file}")
            print("=========================================================")
        else:
            print("[ERROR] No se detectaron las 2 matrices.")

if __name__ == "__main__":
    extractor = ExtractorPesos()
    extractor.extraer()