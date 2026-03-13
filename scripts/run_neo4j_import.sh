#!/bin/bash

#SBATCH --job-name=neo4j_import
#SBATCH --output=../outputs/slurm/neo4j_import.txt
#SBATCH --partition=long
#SBATCH --mem=200G


python -u neo4j_import.py
