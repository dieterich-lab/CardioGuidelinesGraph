#!/bin/bash

#SBATCH --job-name=row10_struct_tests
#SBATCH --output=/home/pwiesenbach/CardioGuidelinesGraph/slurm/run_row10_structure_tests_%j.log
#SBATCH --partition=small
#SBATCH --mem=8G

set -euo pipefail

cd /home/pwiesenbach/CardioGuidelinesGraph

poetry run python -m unittest tests.test_row_10_structure_extraction
