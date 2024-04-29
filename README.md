# GENEMEDE GAT TOOL
Genemede API and Tools

This repository contains code to run the GENEMEDE GAT server that takes API requests.

## Installation
1. Download this repository via github `git clone https://github.com/genemede/gnmd-gat`
2. Setup a python virtual environment
```
cd gnmd-gat
python -m venv env
source env/bin/activate  |  env\Scripts\activate.bat `(if on windows)`
pip install -r requirements.txt
```

## Usage
1. Create a `.env` file on the project root or copy `.env.example` to `.env`
2. Set `ALLOW_NUKER=1` and `ALLOW_FAKER=1` on the `.env` file
3. Create fake data by running `python util.py faker`
4. Start the GAT server `python serve.py`
5. The tool should serve requests at `http://127.0.0.1:5342/v0/search?q=a&mtype=researcher` for example.

There are several utility scripts available on `util.py`, you can run `python util.py` without any arguments to see a list of utilities available.