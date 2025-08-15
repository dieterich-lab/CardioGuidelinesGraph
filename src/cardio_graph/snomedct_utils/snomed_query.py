import mysql.connector
import csv
import json
import os
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import re

class SnomedExplorer:
    """
    A class to explore the SNOMED CT database and extract concepts related to cardiovascular guidelines
    """
    
    def __init__(self, host: str = "10.250.135.23", port: str = "3306", 
                 user: str = "test_user", password: str = "medicaldatabase", 
                 database: str = "snomedct"):
        """
        Initialize connection to the SNOMED CT database
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }
        self.conn = None
        self.cursor = None
        
    def connect(self) -> None:
        """Establish connection to the database"""
        try:
            self.conn = mysql.connector.connect(**self.connection_params)
            self.cursor = self.conn.cursor(dictionary=True)
            print(f"Connected to {self.connection_params['database']} database on {self.connection_params['host']}")
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}")
            raise
            
    def disconnect(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")
            
    def explore_database_structure(self) -> Dict[str, List[str]]:
        """Get database structure - tables and their columns"""
        if not self.conn or not self.cursor:
            self.connect()
            
        # Get tables
        self.cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_' + self.connection_params['database']] for table in self.cursor.fetchall()]
        
        structure = {}
        
        # Get columns for each table
        for table in tables:
            self.cursor.execute(f"DESCRIBE {table}")
            columns = [col['Field'] for col in self.cursor.fetchall()]
            structure[table] = columns
            
        return structure
    
    def print_database_structure(self) -> None:
        """Print database structure in a readable format"""
        structure = self.explore_database_structure()
        
        print("=== SNOMED CT DATABASE STRUCTURE ===")
        for table, columns in structure.items():
            print(f"\n📋 TABLE: {table}")
            print("  Columns:")
            for col in columns:
                print(f"    - {col}")
                
    def search_cardiovascular_concepts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for concepts related to cardiovascular domain
        
        This is just an example - you may need to adjust the query based on the actual database schema
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        # This query assumes a certain structure - adjust according to your actual SNOMED CT database
        query = """
        SELECT c.id, c.term, c.conceptId, c.active
        FROM concept c
        JOIN description d ON c.conceptId = d.conceptId
        WHERE 
            d.term LIKE '%cardio%' OR 
            d.term LIKE '%heart%' OR 
            d.term LIKE '%vascular%' OR 
            d.term LIKE '%coronary%' OR
            d.term LIKE '%atrial%' OR
            d.term LIKE '%ventricul%' OR
            d.term LIKE '%ischemi%' OR
            d.term LIKE '%ischaemi%' OR
            d.term LIKE '%hypertens%'
        GROUP BY c.conceptId
        LIMIT %s
        """
        
        try:
            self.cursor.execute(query, (limit,))
            results = self.cursor.fetchall()
            return results
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
            # Try alternative query approach if the first one fails
            try:
                # Simplified query for different database structure
                alt_query = """
                SELECT * 
                FROM concept 
                WHERE term LIKE '%cardio%' OR term LIKE '%heart%'
                LIMIT %s
                """
                self.cursor.execute(alt_query, (limit,))
                return self.cursor.fetchall()
            except:
                print("Both query approaches failed. Please check the database structure.")
                return []
    
    def get_relationships(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific concept
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        try:
            # Attempt to find IS-A relationships (this query assumes a relationship table exists)
            query = """
            SELECT * 
            FROM relationship 
            WHERE sourceId = %s OR destinationId = %s
            """
            self.cursor.execute(query, (concept_id, concept_id))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error finding relationships: {err}")
            print("Trying alternative approach...")
            
            # Try alternative table that might contain relationships
            try:
                alt_query = """
                SELECT * 
                FROM stated_relationship 
                WHERE sourceId = %s OR destinationId = %s
                """
                self.cursor.execute(alt_query, (concept_id, concept_id))
                return self.cursor.fetchall()
            except:
                return []
    
    def search_concepts_by_term(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search concepts by term
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        try:
            query = """
            SELECT * 
            FROM concept 
            WHERE term LIKE %s
            LIMIT %s
            """
            self.cursor.execute(query, (f"%{search_term}%", limit))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error searching concepts: {err}")
            
            # Try alternative approach using description table
            try:
                alt_query = """
                SELECT c.* 
                FROM concept c
                JOIN description d ON c.conceptId = d.conceptId
                WHERE d.term LIKE %s
                GROUP BY c.conceptId
                LIMIT %s
                """
                self.cursor.execute(alt_query, (f"%{search_term}%", limit))
                return self.cursor.fetchall()
            except:
                return []
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Export data to CSV file
        """
        if not data:
            print("No data to export")
            return ""
            
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            print(f"Data exported to {filepath}")
            return filepath
        except Exception as e:
            print(f"Error exporting data: {e}")
            return ""
    
    def export_to_json(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Export data to JSON file
        """
        if not data:
            print("No data to export")
            return ""
            
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w') as jsonfile:
                json.dump(data, jsonfile, indent=2)
            
            print(f"Data exported to {filepath}")
            return filepath
        except Exception as e:
            print(f"Error exporting data: {e}")
            return ""
    
    def explore_table(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Explore a specific table with sample data
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        try:
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error exploring table {table_name}: {err}")
            return []
            
    def find_cardiovascular_guidelines_concepts(self) -> List[Dict[str, Any]]:
        """
        Find concepts specifically related to cardiovascular guidelines
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        # Search for guideline-related concepts in cardiovascular domain
        query_terms = [
            '%guideline%', '%recommendation%', '%protocol%',
            '%cardiac%', '%coronary%', '%heart%', '%vascular%',
            '%hypertension%', '%arrhythmia%', '%fibrillation%',
            '%angina%', '%infarction%', '%myocardial%',
            '%stroke%', '%thrombosis%', '%embolism%'
        ]
        
        results = []
        for term in query_terms:
            try:
                concepts = self.search_concepts_by_term(term, 20)
                results.extend(concepts)
            except:
                continue
                
        # Remove duplicates based on conceptId if it exists
        unique_results = []
        seen_ids = set()
        
        for item in results:
            if 'conceptId' in item:
                if item['conceptId'] not in seen_ids:
                    seen_ids.add(item['conceptId'])
                    unique_results.append(item)
            else:
                unique_results.append(item)  # Keep items without conceptId
                
        return unique_results
        
    def execute_custom_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query
        """
        if not self.conn or not self.cursor:
            self.connect()
            
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
            return []


def main():
    """Main function to demonstrate the SNOMED CT explorer"""
    explorer = SnomedExplorer()
    
    try:
        # Connect to database
        explorer.connect()
        
        # Print menu for interactive exploration
        while True:
            print("\n==== SNOMED CT Explorer for Cardiovascular Guidelines ====")
            print("1. Explore database structure")
            print("2. Show sample data from a specific table")
            print("3. Search cardiovascular concepts")
            print("4. Search concepts by term")
            print("5. Find concepts related to cardiovascular guidelines")
            print("6. Get relationships for a concept")
            print("7. Execute custom query")
            print("8. Export results to CSV/JSON")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-8): ")
            
            if choice == '1':
                explorer.print_database_structure()
                
            elif choice == '2':
                table_name = input("Enter table name: ")
                limit = int(input("Enter limit (default 10): ") or 10)
                results = explorer.explore_table(table_name, limit)
                
                if results:
                    # Convert to DataFrame for better display
                    df = pd.DataFrame(results)
                    print(df.head(limit))
                    print(f"\nShowing {len(results)} results")
                else:
                    print("No results found or table doesn't exist")
                    
            elif choice == '3':
                limit = int(input("Enter limit (default 100): ") or 100)
                results = explorer.search_cardiovascular_concepts(limit)
                
                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))  # Show first 20 results
                    print(f"\nFound {len(results)} cardiovascular concepts")
                else:
                    print("No cardiovascular concepts found")
                    
            elif choice == '4':
                term = input("Enter search term: ")
                limit = int(input("Enter limit (default 100): ") or 100)
                results = explorer.search_concepts_by_term(term, limit)
                
                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nFound {len(results)} concepts matching '{term}'")
                else:
                    print(f"No concepts found matching '{term}'")
                    
            elif choice == '5':
                print("Searching for cardiovascular guideline concepts...")
                results = explorer.find_cardiovascular_guidelines_concepts()
                
                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nFound {len(results)} concepts related to cardiovascular guidelines")
                else:
                    print("No cardiovascular guideline concepts found")
                    
            elif choice == '6':
                concept_id = input("Enter concept ID: ")
                results = explorer.get_relationships(concept_id)
                
                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nFound {len(results)} relationships for concept {concept_id}")
                else:
                    print(f"No relationships found for concept {concept_id}")
                    
            elif choice == '7':
                query = input("Enter custom SQL query: ")
                results = explorer.execute_custom_query(query)
                
                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nQuery returned {len(results)} results")
                else:
                    print("Query returned no results")
                    
            elif choice == '8':
                # Need to have results from a previous operation
                if 'results' not in locals() or not results:
                    print("No results to export. Run a search first.")
                    continue
                    
                format_choice = input("Export format (1: CSV, 2: JSON): ")
                filename = input("Enter filename: ")
                
                if not filename:
                    filename = "snomed_export"
                    
                if format_choice == '1':
                    if not filename.endswith('.csv'):
                        filename += '.csv'
                    explorer.export_to_csv(results, filename)
                else:
                    if not filename.endswith('.json'):
                        filename += '.json'
                    explorer.export_to_json(results, filename)
                    
            elif choice == '0':
                break
                
            else:
                print("Invalid choice. Please try again.")
                
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        explorer.disconnect()


if __name__ == "__main__":
    main()
