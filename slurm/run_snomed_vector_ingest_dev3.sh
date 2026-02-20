#!/bin/bash

#SBATCH --job-name=snomed_vec_ingest
#SBATCH --output=/home/pwiesenbach/CardioGuidelinesGraph/slurm/snomed_vector_ingest_dev3.log
#SBATCH --partition=small
#SBATCH --mem=24G

set -euo pipefail

cd /home/pwiesenbach/CardioGuidelinesGraph

export PYTHONPATH="$PWD/src"

SECRETS_ENV_DEFAULT="$HOME/.config/cardio_graph/secrets.env"
SECRETS_ENV_PATH="${CARDIO_GRAPH_SECRETS_ENV_PATH:-$SECRETS_ENV_DEFAULT}"
if [[ -f "$SECRETS_ENV_PATH" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS_ENV_PATH"
  set +a
fi

export CARDIO_GRAPH_GROUNDING_VECTOR_URI=${CARDIO_GRAPH_GROUNDING_VECTOR_URI:-bolt://neo4j-dev3.internal:7687}
export CARDIO_GRAPH_GROUNDING_VECTOR_USER=${CARDIO_GRAPH_GROUNDING_VECTOR_USER:-neo4j}
export CARDIO_GRAPH_GROUNDING_VECTOR_INDEX=${CARDIO_GRAPH_GROUNDING_VECTOR_INDEX:-snomed_term_embeddings_4096}
export CARDIO_GRAPH_GROUNDING_EMBEDDING_URL=${CARDIO_GRAPH_GROUNDING_EMBEDDING_URL:-http://10.250.135.153:11434}
export CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL=${CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL:-Qwen3embed}

if [[ -z "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD:-}" && -n "${CARDIO_GRAPH_GROUNDING_PASSWORD:-}" ]]; then
  export CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD="${CARDIO_GRAPH_GROUNDING_PASSWORD}"
fi

if [[ -z "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD:-}" && -n "${NEO4J_PASSWORD:-}" ]]; then
  export CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD="${NEO4J_PASSWORD}"
fi

if [[ -z "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD:-}" && -n "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD_FILE:-}" ]]; then
  if [[ -f "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD_FILE}" ]]; then
    export CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD="$(tr -d '\r\n' < "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD_FILE}")"
  fi
fi

if [[ -z "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD:-}" ]]; then
  echo "[snomed-vector-ingest] ERROR: Neo4j password is not set"
  echo "[snomed-vector-ingest] looked at:"
  echo "  - CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD"
  echo "  - CARDIO_GRAPH_GROUNDING_PASSWORD"
  echo "  - NEO4J_PASSWORD"
  echo "  - CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD_FILE"
  echo "  - optional secrets env: ${SECRETS_ENV_PATH}"
  exit 1
fi

echo "[snomed-vector-ingest] starting at $(date -Is)"
echo "[snomed-vector-ingest] neo4j_uri=${CARDIO_GRAPH_GROUNDING_VECTOR_URI}"
echo "[snomed-vector-ingest] vector_index=${CARDIO_GRAPH_GROUNDING_VECTOR_INDEX}"
echo "[snomed-vector-ingest] embedding_url=${CARDIO_GRAPH_GROUNDING_EMBEDDING_URL}"
echo "[snomed-vector-ingest] embedding_model=${CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL}"

poetry run python -m cardio_graph_core.neo4j.snomed_vector_ingest \
  --neo4j-uri "${CARDIO_GRAPH_GROUNDING_VECTOR_URI}" \
  --neo4j-user "${CARDIO_GRAPH_GROUNDING_VECTOR_USER}" \
  --neo4j-password "${CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD}" \
  --index-name "${CARDIO_GRAPH_GROUNDING_VECTOR_INDEX}" \
  --embedding-url "${CARDIO_GRAPH_GROUNDING_EMBEDDING_URL}" \
  --embedding-model "${CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL}" \
  --dimensions 4096 \
  --batch-size 24 \
  --fetch-size 2000 \
  --log-every 5000 \
  --no-wipe-db \
  --resume-only \
  --neo4j-max-attempts 8 \
  --neo4j-retry-backoff 2 \
  --drop-existing-vector-indexes

echo "[snomed-vector-ingest] finished at $(date -Is)"
