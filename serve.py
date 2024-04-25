from src import routes
from flask import Flask
print("== SERVING FROM SERVE.PY ==")

app = Flask("genemede") #static_url_path='', static_folder='static')

app.json.sort_keys = False
app.config['JSON_SORT_KEYS'] = False

routes.create_routes(app);
app.run(debug=True, port=5342)
