#!/bin/bash

# SLURM Ollama Wrapper Script
# Usage: sbatch --export=GPU_TYPE=<type>,OLLAMA_PORT=<port> slurm_ollama_wrapper.sh <gpu_type> <port> "<python_command>"
# The python_command should be the full command to run, e.g., "poetry run python /path/to/script.py --args"

# Arguments from command line (passed via sbatch)
GPU_TYPE="$1"
OLLAMA_PORT="$2"
PYTHON_COMMAND="$3"

# Map GPU type to node
case $GPU_TYPE in
    ampere)
        NODE="g4"
        ;;
    hopper)
        NODE="g5"
        ;;
    turing)
        NODE="g2"  # Default to g2 for turing
        ;;
    pascal)
        NODE="g1"
        ;;
    *)
        echo "Unknown GPU_TYPE: $GPU_TYPE"
        exit 1
        ;;
esac

# SLURM directives
#SBATCH --gres=gpu:${GPU_TYPE}:1
#SBATCH --partition=gpu
#SBATCH --mem=16G

# Get the actual node name
ACTUAL_NODE=$(hostname)
echo "Actual node: $ACTUAL_NODE"
echo "Available IPs on this node:"
ip addr show | grep inet | awk '{print $2}' | cut -d'/' -f1
echo "Hostname IPs: $(hostname -I)"

# Get IP for the node
case $ACTUAL_NODE in
    gpu-g2-1)
        OLLAMA_IP="10.250.135.143"
        ;;
    gpu-g3-1)
        OLLAMA_IP="10.250.135.150"
        ;;
    gpu-g4-1)
        OLLAMA_IP="10.250.135.153"
        ;;
    gpu-g5-1)
        OLLAMA_IP="10.250.135.156"
        ;;
    slurm-c-mk1-1c)
        OLLAMA_IP="10.250.135.129"  # Guessed, adjust if needed
        ;;
    slurm-c-mk2-1a)
        OLLAMA_IP="10.250.135.128"
        ;;
    slurm-c-mk2-2d)
        OLLAMA_IP="10.250.135.115"
        ;;
    *)
        echo "Unknown ACTUAL_NODE: $ACTUAL_NODE"
        echo "Please add the IP mapping for this node."
        exit 1
        ;;
esac

echo "Using GPU_TYPE=$GPU_TYPE, NODE=$NODE, ACTUAL_NODE=$ACTUAL_NODE, OLLAMA_IP=$OLLAMA_IP, OLLAMA_PORT=$OLLAMA_PORT"
echo "Available IPs on this node:"
ip addr show | grep inet | awk '{print $2}' | cut -d'/' -f1
echo "Hostname: $(hostname)"
echo "Hostname IPs: $(hostname -I)"
echo "Python command: $PYTHON_COMMAND"

# Function to start Ollama server
start_ollama() {
    echo "Starting Ollama server on $NODE ($OLLAMA_IP:$OLLAMA_PORT)..."
    OLLAMA_ORIGINS=* OLLAMA_KEEP_ALIVE=240h OLLAMA_CONTEXT_LENGTH=128000 OLLAMA_TMPDIR=/beegfs/scratch/pwiesenbach TMPDIR=/beegfs/scratch/pwiesenbach OLLAMA_HOST=$OLLAMA_IP:$OLLAMA_PORT OLLAMA_TIMEOUT=30 OLLAMA_DEBUG=1 ollama serve &
    OLLAMA_PID=$!
    echo "Ollama started with PID: $OLLAMA_PID"
    # Wait a bit for Ollama to start
    sleep 10
}

# Function to stop Ollama server
stop_ollama() {
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "Stopping Ollama server (PID: $OLLAMA_PID)..."
        kill $OLLAMA_PID
        wait $OLLAMA_PID 2>/dev/null
        echo "Ollama stopped."
    fi
}

# Trap to ensure Ollama is stopped on exit
trap stop_ollama EXIT

# Start Ollama
start_ollama

# Pull the required model (assuming qwen3:latest for now, can be parameterized later)
echo "Pulling model qwen3:latest..."
ollama pull qwen3:latest

# Check if Ollama is listening on the port
if ! ss -tln | grep -q ":$OLLAMA_PORT "; then
    echo "Error: Ollama failed to start on port $OLLAMA_PORT"
    exit 1
fi

# Run the provided Python command with added --node and --ollama-port
eval "$PYTHON_COMMAND --node $NODE --ollama-port $OLLAMA_PORT"

# Ollama will be stopped automatically via trap