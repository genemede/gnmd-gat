import os
from src import routes, mtypes
from flask import Flask, jsonify, request
from src.core import *

print("== SERVING FROM WSGI.PY ==")

app = Flask("genemede")
routes.create_routes(app);
