from src import routes
from flask import Flask
from dotenv import dotenv_values

envvalues = dotenv_values(".env")
fhost = envvalues["FLASK_RUN_HOST"] if "FLASK_RUN_HOST" in envvalues else "localhost"
fport = envvalues["FLASK_RUN_PORT"] if "FLASK_RUN_PORT" in envvalues else 5342
fdebug = (envvalues["FLASK_DEBUG"] == "1") if "FLASK_DEBUG" in envvalues else False
print("\n== SERVING FROM SERVE.PY ==")
print(f"{fhost}:{fport} debug:", "on" if fdebug else "off" )

app = Flask("genemede")
routes.create_routes(app);

app.run(debug=fdebug, port=fport)
