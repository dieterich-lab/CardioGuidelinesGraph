#!/bin/bash

export PYTHONPATH=$PYTHONPATH:./src
export CUDA_LAUNCH_BLOCKING=1
export CUDA_VISIBLE_DEVICES=4

DEBUG=false
WAIT=false
PROG="neo4j_import.py"

POSITIONAL=()
while [ $# -gt 0 ]; do
	key="$1"

	case $key in
	-d | --DEBUG)
		DEBUG=true
		shift # past argument
		;;
	-w | --WAIT)
		WAIT=true
		shift # past argument
		;;
	*)                  # unknown option
		POSITIONAL+=("$1") # save it in an array for later
		shift              # past argument
		;;
	esac
done

set -- "${POSITIONAL[@]}" # restore positional parameters

PROG+=" $*"

if [ "$DEBUG" = true ]; then
	if [ "$WAIT" = true ]; then
		echo "Debugging $PROG (waiting...)"
		python -u -m debugpy --listen 0.0.0.0:5679 --wait-for-client $PROG
	else
		echo "Debugging $PROG"
		python -u -m debugpy --listen 0.0.0.0:5679 $PROG
	fi
else
	echo "Running $PROG"
	python -u $PROG
fi
