#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run streamlit with PM2
streamlit run generate_yaml_ui.py --server.address 0.0.0.0