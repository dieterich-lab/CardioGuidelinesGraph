import os
from pathlib import Path

from neo4j import GraphDatabase

DEFAULT_URI = "bolt://neo4j-dev4.internal:7687"
DEFAULT_USER = "neo4j"
DEFAULT_CYPHER_DIR = "/prj/doctoral_letters/guide/outputs2/cypher"
DEFAULT_SECRETS_ENV_PATH = Path.home() / ".config" / "cardio_graph" / "secrets.env"

# Backward-compatible module constants used by existing tests/tools.
URI = os.environ.get("CARDIO_GRAPH_NEO4J_URI", DEFAULT_URI)
AUTH = (
    os.environ.get("CARDIO_GRAPH_NEO4J_USER", DEFAULT_USER),
    os.environ.get("CARDIO_GRAPH_NEO4J_PASSWORD", ""),
)


def _load_env_file(env_path: Path) -> None:
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _neo4j_settings() -> tuple[str, tuple[str, str], str]:
    secrets_env = Path(
        os.environ.get("CARDIO_GRAPH_SECRETS_ENV_PATH", str(DEFAULT_SECRETS_ENV_PATH))
    )
    _load_env_file(secrets_env)

    uri = os.environ.get("CARDIO_GRAPH_NEO4J_URI", DEFAULT_URI)
    user = os.environ.get("CARDIO_GRAPH_NEO4J_USER", DEFAULT_USER)
    password = (
        os.environ.get("CARDIO_GRAPH_NEO4J_PASSWORD")
        or os.environ.get("NEO4J_PASSWORD")
        or os.environ.get("CARDIO_GRAPH_GROUNDING_PASSWORD")
    )
    cypher_dir = os.environ.get("CARDIO_GRAPH_CYPHER_DIR", DEFAULT_CYPHER_DIR)

    if not password:
        raise RuntimeError(
            "Missing Neo4j password. Set CARDIO_GRAPH_NEO4J_PASSWORD (preferred) "
            "or NEO4J_PASSWORD, optionally via "
            f"{secrets_env}."
        )

    return uri, (user, password), cypher_dir


def execute_cypher_file(session, filepath):
    """Execute all Cypher statements from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            cypher_statements = f.read()

        # Split the file content into individual statements
        filtered_lines = [
            line
            for line in cypher_statements.split("\n")
            if line.strip() and not line.strip().startswith("//")
        ]
        query = "\n".join(filtered_lines)
        session.run(query)

        print(f"Successfully executed all statements from {os.path.basename(filepath)}")

    except Exception as e:
        print(f"Error executing {filepath}: {str(e)}")


def main():
    try:
        uri, auth, cypher_dir = _neo4j_settings()

        with GraphDatabase.driver(uri, auth=auth) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")

            with driver.session() as session:
                # Process each Cypher file in the directory
                for filename in os.listdir(cypher_dir):
                    if filename.endswith("_cypher.txt"):
                        filepath = os.path.join(cypher_dir, filename)
                        print(f"\nProcessing file: {filename}")
                        execute_cypher_file(session, filepath)

    except Exception as e:
        print(f"Database connection error: {str(e)}")


if __name__ == "__main__":
    main()
