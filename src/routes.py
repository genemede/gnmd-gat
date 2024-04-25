from src import core
from pathlib import Path
from flask import Flask, jsonify, request, make_response
from flask.json.provider import JSONProvider
import json

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=core.customEncoder)

    def loads(self, s: str or bytes, **kwargs):
        return json.loads(s, **kwargs)

API_PREFIX = "/v0"

class _GnmdRoutes:
    def r1test(self):
        return "routetest1"

GnmdRoutes = _GnmdRoutes()

def create_routes(app):

    app.json = CustomJSONProvider(app)
    #app.config["RESTX_JSON"] = {'cls': customEncoder}

    print("- creating routes")

    @app.before_request
    def bef_req():
        # possible solution to allow write access to local ip only
        ip = request.environ.get('REMOTE_ADDR')
        print(ip)

    @app.after_request
    def after_request(response):
        # deal with cors (unfinished)
        if request.path.startswith(API_PREFIX):
            response.headers['Access-Control-Allow-Methods']='*'
            response.headers['Access-Control-Allow-Methods']='GET, POST, PUT, DELETE'
            response.headers['Access-Control-Allow-Origin']='*'
            response.headers['Access-Control-Allow-Headers']='Content-Type'
            response.headers['Access-Control-Max-Age']='300'
            response.headers['Vary']='Origin'
            response.headers.add('Content-Type', 'application/json')

        return response

    # prefer to avoid decorators
    app.add_url_rule(f'{API_PREFIX}/version', 'get_version', get_version)
    app.add_url_rule(f'{API_PREFIX}/config', 'get_config', get_config)
    app.add_url_rule(f'{API_PREFIX}/mtypes', 'get_mtypes', get_mtypes)
    app.add_url_rule(f'{API_PREFIX}/reload', 'get_reload_data', get_reload_data)
    app.add_url_rule(f'{API_PREFIX}/search', 'search', get_search)
    app.add_url_rule(f'{API_PREFIX}/stats', 'stats_get', stats_get,  methods=['GET'])

    app.add_url_rule(f'{API_PREFIX}/tstr1', 'tstr2', GnmdRoutes.r1test)

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/<path:filename>')
    def send_static(filename):
        return app.send_static_file(filename)

    # address the static built-in route if necessary

    # refactored: build CRUD routes for registered metatypes

    # http paths are ok with using dot (.) but we should discuss alternatives for nested mtypes
    # https://www.rfc-editor.org/rfc/rfc3986
    # ex.: GET /v0/data/project.cogitate

    # list resource
    app.add_url_rule(f'{API_PREFIX}/data/<mtype>', f'data_list', data_list,  methods=['GET'])

    # get resource (by guid)
    app.add_url_rule(f'{API_PREFIX}/guid/<guid>', 'data_get', data_get,  methods=['GET'])

    # update resource (by guid)
    app.add_url_rule(f'{API_PREFIX}/data/<guid>', f'data_put', data_put,  methods=['PUT'])

    # create resource
    app.add_url_rule(f'{API_PREFIX}/data', f'data_post', data_post,  methods=['POST'])

    # delete resource (by guid)
    app.add_url_rule(f'{API_PREFIX}/data/<guid>', f'data_delete', data_delete,  methods=['DELETE'])

    print("- routes created")

'''
all data in API Responses in element 'data'
'''

def get_version():
    return jsonify(core.gnmdversion)

def get_config():
    data = core.config #serializeConfig()
    return make_response({"data": data}, 200)

def get_mtypes():
    res = {"data": core.mtypes.getList()}
    return make_response(res, 200)

def get_reload_data():
    print("RELOADING")
    core.data.loadData()
    core.mtypes.loadFiles()
    return "Success", 200

def get_search():
    data = []
    # process args
    # only q so far
    q = request.args.get('q', default = None, type = str)
    mtype = request.args.get('mtype', default = None, type = str)
    data = core.data.search(q, mtype)

    return make_response({"data": data}, 200)

# only paths are considered right now; url args will be developed as needed
# routes asks data broker to execute specified operation and returns api responses

def data_list():
    # lists data of specified mtype
    pth = request.path.split("/")
    mtype = pth[3]
    lst = core.data.listResource(mtype)
    res = {"data": lst}
    return make_response(res, 200)

def data_get(guid):
    # gets specific resource by guid
    data = []
    obj = core.data.findByGuid(guid)
    return make_response({"data": obj.normalize()}, 200)

    #return "{\"data\": " + obj.serialize() + "}"
    #return {"result": obj.serialize() }

def data_put(guid):
    content_type = request.headers.get('Content-Type')
    print("PUT", content_type)
    if (content_type == 'application/json'):
        data = request.json
        res = core.data.putData(data)
        return data
    else:
        return 'Content-Type not supported!'

    # gets json payload from body
    payload = None
    res = None
    return {"result": f"PUT RESOURCE {mtype} : {guid}"}

def data_post():
    # gets json payload from body
    # post creates a new object
    # incoming guid is ignored
    # new object has new guid attributed
    content_type = request.headers.get('Content-Type')
    print("POSTED", content_type)
    if (content_type == 'application/json'):
        data = request.json
        res = core.data.postData(data)
        return data
    else:
        return 'Content-Type not supported!'

    payload = None
    res = None
    return {"result": f"POST RESOURCE {mtype}"}

def data_delete(guid):
    pth = request.path.split("/")
    mtype = pth[3]
    res = None
    return {"result": f"DELETE RESOURCE {mtype} : {guid}"}

def stats_get():
    res = core.data.getStats()
    return {"data": res}
