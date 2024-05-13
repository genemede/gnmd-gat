# MetaTypesBroker - can be changed into just module functions...
from src import core
from typing import Any, Optional, NewType
from pathlib import Path
import random
import json
from json import JSONEncoder
import copy

MetaTypeType = NewType("MetaType", object)

class MetaType:
    def __init__(self, pth: Path, ns = ""):
        self.path = pth
        self.mtype = pth.stem
        self.folder = pth.parents[0]
        self.name = ""
        self.description = ""
        self.namespace = ""
        self.fa_icon = "far fa-file-alt"
        self.properties =  {}
        self.modules = {}
        self.sources = {}

        # temp set for duplication prevention - is converted into sorted list on data.names after loading
        self._defaults = []
        self._names = set()
        self._linkFields = set()
        self.loadFile()

    def loadFile(self):
        # loads current file
        def getval(dc, k, dflt = None):
            if k in dc:
                return dc[k]
            else:
                return dflt

        with open(self.path) as json_file:
            self.loaded_data = json.load(json_file)
            self.validateData()

        self.name = self.loaded_data["name"]
        self.description = self.loaded_data["description"]
        self.fa_icon = getval(self.loaded_data, "fa_icon", "far fa-file-alt")

        self.procFields(self.properties, self.loaded_data["properties"])
        self.procSources()

        # load modules
        p = Path.joinpath(self.folder, "modules")
        if p.is_dir():
            for f in p.iterdir():
                if f.is_file():
                    if not f.stem.startswith("_") and f.suffix == ".json":
                        self.loadModule(f)

        #print("link fields", self.mtype, self._linkFields)

    def loadModule(self, fl):
        with open(fl) as json_file:
            data = json.load(json_file)
            if "properties" in data:
                # only loads module if it has a properties key
                mod = {
                    "name": data["name"] if "name" in data else fl.stem,
                    "description": data["description"] if "description" in data else fl.stem,
                    "datatype": "module",
                    "properties": {}
                }
                self.modules[fl.stem] = mod
                self.procFields(self.modules[fl.stem]["properties"], data["properties"])

    def procFields(self, fldroot, fldlist, included = None):
        # iterates dict with list of fields
        # still processes field by field for validation and ensuring default values
        # keeps fields directly on data structure instead of dedicated object tree
        for n, v in fldlist.items():
            self.procField(fldroot, n, v)

    def procField(self, fldroot, fldname, fldvalue):
        # processes a field declaration

        def intProcKey(key, defval):
            # adds keys or default value, for important fields
            nonlocal fldname, fldvalue
            if key in fldvalue:
                fldroot[fldname][key] = fldvalue[key]
            else:
                fldroot[fldname][key] = defval
                self._defaults.append(fldname + "." + key)

        def intCheckDupe(n):
            if fldname in self._names:
                print("duplicate name", fldname)
                return False
                #exit()
            return True

        # sanity: convert to lower case before anything else
        fldname = fldname.lower()

        # normal field declaration
        if intCheckDupe(fldname):
            fldroot[fldname] = {}
            self._names.add(fldname)
            deftext = fldname.replace("_", " ").capitalize()
            intProcKey("description", deftext)
            intProcKey("datatype", "text")
            intProcKey("label", deftext)
            intProcKey("help", deftext)

            # proc sources
            # possible values:
            # text string, refers to a registered source
            # list (of strings) are inplace declaration sources for the field
            # dict would be a full fledged inplace sources declaration (wip)
            if "sources" in fldvalue:
                if isinstance(fldvalue["sources"], str):
                    fldroot[fldname]["sources"] = fldvalue["sources"]
                elif isinstance(fldvalue["sources"], list):
                    core.mtypes.addMTypeSource(self.mtype, fldname, { "codes": fldvalue["sources"]})
                    fldroot[fldname]["sources"] = self.mtype + "." + fldname
                else:
                    print("Invalid source type", self.mtype, fldname, type(fldvalue["sources"]))

            # proc subfields (for links)
            if fldroot[fldname]["datatype"] == "link":
                self._linkFields.add(fldname)
                if "properties" in fldvalue:
                    fldroot[fldname]["properties"] = {}
                    subfldroot = fldroot[fldname]["properties"]
                    for n, v in fldvalue["properties"].items():
                        subfldroot[n] = {}
                        self.procField(subfldroot, n, v)


    def procSources(self):
        if "sources" in self.loaded_data:
            for k in self.loaded_data["sources"]:
                core.mtypes.addMTypeSource(self.mtype, k, self.loaded_data["sources"][k])

    def validateData(self):
        # sanity check for required fields: name and description
        for req in ['name', 'description']:
            if not req in self.loaded_data:
                print("FATAL:", self.filename, "missing required field", req)
                exit()

        # properties can be absent on mtype file - add it if missing
        if not "properties" in self.loaded_data:
            self.loaded_data["properties"] = {}

    def asDict(self):
        obj = {
            "mtype": self.mtype,
            "name": self.name,
            "description": self.description,
            "namespace": self.namespace,
            "fa_icon": self.fa_icon,
            "properties": self.properties,
            "modules": self.modules,
            "sources": self.sources,
        }
        return obj

    def serialize(self, ind=None):
        s = json.dumps(self.asDict(), indent = ind)
        return s

def set_json_default(obj):
    if isinstance(obj, set):
        #return list(obj)
        return sorted(obj)
    raise TypeError

class MetaTypesBroker:
    """Global MTypes Broker / Manager"""

    def __init__(self):
        # root for mtype template files
        self.mtypes = []
        self.sources = {}

    def dbgdump(self):
        print("Dumping", len(self.mtypes), 'mtypes')
        for mt in self.mtypes:
            fname = core.config["folders"]["user_scratch"]
            fname = Path.joinpath(fname, 'dbg_' + mt.mtype + '.json')
            #print("DBG:mtype", mt.mtype, mt.path, 'into', fname)
            #s = json.dumps(mt.data)
            #s = json.dumps(mt.data, indent=4) #, default=set_json_default)
            s = json.dumps(mt.asDict(), indent=4) #, default=set_json_default)

            with open(fname, 'w') as f:
                #f.write(json.dumps(mt.data, indent=4))
                f.write(s)

        res = {}
        for mt in self.mtypes:
            #res[mt.mtype] = copy.deepcopy(mt.data)
            res[mt.mtype] = mt.asDict()

        fname = core.config["folders"]["user_scratch"]
        fname = Path.joinpath(fname, 'dbg_all_mtypes.json')
        s = json.dumps(res, indent=4, default=set_json_default)
        with open(fname, 'w') as f:
                f.write(s)

    def addMtype(self, mt: MetaType):
        self.mtypes.append(mt)

    def loadFiles(self):

        def procFolder(folder: Path, ns):
            for f in folder.iterdir():
                if f.is_dir():
                    if not f.stem.startswith("_"):
                        fn = Path.joinpath(f, f.stem + ".json")
                        mt = MetaType(fn, ns)
                        self.addMtype(mt)

        # load all mtypes into in-memory structure
        # lifecycle is important, this will be needed to construct routes for api server
        self.mtypes.clear()
        self.sources.clear()

        # 1 - load system mtypes
        procFolder(core.config["folders"]["system_mtypes"], "")

        # 2 - load user/local mtypes
        procFolder(core.config["folders"]["user_mtypes"], "user")

        # 3 - load imported mtypes
        procFolder(core.config["folders"]["imported_mtypes"], "imported")

        # 4 - load global sources
        p = Path(core.config["folders"]["global_sources"])
        if p.is_dir():
            for f in p.iterdir():
                if f.is_file():
                    if not f.stem.startswith("_") and f.suffix == ".json":
                        self.loadSource(f)

    def loadSource(self, fl):
        #print("loading source", fl)
        with open(fl, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            self.sources[fl.stem] = data

    def addMTypeSource(self, mt, srcname, srcdata):

        sn = mt + "." + srcname
        obj = {
            "name": sn,
            "description": sn,
            "codes": {}
        }
        if "name" in srcdata: obj["name"] = srcdata["name"]
        if "description" in srcdata: obj["description"] = srcdata["description"]
        if "codes" in srcdata:
            # must have a codes key
            v = srcdata["codes"]
            if isinstance(v, list):
                for k in v:
                    s = k.split('|')
                    if len(s) == 2:
                        obj["codes"][s[0]] = { "value": s[1]}
                    else:
                        obj["codes"][k] = { "value": k}
            elif isinstance(v, dict):
                for k in v:
                    x = 1

        self.sources[sn] = obj

    def getSource(self, srcname, api = False):
        if srcname in self.sources:
            src = self.sources[srcname]
            if api:
                res = {
                    "name": src["name"],
                    "description": src["description"],
                    "codes": []
                }
                for key in src["codes"]:

                    res["codes"].append({
                        "code": key,
                        "value": src["codes"][key]["value"]
                    })
                return res
            else:
                return src
        return None

    def getSourceValue(self, src, code):
        code = code.lower()
        if src in self.sources:
            #print("source found", src)
            if code in self.sources[src]["codes"]:
                return self.sources[src]["codes"][code]
        return None

    def getRandomSourceValue(self, src, rand = None):
        # helper for testing sources
        if rand:
            r = rand
        else:
            r = random
        s = self.getSource(src)
        if s:
            r = r.randrange(0, len(s["codes"]))
            l = list(s["codes"])
            res = l[r] + "|" + s["codes"][l[r]]["value"]
            return res

        # if not found
        return ""

    def listSources(self):
        res = []
        for k in self.sources:
            res.append({
                "code": k,
                "name": self.sources[k]["name"],
                "description": self.sources[k]["description"]
            })
        return res

    def getMType(self, mtname):
        for mt in self.mtypes:
            if mt.mtype == mtname:
                return mt
        return None

    def getMtypes(self):
        # simple list of unique mtypes
        res = []
        for mt in self.mtypes:
            res.append(mt.mtype)
        return res

    def getList(self):
        # returns full mtype library as list
        res = []
        for mt in self.mtypes:
            res.append(mt.asDict())
        return res

    def getJson(self):
        # returns full mtype library as json
        l = []
        for mt in self.mtypes:
            l.append(mt.asDict())
        res = json.dumps(l)
        return res
