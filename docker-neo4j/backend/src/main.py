import time
from RouteGenerator import RouteGenerator

#MAIN
def main():
    print("=== INICIANDO SERVICIO BACKEND ===\n")
    
    # esperamos a Neo4j y conectamos el RouteGenerator.
    generador = None
    try:
        print("[Main] Conectando a Neo4j...")
        generador = RouteGenerator()
        print("[Main] Conexión establecida.")
        
        while True:
            time.sleep(3600)

    except Exception as e:
        print(f"\n¡ERROR FATAL EN MAIN!: {e}")
    finally:
        if generador:
            generador.cerrar_conexion()
            print("\n Al finalizar, cerrando conexión del generador de rutas...")

if __name__ == "__main__":
    main()