#!/bin/bash

#SBATCH --job-name=grounding_index_to_neo4j
#SBATCH --output=/home/pwiesenbach/CardioGuidelinesGraph/slurm/grounding_index_to_neo4j.log
#SBATCH --partition=long
#SBATCH --mem=8G

set -euo pipefail

cd /home/pwiesenbach/CardioGuidelinesGraph

echo "==== GROUNDING INDEX TO NEO4J START ===="

INDEX_PATH_DEFAULT="/prj/doctoral_letters/guide/data/grounding_index.json"
RULES_PATH_DEFAULT="/prj/doctoral_letters/guide/data/extracted_rules.jsonl"

INDEX_PATH="${INDEX_PATH:-$INDEX_PATH_DEFAULT}"
RULES_PATH="${RULES_PATH:-$RULES_PATH_DEFAULT}"

if [[ ! -f "$INDEX_PATH" ]]; then
  echo "ERROR: grounding index not found at $INDEX_PATH"
  exit 1
fi

RULES_ARGS=""
if [[ -f "$RULES_PATH" ]]; then
  RULES_ARGS="--rules-path $RULES_PATH"
else
  echo "WARNING: rules file not found at $RULES_PATH (continuing without rule nodes)"
fi

poetry run python /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/neo4j_utils/grounding_index_to_neo4j.py \
  --index-path "$INDEX_PATH" \
  --allow-null-rule-ids \
  $RULES_ARGS

echo "==== GROUNDING INDEX TO NEO4J END ===="
