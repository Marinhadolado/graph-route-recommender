import time
from persistencia.Neo4jConnection import Neo4jConnection
#MAIN
def main():
    print("=== INICIANDO SERVICIO BACKEND ===\n")
    
    # esperamos a Neo4j y conectamos el RouteGenerator.
    generador = None
    try:
        print("[Main] Conectando a Neo4j...")
        generador = Neo4jConnection()
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