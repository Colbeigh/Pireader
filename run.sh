#!/bin/bash
# run.sh - Run the e-reader

cd /home/colbeigh/ereader
export PYTHONPATH="/home/colbeigh/e-Paper/RaspberryPi_JetsonNano/python/lib:$PYTHONPATH"
python3 main.py 2>&1 | tee /home/colbeigh/ereader.log