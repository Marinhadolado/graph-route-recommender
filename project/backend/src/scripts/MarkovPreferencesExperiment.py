import json
import os
from services.Predictor import Predictor
import random

def experiment(user_id, city_name):
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
    
    predictor = Predictor(city_name)
    
    context = None
    steps = 1
    algorithm = "markov_preferences"

    print(f"=== STARTING EXPERIMENT BATTERY FOR {city_name} ===")

    for p_markov, p_nmf in pruebas:
        random.seed(42)

        m_int = int(p_markov * 100)
        n_int = int(p_nmf * 100)
        sufijo = f"{m_int}_{n_int}"
        
        print(f"\n[CONFIG] Testing balance: {m_int}% Markov / {n_int}% NMF")
        
        predictor.recommender.set_weights(p_markov, p_nmf)
        
        predictor.generate_predictions(
            user_id=user_id, 
            context=context, 
            steps=steps, 
            algorithm=algorithm, 
            suffix=sufijo
        )

    predictor.close()
    print("\n=== PROCESS FINISHED. Check the /predictions folder ===")

if __name__ == "__main__":
    USER_TEST = "155648" 
    CITY = "Tokyo"
    
    experiment(USER_TEST, CITY)