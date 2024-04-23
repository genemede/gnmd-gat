import os
from src import routes, mtypes
from flask import Flask, jsonify, request
from src.core import *

app = Flask("genemede")
routes.create_routes(app);
