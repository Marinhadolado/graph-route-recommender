import os
import sys
from elliot.run import run_experiment

class EntrenadorElliot:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "configuration.yml")

    def entrenar(self):
        if not os.path.exists(self.config_path):
            print(f"[ENTRENADOR ELLIOT] ERROR: No se encuentra el archivo YAML en {self.config_path}")
            sys.exit(1)

        print("[ENTRENADOR ELLIOT] Iniciando el framework Elliot...")
        print(f"[ENTRENADOR ELLIOT] Archivo de configuración: {self.config_path}")
        print("[ENTRENADOR ELLIOT] Se va a realizar la búsqueda de hiperparámetros...")
        
        try:
            run_experiment(self.config_path)
            
            print("[ENTRENADOR ELLIOT] Entrenamiento finalizado con éxito.")
            print("[ENTRENADOR ELLIOT] Revisa la carpeta 'results/' para ver los pesos guardados y las métricas.")
            
        except Exception as e:
            print(f"\n[ENTRENADOR ELLIOT] ERROR FATAL durante el entrenamiento: {e}")

if __name__ == "__main__":
    entrenador = EntrenadorElliot()
    entrenador.entrenar()