import os
from src import gdev, routes, mtypes
from flask import Flask, jsonify, request
from src.core import *

def create_app(test_config=None):
    # create and configure the app
    app = Flask("genemede", instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    app.json.sort_keys = False
    app.config['JSON_SORT_KEYS'] = False

    # check if local config exists
    # prompts to create
    # needs data folder - defaults to user folder/genemede


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # routing
    #@app.route('/version')
    #def getversion():
    #    return jsonify(gnmdversion);
    # avoiding decorators

    routes.create_routes(app);

    return app