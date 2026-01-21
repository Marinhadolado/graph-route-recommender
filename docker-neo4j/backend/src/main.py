import time
from RouteGenerator import RouteGenerator
from Predictor import Predictor

#FUNCIONES AUXILIARES
def generate_csv_files(driver, predictor):
    """
    Busca todas las rutas en la BD y generamos los CSV de predictions
    """
    query_trails = """
    MATCH ()-[r:VISITED]->()
    WHERE r.trail_id IS NOT NULL AND r.user_id IS NOT NULL
    RETURN DISTINCT r.user_id as user_id, r.trail_id as trail_id
    """
    
    trails_to_process = []
    with driver.session() as session:

        results = session.run(query_trails)

        for record in results:

            trails_to_process.append({
                'user': record['user_id'],
                'trail': record['trail_id']
            })
    
    print(f"[Main] Se encontraron {len(trails_to_process)} rutas para procesar.")

    for i, item in enumerate(trails_to_process):

        if i % 10 == 0:
            print(f"  -> Procesando {i+1}/{len(trails_to_process)}...")
            
        predictor.process_trail(
            user_id=item['user'],
            trail_id=item['trail']
        )

#MAIN
def main():
    print("=== INICIANDO SERVICIO BACKEND ===\n")
    
    # esperamos a Neo4j y conectamos el RouteGenerator.
    generador = None
    try:
        print("[Main] Conectando a Neo4j...")
        generador = RouteGenerator()
        print("[Main] Conexión establecida.")
        
        # inicializamos componentes
        predictor = Predictor(generador.driver)
        
        # creamos los archivos para el predictor
        #print("\n[Main] Iniciando generación de archivos csv...")
        #generate_csv_files(generador.driver, predictor)
        #
        #print("\n[Main] Tarea completada con éxito.")
#
        ##para poder ejecutar pruebas manuales con docker exec
        #print("\n[Main] El servicio se mantendrá activo para pruebas (docker exec).")
        #print("[Main] Pulsa Ctrl+C para detenerlo.")
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