from src import core
from datetime import datetime
from pathlib import Path
import uuid
from src.mtypes import *
import copy
import logging
log = logging.getLogger(__name__)

class DataResource:
    def __init__(self, mtype = None, guid = None):
        self.mtype = mtype
        self.name = ""
        self.description = ""
        self.properties = {}
        self.custom = {}

        self._is_altered = False
        self._is_saved = False
        if guid:
            self.guid = guid
        else:
            self.guid = str(uuid.uuid4())
        self.modified_at = datetime.now()

        self.created_version = core.version_string
        self.modified_version = core.version_string

        # filename will only be defined if mtype and guid are specified
        # this is done through the property 'filename'
        self._filename = None

        if mtype != None: self.name = "new " + mtype

    @property
    def filename(self):
        # if filename is still not set, tries to set it here
        if self._filename == None:
            if self.mtype != None and self.guid != None:
                # both mtype and guid need to be defined in order to assign a filename
                pth = Path.joinpath(core.config["folders"]["user_data"], self.mtype + "_" + self.guid + ".json")
                self._filename = pth
        return self._filename

    @property
    def is_altered(self):
        return self._is_altered

    @property
    def is_saved(self):
        return self._is_saved

    def getMtypeDef(self):
        return core.mtypes.getMType(self.mtype)

    def loadFromFile(self, fl: Path):
        # existing filename is overriden when loading from a file
        self._filename = fl
        with open(self._filename, encoding='utf-8') as json_file:
            data = json.load(json_file)
            self.assignDict(data, True)

    def assignDict(self, data, is_loading = False):
        # loads from an object (assumed a dict for now)
        # is used when loading from file
        # is_loading indicates its being loaded from file, and will reconstruct links
        # if not loading from file, it will maintain link fields intact

        def safeval(k, d = None):
            nonlocal data
            if k in data:
                return data[k]
            return d

        if "mtype" in data: self.mtype = data["mtype"]
        if "guid" in data: self.guid = data["guid"]
        if "modified_at" in data:
            self.modified_at = datetime.fromisoformat(data["modified_at"])
        else:
            self.modified_at = datetime.now()

        if "created_version" in data: self.created_version = data["created_version"]
        if "modified_version" in data: self.modified_version = data["modified_version"]
        if "name" in data: self.name = data["name"]
        if "description" in data: self.description = data["description"]
        if "properties" in data: self.properties = data["properties"]
        if "custom" in data: self.custom = data["custom"]

        # remove link fields if present - links come from dedicated links file
        if is_loading:
            mtdef = self.getMtypeDef()
            if mtdef:
                for f in mtdef._linkFields:
                    # keeps link data and removes it from properties
                    self.properties.pop(f, None)
            else:
                log.critical(f"Invalid mtype [{self.mtype}] while loading object")

            # reconstruct link fields from the information in the links file
            links = core.data.getLinkFieldsFor(self.guid)
            for l in links:
                #print('xxx', l, links[l])
                self.properties[l] = links[l]

            #print("field links", json.dumps(links, indent=4, ensure_ascii=False))
            #print("field links", json.dumps(self.properties, indent=4, ensure_ascii=False))


    def save(self):
        # saves data object to disk, while synchronizing links
        # link fields are kept in the in-memory objects but are not saved to the object file
        # they are instead stored in a specific file
        # the link field removal and restoring is a bit wonky and should be improved, but possible only when switching to database storage

        # process links
        links = {}

        # saves full copy of properties before removing links
        saveProps = copy.deepcopy(self.properties)

        mtdef = self.getMtypeDef()
        if mtdef:
            for f in mtdef._linkFields:
                # keeps link data and removes it from properties
                obj = self.properties.pop(f, None)
                if obj:
                    links[f] = obj
        else:
            log.critical(f"Invalid mtype [{self.mtype}] while saving object")

        core.data.syncLinks(self.guid, self.mtype, links)

        f = self.filename
        d = self.serialize(core.config["json_indent"])

        f.parent.mkdir(parents=False, exist_ok=True)
        try:
            with open(f, 'w', encoding="utf-8") as fl:
                fl.write(d)
            self._is_saved = True
            self._is_altered = False

            # restores full properties with link fields included
            self.properties = copy.deepcopy(saveProps)

            # adds to in memory data, if not already there
            core.data.commitData(self)
        except Exception as e:
            log.critical(f"Error writing file for [{self.mtype}] f{self.guid}")
            print("Error writing file", e)

    def normalize(self):
        # returns a structure with all values as strings
        res = {
            "mtype": self.mtype,
            "guid": self.guid,
            "modified_at": self.modified_at.isoformat("T", "seconds"),
            "created_version": self.created_version,
            "modified_version": self.modified_version,
            "name": self.name,
            "description": self.description,
            "properties": {}
        }
        res["properties"] = self.properties.copy()

        if len(self.custom)>0:
            res["custom"] = self.custom.copy()

        return res

    def serialize(self, ind=None):
        res = json.dumps(self.normalize(), indent=ind, ensure_ascii=False, cls=core.customEncoder)
        return res

    def addLink(self, fldname, guid, props = None):
        # convenient helper to add a linked field to properties
        # doesnt save the record

        # TODO: validate props
        rel = core.data.findByGuid(guid)
        if rel:
            if not fldname in self.properties:
                self.properties[fldname] = []
            obj = {
                "to": guid,
                "mtype": rel.mtype,
                "label": rel.name
            }
            if props:
                obj["properties"] = props
            self.properties[fldname].append(obj)
        else:
            log.warn(f"Guid {guid} not found in addLink")

class DataBrokerClass:

    def __init__(self):
        self.data = {}
        self.indexes = {}
        self.links = {}
        self.links_filename = Path.joinpath(core.config["folders"]["user_data"], "links.json")
        self._links_saved = True
        self._links_altered = False

    def new(self, mtype = None, guid = None):
        # creates new resource of mtype
        return DataResource(mtype, guid)

    def commitData(self, data):
        self.data[data.guid] = data

    def getLinkFieldsFor(self, guid):
        res = {}
        if guid in self.links:
            links = self.links[guid]
            for fld in links["fields"]:
                res[fld] = []
                for lnk in links["fields"][fld]["links"]:
                    obj = {
                        "to": lnk["to"],
                        "mtype": lnk["mtype"],
                        "label": lnk["label"]
                    }
                    if "properties" in lnk:
                        obj["properties"] = copy.deepcopy(lnk["properties"])
                    res[fld].append(obj)
        #print("field links", json.dumps(res, indent=4, ensure_ascii=False))
        return res

    def syncLinks(self, guid, mtype, links):
        # remove all links to current guid
        if guid in self.links:
            self._links_altered = True
            self.links.pop(guid)

        if len(links) > 0:
            # add links
            obj = {"mtype": mtype, "fields": {}}
            #print("sync links", json.dumps(links, indent=4, ensure_ascii=False, cls=core.customEncoder))

            for linkfield in links:
                obj["fields"][linkfield] = { "links": [] }
                for lnk in links[linkfield]:
                    tmp = {
                        "to": lnk["to"],
                        "mtype": lnk["mtype"],
                        "label": lnk["label"]
                    }

                    if "properties" in lnk:
                        tmp["properties"] = lnk["properties"]
                    obj["fields"][linkfield]["links"].append(tmp)

            #print(json.dumps(obj, indent=4, ensure_ascii=False, cls=core.customEncoder))
            if len(obj["fields"]) > 0:
                self._links_altered = True
                self.links[guid] = obj

        if self._links_altered:
            #print("saving links", self.links)
            self.saveLinks()

    def saveLinks(self):
        # links file: dict of guids
        # each item has a dict of fields, with an array of link definitions
        d = json.dumps(self.links, indent=core.config["json_indent"], ensure_ascii=False, cls=core.customEncoder)

        self.links_filename.parent.mkdir(parents=False, exist_ok=True)
        try:
            with open(self.links_filename, 'w', encoding="utf-8") as f:
                f.write(d)
            self._links_saved = True
            self._links_altered = False

        except Exception as e:
            print("Error writing file", e)

    def getLinksTo(self, guid):
        # returns list of links pointing to specified guid
        # format is the same as links structure, with added "from" field containing the linking guid
        res = []
        for l in self.links:
            if "fields" in self.links[l]:
                for fld in self.links[l]["fields"]:
                    if "links" in self.links[l]["fields"][fld]:
                        lnks = self.links[l]["fields"][fld]["links"]
                        for i in lnks:
                            if i["to"] == guid:
                                obj = copy.deepcopy(i)
                                obj["from"] = l
                                res.append(obj)
        return res

    def findByGuid(self, guid):
        if guid in self.data:
            return self.data[guid]
        return None

    def intDeleteObjectFile(self, fname, hard = False):
        if Path(fname).is_file():
            if hard:
                return core.safeDeleteFile(fname)
            else:
                # soft delete moves file to deleted folder
                dfn = Path.joinpath(core.config["folders"]["user_deleted_data"], Path(fname).name)
                #Path(fname).rename(dfn)

            return True
        return False

    def deleteByGuid(self, guid, hard = False):
        '''
        TODO: soft deletion
        overriding hard to true until soft deletion is implemented
        '''
        hard = True

        obj = self.findByGuid(guid)
        if obj:
            if self.intDeleteObjectFile(obj.filename, hard):
                self.data.pop(guid)
                # removes links
                if guid in self.links:
                    self._links_altered = True
                    self.links.pop(guid)

                # TODO: remove links to this object
                # might wait until database storage to go forward on this

                if self._links_altered:
                    self.saveLinks()

                return True
        return None

    def validate(self, obj):
        def checkProp(prop, mtrules):
            # validates property values according to mtype rules
            nonlocal obj, res
            #print("checking", prop, mtrules["label"])

        res = core.GenemedeResponse()
        if "mtype" in obj:
            mt = core.mtypes.getMType(obj["mtype"])
            if mt:
                for p in mt.data["properties"]:
                    checkProp(p, mt.data["properties"][p])

                for m in mt.data["modules"]:
                    for p in mt.data["modules"][m]["properties"]:
                        checkProp(p, mt.data["modules"][m]["properties"][p])

            else:
                res.error("Invalid mtype", value=obj["mtype"])

        else:
            res.error("mtype not present", context="mtype")

        return res

    def postData(self, jsn):
        # POST creates new object
        # thus, if guid is specified and already exists (or other unique checking mechanism fails) this fails
        res = None

        try:
            # create object and return guid
            # TODO: validate against mtype rules
            if "mtype" in jsn:
                objmt = jsn["mtype"]
                hasguid = "guid" in jsn
                mt = core.mtypes.getMType(objmt)
                if mt:
                    if hasguid:
                        # must not yet exist
                        if jsn["guid"] in self.data:
                            # add specific error to response
                            log.error(f"GUID already exists in POST: {jsn['guid']}")
                            return False

                    obj = DataResource(objmt)
                    obj.assignDict(jsn)
                    # set properties for new object
                    obj.modified_at = datetime.now()
                    obj.created_version = core.version_string
                    obj.modified_version = core.version_string
                    obj.save()
                    res = obj.normalize()
            else:
                # add specific error to response
                pass

        except Exception as e:
            # TODO: add to log or report
            s = str(e)
            log.error(f"Error on postData: " + s)
            res = None

        return res

    def putData(self, jsn):
        # resource must exist
        # returns save object with updated control fields
        res = None
        try:
            if "mtype" in jsn:
                objmt = jsn["mtype"]
                mt = core.mtypes.getMType(objmt)
                if mt:
                    if "guid" in jsn:
                        # must exist
                        obj = self.findByGuid(jsn["guid"])
                        obj.assignDict(jsn)
                        obj.modified_at = datetime.now()
                        obj.created_version = core.version_string
                        obj.modified_version = core.version_string
                        obj.save()
                        res = obj.normalize()
            else:
                pass

        except Exception as e:
            s = str(e)
            log.error(f"Error on postData: " + s)
            res = None
        return res

    def getStats(self):
        res = {
            "total_files": 0,
            "total_mtypes": len(core.mtypes.mtypes)
        }
        res["total_files"] = len(self.data)
        res["mtypes"] = {}

        # count by mtype
        for obj in self.data:
            mt = self.data[obj].mtype
            if mt in res["mtypes"]:
                res["mtypes"][mt] += 1
            else:
                res["mtypes"][mt] = 1

        return res

    def loadData(self):
        # loads all existing data to memory
        def procfolder(folder: Path, parent: MetaType = None):
            for f in folder.iterdir():
                if f.is_dir():
                    if not f.stem.startswith("_"):
                        procfolder(f)
                elif f.is_file():
                    if not f.stem.startswith("_") and f.suffix == ".json" and f.stem != "links":
                        obj = DataResource()
                        obj.loadFromFile(f)
                        self.data[obj.guid] = obj

        # reinitializes data
        self.data.clear()
        self.links = {}

        # load links before loading records so link reconstruction is available

        if Path(self.links_filename).is_file():
            with open(self.links_filename, encoding='utf-8') as json_file:
                try:
                    data = json.load(json_file)
                    self.links = data
                except Exception as e:
                    s = str(e)
                    log.error(f"Error loading links file: " + s)

        # load records
        procfolder(core.config["folders"]["user_data"])
        #print("- data loaded", len(self.data))

    def buildIndexes(self):
        def sortkey(v):
            return v[0] + v[1]

        # starting with simple indexes for name and modified_at
        self.indexes= {}
        for mt in core.mtypes.mtypes:
            self.indexes[mt.mtype + ":name"] = []
            self.indexes[mt.mtype + ":modified_at"] = []

        for obj in self.data:
            k = self.data[obj].name
            #print("IDX", k)
            if k != "":
                kv = k.lower()
                # lower case value, guid, original value
                self.indexes[self.data[obj].mtype + ":name"].append([kv, self.data[obj].guid, k])

            k = self.data[obj].modified_at.isoformat()
            if k != "":
                # lower case value, guid, original value
                self.indexes[self.data[obj].mtype + ":name"].append([k, self.data[obj].guid])

        for mt in core.mtypes.mtypes:
            self.indexes[mt.mtype + ":name"].sort(key=sortkey)
            self.indexes[mt.mtype + ":modified_at"].sort(key=sortkey)

        #print("indexes", self.indexes)

    def listResource(self, mtype):
        # returns guids
        # could eventually be done through a more complex search mechanism if implemented
        res = []
        for obj in self.data:
            if self.data[obj].mtype == mtype:
                res.append({
                    "guid": obj,
                    "mtype": self.data[obj].mtype,
                    "label": self.data[obj].name
                })

        return res

    def search(self, q, mt = None, flds = None):
        def checkcur(curvalue):
            #print("check", curvalue)
            nonlocal found
            v = curvalue
            f = False
            if isinstance(v, str):
                pp = v.casefold().find(q)
                f = pp >= 0
            if f:
                found = True

        res = []
        q = q.casefold()
        if mt:
            mtypes = set(mt.split(','))
        else:
            mtypes = None

        if flds:
            fields = set(flds.split(','))
        else:
            fields = None

        # iterate all data objects
        for obj in self.data:
            # prefilter by mtype if specified
            dothis = True
            if mtypes:
                dothis = self.data[obj].mtype in mtypes
            if not dothis:
                continue

            cur = self.data[obj]
            found = False

            # search loop
            if fields != None:
                # if fields is specified
                for prop in fields:
                    found = False
                    if prop == "name":
                        checkcur(cur.name)
                    elif prop == "description":
                        checkcur(cur.description)
                    else:
                        if prop in cur.properties:
                            checkcur(cur.properties[prop])
            else:
                # if fields is empty, search all properties
                checkcur(cur.name)
                checkcur(cur.description)
                for prop in self.data[obj].properties:
                    checkcur(cur.properties[prop])

            # add result when found
            if found:
                res.append({
                    "guid": obj,
                    "mtype": self.data[obj].mtype,
                    "label": self.data[obj].name
                })
        return res

    def exportData(self):
        usr = f"{core.config['user']['name']} ({core.config['user']['email']})"
        res = {
            "_version": core.version_string,
            "guid": str(uuid.uuid4()),
            "modified_at": datetime.now(),
            "datatype": "export",
            "name": "Exported Data",
            "description": "Exported data for " + usr,
            "data": []
        }
        for obj in self.data:
            cur = self.data[obj]
            res["data"].append(cur.normalize())

        return res

    def exportDataToFile(self):
        res = self.exportData()
        fname = core.config["folders"]["user_scratch"]
        d = datetime.now()
        fname = Path.joinpath(fname, "export_" + d.strftime("%Y%m%d%H%M%S") + ".gnmd.json")
        s = json.dumps(res, indent=4, ensure_ascii=False, cls=core.customEncoder)
        with open(fname, 'w') as f:
            f.write(s)
        return fname

