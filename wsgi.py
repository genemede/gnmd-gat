from src import routes
from flask import Flask
from dotenv import dotenv_values

envvalues = dotenv_values(".env")
fhost = envvalues["FLASK_RUN_HOST"] if "FLASK_RUN_HOST" in envvalues else "localhost"

#this default is different from serve.py because this is flask's default port, and serve.py defines our chosen port as 5342
fport = envvalues["FLASK_RUN_PORT"] if "FLASK_RUN_PORT" in envvalues else 5000
fdebug = (envvalues["FLASK_DEBUG"] == "1") if "FLASK_DEBUG" in envvalues else False
print("== SERVING FROM WSGI.PY ==")
print(f"{fhost}:{fport} debug:", "on" if fdebug else "off" )

app = Flask("genemede")
routes.create_routes(app);

