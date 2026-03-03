import os
from neo4j import GraphDatabase

class Neo4jConnection:
    
    def __init__(self):
        # Configuración de la conexión a Neo4j
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7999")
        user= os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("[NEO4J CONNECTION] Conexión exitosa a la base de datos Neo4j")
        except Exception as e:
            print(f"[NEO4J CONNECTION]Error al conectar a la base de datos Neo4j: {e}")
            raise

    def __str__(self):
        if self.driver:
            estado = "Conectado" 
        else: 
            estado ="Desconectado"
        return f"Neo4jConnection {estado}" 

    def close(self):  
        self.driver.close()