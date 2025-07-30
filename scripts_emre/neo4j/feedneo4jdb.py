from neo4j import GraphDatabase
import os

# Database configuration
URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
CYPHER_DIR = "/prj/doctoral_letters/guide/outputs2/cypher"

def execute_cypher_file(session, filepath):
    """Execute all Cypher statements from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cypher_statements = f.read()
            
        # Split the file content into individual statements
        filtered_lines = [line for line in cypher_statements.split('\n') 
                  if line.strip() and not line.strip().startswith('//')]
        query = '\n'.join(filtered_lines)
        session.run(query)
                
        print(f"Successfully executed all statements from {os.path.basename(filepath)}")
        
    except Exception as e:
        print(f"Error executing {filepath}: {str(e)}")

def main():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            
            with driver.session() as session:
                # Process each Cypher file in the directory
                for filename in os.listdir(CYPHER_DIR):
                    if filename.endswith('_cypher.txt'):
                        filepath = os.path.join(CYPHER_DIR, filename)
                        print(f"\nProcessing file: {filename}")
                        execute_cypher_file(session, filepath)
                        
    except Exception as e:
        print(f"Database connection error: {str(e)}")

if __name__ == "__main__":
    main()

