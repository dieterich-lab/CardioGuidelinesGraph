import csv
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import and_, create_engine, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from cardio_graph.snomedct_utils.models import SnapDescription, SnapRelationship


class SnomedExplorer:
    """
    A class to explore the SNOMED CT database and extract concepts related to cardiovascular guidelines
    """

    def __init__(
        self,
        host: str = "10.250.135.23",
        port: str = "3306",
        user: str = "test_user",
        password: str = "medicaldatabase",
        database: str = "snomedct",
    ):
        """
        Initialize connection to the SNOMED CT database
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
        }
        self.engine = None
        self.Session = None
        self.session = None

    def connect(self) -> None:
        """Establish connection to the database using SQLAlchemy ORM"""
        try:
            user = self.connection_params["user"]
            password = self.connection_params["password"]
            host = self.connection_params["host"]
            port = self.connection_params["port"]
            database = self.connection_params["database"]
            url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(url)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Connected to {database} database on {host}")
        except SQLAlchemyError as err:
            print(f"Error connecting to database: {err}")
            raise

    def disconnect(self) -> None:
        """Dispose SQLAlchemy engine and close session"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
            print("Database connection closed")

    def explore_database_structure(self) -> Dict[str, List[str]]:
        """Get database structure - tables and their columns"""
        if not self.engine:
            self.connect()

        structure = {}
        db_name = self.connection_params["database"]
        with self.engine.connect() as conn:
            tables = conn.execute(text("SHOW TABLES")).fetchall()
            table_names = [row[0] for row in tables]
            for table in table_names:
                columns = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                col_names = [col[0] for col in columns]
                structure[table] = col_names
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
        Search for concepts related to cardiovascular domain using SnapDescription only.
        """
        if not self.session:
            self.connect()

        filters = or_(
            SnapDescription.term.ilike("%cardio%"),
            SnapDescription.term.ilike("%heart%"),
            SnapDescription.term.ilike("%vascular%"),
            SnapDescription.term.ilike("%coronary%"),
            SnapDescription.term.ilike("%atrial%"),
            SnapDescription.term.ilike("%ventricul%"),
            SnapDescription.term.ilike("%ischemi%"),
            SnapDescription.term.ilike("%ischaemi%"),
            SnapDescription.term.ilike("%hypertens%"),
        )
        results = self.session.query(SnapDescription).filter(filters).limit(limit).all()
        if results:
            print(
                f"Successfully found cardiovascular concepts in snap_description table"
            )
            return [r.__dict__ for r in results]
        return []

    def get_relationships(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific concept using snap_relationship table only.
        Returns list of dicts with keys: typeId, destinationId, sourceId, id, active
        """
        if not self.session:
            self.connect()

        results = (
            self.session.query(SnapRelationship)
            .filter(SnapRelationship.sourceId == concept_id)
            .limit(200)
            .all()
        )
        if results:
            return [r.__dict__ for r in results]
        return []

    def search_concepts_by_term(
        self, search_term: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search concepts by term using ORM models
        """
        if not self.session:
            self.connect()

        term_like = f"%{search_term}%"
        # Try snap_fsn
        results = (
            self.session.query(SnapDescription)
            .filter(SnapDescription.term.ilike(term_like))
            .limit(limit)
            .all()
        )
        if results:
            return [r.__dict__ for r in results]
        # Try snap_pref
        results = (
            self.session.query(SnapDescription)
            .filter(SnapDescription.term.ilike(term_like))
            .limit(limit)
            .all()
        )
        if results:
            return [r.__dict__ for r in results]
        # Try snap_description
        results = (
            self.session.query(SnapDescription)
            .filter(SnapDescription.term.ilike(term_like))
            .limit(limit)
            .all()
        )
        if results:
            return [r.__dict__ for r in results]
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
            with open(filepath, "w", newline="") as csvfile:
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
            with open(filepath, "w") as jsonfile:
                json.dump(data, jsonfile, indent=2)

            print(f"Data exported to {filepath}")
            return filepath
        except Exception as e:
            print(f"Error exporting data: {e}")
            return ""

    def explore_table(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Explore a specific table with sample data using ORM models
        """
        if not self.session:
            self.connect()

        # Map table name to model (only available models)
        model_map = {
            "snap_description": SnapDescription,
            "snap_relationship": SnapRelationship,
        }
        model = model_map.get(table_name)
        if not model:
            print(f"No ORM model defined for table {table_name}")
            return []
        results = self.session.query(model).limit(limit).all()
        return [r.__dict__ for r in results]

    def find_cardiovascular_guidelines_concepts(self) -> List[Dict[str, Any]]:
        """
        Find concepts specifically related to cardiovascular guidelines.

        This method searches for cardiovascular guideline concepts using both direct SQL queries
        and iterative term searches. It returns a comprehensive list of relevant concepts for
        building a cardiovascular ontology.
        """
        if not self.session:
            self.connect()

        # Direct ORM query for cardiovascular guideline concepts (SnapDescription only)
        filters = or_(
            and_(
                SnapDescription.term.ilike("%cardio%"),
                or_(
                    SnapDescription.term.ilike("%guideline%"),
                    SnapDescription.term.ilike("%recommendation%"),
                ),
            ),
            and_(
                SnapDescription.term.ilike("%heart%"),
                or_(
                    SnapDescription.term.ilike("%guideline%"),
                    SnapDescription.term.ilike("%recommendation%"),
                ),
            ),
            and_(
                SnapDescription.term.ilike("%vascular%"),
                or_(
                    SnapDescription.term.ilike("%guideline%"),
                    SnapDescription.term.ilike("%recommendation%"),
                ),
            ),
        )
        direct_results = (
            self.session.query(SnapDescription).filter(filters).limit(200).all()
        )
        if direct_results and len(direct_results) > 0:
            print(
                f"Found {len(direct_results)} cardiovascular guideline concepts with direct query"
            )
            return [r.__dict__ for r in direct_results]

        # Search terms approach
        query_terms = [
            "guideline",
            "recommendation",
            "protocol",
            "cardiac",
            "coronary",
            "heart",
            "vascular",
            "hypertension",
            "arrhythmia",
            "fibrillation",
            "angina",
            "infarction",
            "myocardial",
            "stroke",
            "thrombosis",
            "embolism",
        ]

        results = []
        for term in query_terms:
            try:
                print(f"Searching for term: {term}")
                concepts = self.search_concepts_by_term(term, 50)
                if concepts:
                    print(f"Found {len(concepts)} concepts matching '{term}'")
                    results.extend(concepts)
            except Exception as e:
                print(f"Error searching for term {term}: {e}")
                continue

        # No results fallback: return empty list (no SnapRelDefFSN available)
        if not results:
            return []

        # Remove duplicates based on id if it exists
        unique_results = []
        seen_ids = set()
        for item in results:
            id_field = None
            if "conceptId" in item:
                id_field = "conceptId"
            elif "id" in item:
                id_field = "id"
            if id_field:
                if item[id_field] not in seen_ids:
                    seen_ids.add(item[id_field])
                    unique_results.append(item)
            else:
                unique_results.append(item)
        return unique_results

    def execute_custom_query(
        self, query: str, params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query
        """
        if not self.engine:
            self.connect()

        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query), params).mappings().all()
                return [dict(row) for row in result]
            except SQLAlchemyError as err:
                print(f"Error executing query: {err}")
                return []

    def get_descriptions_for_concept(
        self, concept_id: str, lang: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all active descriptions (FSN, Synonyms, etc.) for a given concept ID.

        Args:
            concept_id: The SNOMED CT concept ID to look up.
            lang: The language code to search for (e.g., 'en', 'de').

        Returns:
            A list of dictionaries, where each dictionary represents a description.
        """
        if not self.session:
            self.connect()

        # The typeId for Fully Specified Name (FSN) and Synonym
        FSN_TYPE_ID = 900000000000003001
        SYNONYM_TYPE_ID = 900000000000013009

        try:
            results = (
                self.session.query(SnapDescription)
                .filter(
                    SnapDescription.conceptId == concept_id,
                    SnapDescription.active == 1,
                    # Optional: Add language filter if your DB has multiple languages
                    # SnapDescription.languageCode == lang
                )
                .all()
            )

            descriptions = []
            for r in results:
                desc_type = "Other"
                if r.typeId == FSN_TYPE_ID:
                    desc_type = "FSN"
                elif r.typeId == SYNONYM_TYPE_ID:
                    desc_type = "Synonym"

                # We don't know the preferred term just from this table,
                # but we can assume the non-FSN/non-Synonym is likely preferred.
                # A more robust way involves checking the language refset, but this is a good start.
                if desc_type == "Other":
                    desc_type = "PreferredTerm/Other"

                descriptions.append(
                    {"term": r.term, "type": desc_type, "typeId": r.typeId}
                )
            return descriptions
        except Exception as e:
            print(f"Error fetching descriptions for concept {concept_id}: {e}")
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

            if choice == "1":
                explorer.print_database_structure()

            elif choice == "2":
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

            elif choice == "3":
                limit = int(input("Enter limit (default 100): ") or 100)
                results = explorer.search_cardiovascular_concepts(limit)

                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))  # Show first 20 results
                    print(f"\nFound {len(results)} cardiovascular concepts")
                else:
                    print("No cardiovascular concepts found")

            elif choice == "4":
                term = input("Enter search term: ")
                limit = int(input("Enter limit (default 100): ") or 100)
                results = explorer.search_concepts_by_term(term, limit)

                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nFound {len(results)} concepts matching '{term}'")
                else:
                    print(f"No concepts found matching '{term}'")

            elif choice == "5":
                print("Searching for cardiovascular guideline concepts...")
                results = explorer.find_cardiovascular_guidelines_concepts()

                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(
                        f"\nFound {len(results)} concepts related to cardiovascular guidelines"
                    )
                else:
                    print("No cardiovascular guideline concepts found")

            elif choice == "6":
                concept_id = input("Enter concept ID: ")
                results = explorer.get_relationships(concept_id)

                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(
                        f"\nFound {len(results)} relationships for concept {concept_id}"
                    )
                else:
                    print(f"No relationships found for concept {concept_id}")

            elif choice == "7":
                query = input("Enter custom SQL query: ")
                results = explorer.execute_custom_query(query)

                if results:
                    df = pd.DataFrame(results)
                    print(df.head(20))
                    print(f"\nQuery returned {len(results)} results")
                else:
                    print("Query returned no results")

            elif choice == "8":
                # Need to have results from a previous operation
                if "results" not in locals() or not results:
                    print("No results to export. Run a search first.")
                    continue

                format_choice = input("Export format (1: CSV, 2: JSON): ")
                filename = input("Enter filename: ")

                if not filename:
                    filename = "snomed_export"

                if format_choice == "1":
                    if not filename.endswith(".csv"):
                        filename += ".csv"
                    explorer.export_to_csv(results, filename)
                else:
                    if not filename.endswith(".json"):
                        filename += ".json"
                    explorer.export_to_json(results, filename)

            elif choice == "0":
                break

            else:
                print("Invalid choice. Please try again.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        explorer.disconnect()


if __name__ == "__main__":
    main()
