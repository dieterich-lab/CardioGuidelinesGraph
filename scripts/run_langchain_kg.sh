#!/bin/bash

#SBATCH --job-name=langchain-kg
#SBATCH --output=../outputs/slurm/langchain-kg.txt
#SBATCH --partition=long
#SBATCH --mem=100G


python -u langchain_kg.py
