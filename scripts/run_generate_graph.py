#!/bin/bash

#SBATCH --job-name=generate_graph
#SBATCH --output=../outputs/slurm/langchain-kg.txt
#SBATCH --partition=long
#SBATCH --mem=100G


python -u generate_graph.py
