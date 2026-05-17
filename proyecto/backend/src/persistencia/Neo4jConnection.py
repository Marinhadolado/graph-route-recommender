import os
from neo4j import GraphDatabase

class Neo4jConnection:
    """Manages the connection with the Neo4j database."""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7999")
        user= os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("[Neo4jConnection] Successfully connected to the Neo4j database.")
        except Exception as e:
            print(f"[Neo4jConnection] Error connecting to Neo4j: {e}")
            raise

    def run_read(self, query, parameters):
        """Executes a read-only query and transforms records into a list of dictionaries."""        
        with self.driver.session() as session:

            result = session.run(query, parameters)
            data =[]

            for record in result:
                data.append(record.data())

            return data
        
    def __str__(self):
        if self.driver:
            estado = "Connected" 
        else: 
            estado ="Disconnected"
        return f"Neo4jConnection {estado}" 

    def close(self):
        """ Closes the connection to the database.""" 
        if self.driver:
            self.driver.close()