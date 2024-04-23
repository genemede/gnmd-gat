# GENEMEDE GAT TOOL
Genemede API and Tools

This repository contains code to run the GENEMEDE GAT server that takes API requests.

## Installation
1. Download this repository via github `git clone https://github.com/genemede/gnmd-gat`
2. Setup a python virtual environment
```
cd gnmd-gat
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Usage
1. Create fake data by running `python fake.py`
2. Start the GAT server `python serve.py`
3. The tool should serve requests at `http://127.0.0.1:5342/v0/search?q=a&mtype=project` for example.
