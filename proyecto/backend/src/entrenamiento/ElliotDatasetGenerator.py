import os
import csv
import sys

class GeneradorDatasetElliotCSV:
    #esta clase es necesaria ya que elliot necesita que los datos estén divididos en 3 columnas: user_id, item_id, rating. 
    # en nuestro caso el rating siempre será 1 porque solo tenemos interacciones positivas (visitas a POIs)
    def __init__(self, source_file_name="train.csv"):
        # localizamos las rutas donde esta el dataset con el limite de parametros de DatasetGenerator
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = os.path.join(self.base_dir, "..", "..", "dataset")
        
        # creamos el tsv en el mismo sitio
        self.input_file = os.path.join(self.dataset_dir, source_file_name)
        self.output_file = os.path.join(self.dataset_dir, "dataset_elliot.tsv")

    def generar(self):
        if not os.path.exists(self.input_file):
            print(f"[ELLIOT CSV] Error: No se encuentra el archivo {self.input_file}")
            return

        print(f"[ELLIOT CSV] Leyendo datos desde {self.input_file}...")
        
        interacciones_unicas = set()
        
        with open(self.input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extraemos solo lo que Elliot necesita
                user_id = row['user_id']
                poi_id = row['poi_id']
                interacciones_unicas.add((user_id, poi_id))

        print(f"[ELLIOT CSV] Se han encontrado {len(interacciones_unicas)} pares Usuario-POI únicos.")

        # Escribimos el TSV para Elliot
        with open(self.output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            for user_id, poi_id in interacciones_unicas:
                # user_id \t poi_id \t rating(1)
                writer.writerow([user_id, poi_id, 1])

        print(f"[ÉXITO] Archivo para Elliot generado en: {self.output_file}")

if __name__ == "__main__":
    archivo_origen = "dataset.csv"
    generador = GeneradorDatasetElliotCSV(source_file_name=archivo_origen)
    generador.generar()