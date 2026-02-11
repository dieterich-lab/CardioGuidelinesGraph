#!/bin/bash

#SBATCH --job-name=row10_tests
#SBATCH --output=/home/pwiesenbach/CardioGuidelinesGraph/slurm/run_row10_tests.log
#SBATCH --partition=small
#SBATCH --mem=4G

set -euo pipefail

cd /home/pwiesenbach/CardioGuidelinesGraph

poetry run python -m unittest tests.test_row_10_structure_extraction
poetry run python -m unittest tests.test_row_10_structure_rules
poetry run python -m unittest tests.test_row_10_graph
