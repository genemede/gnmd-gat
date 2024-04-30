# going with module approach, see how it goes
# tempted to create dedicated config class
from pathlib import Path
import sys, os
from dotenv import dotenv_values
import json
from src.mtypes import *
from src.mdata import *
import datetime
import logging
log = logging.getLogger(__name__)

# Genemede config file and .env config are different things with different purposes:
# Genemede config stores user defined values
# .env stores installation specific things, mostly for development or deployment purposes

# uuid rfc
#https://www.rfc-editor.org/rfc/rfc4122.txt



envvalues = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}

GENEMEDE_ROOT_PATH = Path(Path().absolute())

this = sys.modules[__name__]
# user home, genemede home and config file locations are fixed
this.user_home_folder = Path.home()
this.genemede_home_folder = Path.joinpath(this.user_home_folder, 'genemede')
this.config_file = Path.joinpath(this.genemede_home_folder, 'config.json')
# further folder locations can be changed in config

# trying to use https://semver.org/
this.gnmdversion = {
    "major": 0,
    "minor": 1,
    "patch": 11
}

this.config = {
    "version": this.gnmdversion,
    "version_string": str(this.gnmdversion["major"]) + "." + str(this.gnmdversion["minor"]) + "." + str(this.gnmdversion["patch"]),
    "json_indent": 4,
    "user": {
        "name": "default user",
        "screen_name": "default",
        "email": "example@example.com"
    },
    "folders": {
        "user_data": Path.joinpath(this.genemede_home_folder, "data"),
        "user_media": Path.joinpath(this.genemede_home_folder, "media"),
        "user_scratch": Path.joinpath(this.genemede_home_folder, "scratch"),

        "system_mtypes": Path(Path().absolute(), "system/mtypes"),
        "user_mtypes": Path.joinpath(this.genemede_home_folder, "mtypes/user"),
        "imported_mtypes": Path.joinpath(this.genemede_home_folder, "mtypes/imported"),

        "global_sources": Path(Path().absolute(), "system/sources"),
        "logfiles": Path.joinpath(this.genemede_home_folder, "logs"),

        #not configurable, always under data
        "user_deleted_data": Path.joinpath(this.genemede_home_folder, "data/_deleted")
    }
}

# =====================================================================
class customEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)

        if isinstance(obj, datetime.datetime):
            return obj.isoformat("T", "seconds")
            #return obj.strftime("%Y-%m-%dT%H:%M:%SZ")

        #if isinstance(obj, datetime.date):
        #    return obj.strftime("%Y-%m-%d")
        return super().default(obj)

class GenemedeResponse:
    def __init__(self):
        self._errors = []

    def error(self, msg, context=None, value=None):
        obj = {
            "message": msg
        }
        if context: obj["context"] = context
        if value: obj["value"] = value
        self._errors.append(obj)

    def serialize(self, ind=None):
        obj = {}
        obj["errors"] = self._errors.copy()
        res = json.dumps(obj, indent=ind, ensure_ascii=False, cls=core.customEncoder)
        return res


def initialize():
    # prepares everything for runtime

    # make sure genemede home folder exists
    if not this.genemede_home_folder.is_dir():
        this.genemede_home_folder.mkdir(parents=False, exist_ok=False)

    this.mtypes = MetaTypesBroker()
    this.mtypes.loadFiles()
    this.data = DataBrokerClass()
    this.data.loadData()
    this.data.buildIndexes()

def envvar(k, dv = None):
    # also considers empty strings as None, to allow for .env to have the key= empty value
    if k in envvalues:
        v = envvalues[k]
        if isinstance(v, str) and v == "":
            v = dv
        return v
    else:
        return dv
# ----------------------------

def loadConfig():
    ok = False
    if Path(this.config_file).is_file():
        try:
            with open(this.config_file) as json_file:
                js = json.load(json_file)
                # single values
                for f in ["json_indent"]:
                    if f in js:
                        this.config[f] = js[f]

                # folder config
                if "folders" in js:
                    for f in ["user_data", "user_media", "user_scratch", "system_mtypes", "user_mtypes", "imported_mtypes", "logfiles"]:
                        if f in js["folders"]:
                            this.config["folders"][f] = Path(js["folders"][f])

                this.config["folders"]["user_deleted_data"] = Path.joinpath(this.config["folders"]["user_data"], '_deleted')

                # user config
                if "user" in js:
                    for f in ["name", "screen_name", "email"]:
                        if f in js["user"]:
                            this.config["user"][f] = Path(js["user"][f])
            ok = True
        except Exception as e:
            # something went wrong, will write full config at the end
            print("Error loading config")

    if not ok:
        # file doesnt exist, write with defaults
        writeConfig()

def cfg_json_serializer(obj):
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError

def serializeConfig():
    return json.dumps(this.config, indent=4, default=cfg_json_serializer)

def writeConfig():
    s = serializeConfig()
    with open(this.config_file, 'w') as f:
        f.write(s)

def safeDeleteFile(fnameorpath):
    # deletes files if path is under specific genemede folders, else fails
    pth = None
    if isinstance(fnameorpath, Path):
        pth = fnameorpath
        pass
    elif isinstance(fnameorpath, str):
        pth = Path(fnameorpath)

    if pth:
        if (
            this.config["folders"]["user_data"] in pth.parents
            or this.config["folders"]["user_media"] in pth.parents
            or this.config["folders"]["user_scratch"] in pth.parents
            or this.config["folders"]["user_deleted_data"] in pth.parents
            or this.config["folders"]["logfiles"] in pth.parents
        ):
            # can remove
            pth.unlink()
            return True

    return False

def prepareFolders():
    this.config["folders"]["user_data"].mkdir(parents=True, exist_ok=True)
    this.config["folders"]["user_media"].mkdir(parents=True, exist_ok=True)
    this.config["folders"]["user_scratch"].mkdir(parents=True, exist_ok=True)

    # system mtypes are special for now
    # this.config.folders.system_mtypes.mkdir(parents=False, exist_ok=True)
    this.config["folders"]["user_mtypes"].mkdir(parents=True, exist_ok=True)
    this.config["folders"]["imported_mtypes"].mkdir(parents=True, exist_ok=True)

    this.config["folders"]["logfiles"].mkdir(parents=True, exist_ok=True)

    this.config["folders"]["user_deleted_data"].mkdir(parents=True, exist_ok=True)
    return True

# =======================================
# make sure at least home folder exists
this.genemede_home_folder.mkdir(parents=True, exist_ok=True)

loadConfig()

# check folders, create them if they dont exist
prepareFolders()

l = core.envvar("LOG_LEVEL", logging.WARNING)
lfn = Path.joinpath(core.config["folders"]["logfiles"], "genemede.log")
logging.basicConfig(filename=lfn, encoding="utf-8", level=l, format="%(asctime)s [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

initialize()