from src import core
import copy
import time
from pathlib import Path
from flask import Flask, jsonify, request, make_response, send_file
from flask.json.provider import JSONProvider
import json
import urllib.request
from dotenv import dotenv_values

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=core.customEncoder)

    def loads(self, s: str or bytes, **kwargs):
        return json.loads(s, **kwargs)

API_PREFIX = "/v0"

def create_app():
    return Flask("genemede") #static_url_path='', static_folder='static')

def create_routes(app):

    envvalues = dotenv_values(".env")

    app.json = CustomJSONProvider(app)
    app.json.sort_keys = False
    app.config['JSON_SORT_KEYS'] = False

    #app.config["RESTX_JSON"] = {'cls': customEncoder}
    print("Genemede GAT " + "v\033[93m" + core.version_string + "\033[0m")

    guiver = None
    try:
        with urllib.request.urlopen('https://genemede.github.io/gnmd-gui/version') as fl:
            tmp = fl.read().decode('utf-8')
            guiver = " (v\033[93m" + tmp + "\033[0m)"

    except Exception as e:
        s = str(e)
        print("\033[33mError retrieving GUI version: " + s + "\033[0m")
        guiver = " (v\033[93m0.1.23\033[0m)"

    msg = "Development GUI available at " + "\033[96m" + "\033[4m" + "https://genemede.github.io/gnmd-gui" + "\033[0m"
    if guiver:
        msg = msg + guiver
    print(msg)



    @app.before_request
    def bef_req():
        # possible solution to allow write access to local ip only
        ip = request.environ.get('REMOTE_ADDR')
        #print(ip)

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
    app.add_url_rule(f'{API_PREFIX}/sources', 'get_sources', get_sources)
    app.add_url_rule(f'{API_PREFIX}/sources/<src>', 'get_source_item', get_source_item)
    app.add_url_rule(f'{API_PREFIX}/reload', 'get_reload_data', get_reload_data)
    app.add_url_rule(f'{API_PREFIX}/export', 'get_export', get_export)
    app.add_url_rule(f'{API_PREFIX}/search', 'search', get_search)
    app.add_url_rule(f'{API_PREFIX}/stats', 'get_stats', get_stats,  methods=['GET'])




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

    print("Ready.")

'''
all data in API Responses in element 'data'
'''

def get_version():
    return jsonify(core.gnmdversion)

def get_config():
    if core.envvar("RELOAD_ON_GET_CONFIG") == "1":
        print("= RELOADING =")
        core.loadConfig()
        core.data.loadData()
        core.mtypes.loadFiles()

    data = copy.deepcopy(core.config)
    # special dev info value, only present if defined in .env
    if core.envvar("GUI_DEV_INFO") == "1":
        data["dev_info"] = True
    else:
        data.pop("dev_info", None)

    data["version"] = core.gnmdversion
    data["version_string"] = core.version_string

    # add feedback form to config to display in gui
    # simple obfuscation just to thwart url scraping a bit
    ffurl = "https:**docs.google.com*forms*d*e*"
    ffurl = ffurl + "1FAIpQLSfcMm_OzRvExRklsAAwtK8ZYl7V0SfotlKADcUWsDFnPgEeCw*viewform"
    data["feedback_form"] = ffurl.replace('*', '/')

    return make_response({"data": data}, 200)

def get_mtypes():
    res = {"data": core.mtypes.getList()}
    return make_response(res, 200)

def get_sources():
    res = {"data": core.mtypes.listSources()}
    return make_response(res, 200)

def get_source_item(src):
    # special case for sources via API
    # can retrieve mtype data as a source
    # this will be improved but it solves several gui issues atm

    #print("GET SOURCE ITEM", src)
    p = src.find(":")
    if (p>0):
        args = src.split(':')
        if len(args) == 2:
            mt = core.mtypes.getMType(args[1])
            if mt:
                lst = core.data.listResource(args[1])
                tmp = {
                    "name": mt.name,
                    "description": mt.description,
                    "codes": []
                }
                for obj in lst:
                    tmp["codes"].append({
                        "code": obj["guid"],
                        "value": obj["label"]
                    })
                res = {"data": tmp}
                return make_response(res, 200)

        # if anything fails
        return make_response(400)
    # normal sources
    res = {"data": core.mtypes.getSource(src, api = True)}
    return make_response(res, 200)

def get_reload_data():
    print("RELOADING")
    core.data.loadData()
    core.mtypes.loadFiles()
    return "Success", 200

def get_export():
    path = core.data.exportDataToFile()
    #path = "C:/Users/jorge/genemede/scratch/dbg_all_data.json"
    return send_file(path, as_attachment=True)

    # exports all data to a downloadable json file
    ## dbg_all_data.json
    return make_response(data, 200)

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

def data_list(mtype):
    # lists data of specified mtype
    lst = core.data.listResource(mtype)
    res = {"data": lst}
    return make_response(res, 200)

def data_get(guid):
    # gets specific resource by guid
    data = []
    obj = core.data.findByGuid(guid)
    return make_response({"data": obj.normalize()}, 200)

def data_put(guid):
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.json
        res = core.data.putData(data)
        if res != None:
            return make_response({"data": res}, 200)
        else:
            return make_response(400)

    else:
        return make_response({"message": "Content-Type not supported!"}, 400)

    return make_response(400)

def data_post():
    # gets json payload from body
    # post creates a new object
    # incoming guid is ignored
    # new object has new guid attributed
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        data = request.json
        res = core.data.postData(data)
        if res != None:
            return make_response({"data": res}, 200)
        else:
            return make_response(400)
    else:
        return make_response({"message": "Content-Type not supported!"}, 400)

    return make_response(400)

def data_delete(guid):
    pth = request.path.split("/")
    mtype = pth[3]
    res = None
    return {"result": f"DELETE RESOURCE {mtype} : {guid}"}

def get_stats():
    res = core.data.getStats()
    return {"data": res}
