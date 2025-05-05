#!/bin/bash

# Add src to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run pytest with all arguments passed to this script
python3 -m pytest tests/ "$@" 