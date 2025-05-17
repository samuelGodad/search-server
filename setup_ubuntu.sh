#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install pytest==7.4.3
pip install pytest-cov==4.1.0
pip install matplotlib==3.8.2
pip install tabulate==0.9.0
pip install markdown==3.5.1

# Create test data directory
mkdir -p tests/data

# Make the script executable
chmod +x tests/test_performance.py 