import json
import os
from servicios.Predictor import Predictor
import random

def ejecutar_experimentos_tfg(user_id, city_name):
    # Definimos las combinaciones de pesos (Markov, NMF)
    # 20_80 significa 20% importancia a la ruta y 80% a los gustos personales
    pruebas = [
        (0.0, 1.0),
        (0.2, 0.8),
        (0.3, 0.7),
        (0.4, 0.6),
        (0.5, 0.5),
        (0.6, 0.4),
        (0.7, 0.3),
        (0.8, 0.2),
        (1.0, 0.0)
    ]
    
    # Instanciamos el predictor una sola vez para ahorrar recursos
    predictor = Predictor(city_name)
    
    # Parámetros por defecto para tu evaluación
    context = None  # Cambiar por un dict si quieres probar con clima/hora
    steps = 1
    algorithm = "markov_preferences"

    print(f"=== INICIANDO BATERÍA DE EXPERIMENTOS PARA {city_name} ===")

    for p_markov, p_nmf in pruebas:
        # crear el sufijo identificador
        random.seed(42)

        m_int = int(p_markov * 100)
        n_int = int(p_nmf * 100)
        sufijo = f"{m_int}_{n_int}"
        
        print(f"\n[CONFIG] Probando balance: {m_int}% Markov / {n_int}% NMF")
        
        #inyectar los pesos en el RecommendationService
        predictor.recommender.set_weights(p_markov, p_nmf)
        
        #generar el archivo de predicciones
        predictor.generate_predictions(
            user_id=user_id, 
            context=context, 
            steps=steps, 
            algorithm=algorithm, 
            suffix=sufijo
        )

    predictor.cerrar_conexion()
    print("\n=== PROCESO FINALIZADO. Revisa la carpeta /predictions ===")

if __name__ == "__main__":
    USER_TEST = "155648" 
    CITY = "Tokyo"
    
    ejecutar_experimentos_tfg(USER_TEST, CITY)