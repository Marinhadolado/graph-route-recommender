import time
from persistence.Neo4jConnection import Neo4jConnection

def main():
    print("=== STARTING BACKEND SERVICE ===\n")
    
    # esperamos a Neo4j y conectamos el RouteGenerator.
    generator = None
    try:
        print("[Main] Connecting to Neo4j...")
        generator = Neo4jConnection()
        print("[Main] Connection established.")
        
        while True:
            time.sleep(3600)

    except Exception as e:
        print(f"\n¡ERROR FATAL EN MAIN!: {e}")
    finally:
        if generator:
            generator.close()
            print("\n Al finalizar, cerrando conexión del generador de rutas...")

if __name__ == "__main__":
    main()