import sys
import os
import argparse
from src import core
from pathlib import Path
import json
import uuid
import csv
from src import datafaker

def doNuke(confirm=True):
    # this nukes all data
    # useful for development, should be removed once data is imported / stabilized
    # or at least have some failsafes
    if core.envvar("ALLOW_NUKER") != "1":
        print("Nuker is disabled")
        exit()

    if confirm:
        print("Type \033[4mnuke\033[0m to confirm:")
        cn = input()
        if (cn != "nuke"):
            print("Cancelled")
            exit()

    if (core.config["folders"]["user_data"]):
        print("Nuking data:\033[1m", core.config["folders"]["user_data"], "\033[0m")
        tot = 0
        for f in core.config["folders"]["user_data"].iterdir():
            if f.is_file():
                tot += 1
                os.remove(f)
        print(f"{tot} files deleted.")

def doTestSubjects():
    def readcsv(fn):
        nonlocal seedroot
        fn = Path.joinpath(seedroot, fn)
        with open(fn, 'r') as infile:
            reader = csv.DictReader(infile)
            fnames = reader.fieldnames
            return fnames

    def addfields(flds, idx):
        nonlocal matrix
        for f in flds:
            if not f in matrix:
                matrix[f] = [False, False, False, False]
            matrix[f][idx] = True

    def addcontext(b, s):
        res = ""
        if b:
            res = "[" + s + "]"
        else:
            res = "[    ]"
        return res


    # test subject files for dev purposes
    if False:
        smt = core.mtypes.getMType("subject")
        for p in smt.data["properties"]: print(p)

        for m in smt.data["modules"]:
            for p in smt.data["modules"][m]["properties"]: print(p)

    seedroot = Path(Path().absolute(), 'seed/data')

    # gnmd_ECOG, gnmd_fMRI, gnmd_MEEG

    # build field matrix
    matrix = {}
    f = readcsv("gnmd_ECOG.csv")
    addfields(f, 1)

    f = readcsv("gnmd_fMRI.csv")
    addfields(f, 2)

    f = readcsv("gnmd_MEEG.csv")
    addfields(f, 3)

    for f in matrix:
        s = ""
        s = s + addcontext(matrix[f][0], 'GNMD')
        s = s + addcontext(matrix[f][1], 'ECOG')
        s = s + addcontext(matrix[f][2], 'FMRI')
        s = s + addcontext(matrix[f][3], 'MEEG')
        print(s, f)


def doSeeder():
    if core.envvar("ALLOW_SEEDER") != "1":
        print("Seeder is disabled")
        exit()

    # seeds full data using existing json files as much as possible
    doNuke(False)

    def copyvalue(vname, obj, data):
        obj.properties[vname] = data["properties"][vname]

    def popguid():
        nonlocal guids, gidx
        s = guids[gidx]
        gidx += 1
        return s

    # seed data files are here
    seedroot = Path(Path().absolute(), 'seed/data')

    # use prepared guids
    gfl = open(Path(Path().absolute(), 'seed/guidlist.json'))
    guids = gfl.read().splitlines()
    gidx = 0

    # import subjects
    if False:
        # gnmd_ECOG, gnmd_fMRI, gnmd_MEEG
        #fn = Path.joinpath(seedroot, "gnmd_ECOG.csv")
        fn = Path.joinpath(seedroot, "gnmd_fMRI.csv")
        #fn = Path.joinpath(seedroot, "gnmd_MEEG.csv")
        with open(fn, encoding="utf-8", newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in spamreader:
                print(', '.join(row))
                break
        exit()


    # import labs
    fn = Path.joinpath(seedroot, "labs.json")
    with open(fn, encoding="utf-8") as json_file:
        data = json.load(json_file)
        for k in data:
            g = popguid()
            lab = core.mdata.new("lab", guid=g)
            lab.name = k["name"]
            copyvalue("official_name", lab, k)
            copyvalue("principal_investigator", lab, k)
            copyvalue("institute", lab, k)
            copyvalue("department", lab, k)
            copyvalue("location", lab, k)
            copyvalue("contact_phone", lab, k)
            copyvalue("contact_email", lab, k)
            copyvalue("contact_website", lab, k)
            copyvalue("contact_address", lab, k)
            lab.save()

    # import researchers
    fn = Path.joinpath(seedroot, "researchers_basic.json")
    with open(fn, encoding="utf-8") as json_file:
        data = json.load(json_file)
        skip = False # we skip the first item
        for k in data:
            if not skip:
                skip = True
            else:
                g = popguid()
                ppl = core.mdata.new("researcher", guid=g)

                # trim leading and trailing space on names
                s = k["name"].strip(" ")

                # remove everything after comma on name
                p = s.find(",")
                if p > 0:
                    s = s[0:p]

                # fix some wrong names
                if s == "Katarina Bentz": s = "Katarina Bendtz"
                if s == "Urzula Gorska": s = "Urszula Górska"
                if s == "David Mazumder": s = "David Rahul Mazumder"

                ppl.name = s
                ppl.properties["name"] = s
                ppl.properties["contact_email"] = k["email"].strip(" ")
                ppl.custom["role"] = k["role"].strip(" ")

                ppl.save()
                print(p, "[", ppl.name, "]", "[", s, "]")

    # create the project (we have only one)
    projguid = "f469c4e2-daf0-4976-880b-5e4466a14856"
    projinc = Path.joinpath(seedroot, "projects.json")
    with open(projinc, encoding="utf-8") as json_file:
        data = json.load(json_file)[0]
        proj = core.mdata.new("project", guid=projguid)
        proj.name = data["name"]
        proj.description = data["description"]
        copyvalue("labs", proj, data)
        copyvalue("subjects", proj, data)
        copyvalue("project_start_date", proj, data)
        copyvalue("project_end_date", proj, data)
        copyvalue("project_lead", proj, data)

        # process members
        proj.properties["members"] = []

        lst = data["properties"]["members"][0].split(",")
        for f in lst:
            n = f.strip()
            # fix wrong name
            if n == "Chris tof Koch": n = "Christof Koch"
            if n == "Maximilian Grobbelaar": n = "Maximillian Grobbelaar"
            ppl = core.mdata.search(n, "researcher", "name")
            if len(ppl) == 1:
                proj.properties["members"].append({
                    "guid": ppl[0]["guid"],
                    "mtype": ppl[0]["mtype"],
                    "label": ppl[0]["label"]
                })

            print('XXX', n, ppl, len(ppl))

        #copyvalue("members", proj, data)
        copyvalue("project_manager", proj, data)
        copyvalue("data_manager", proj, data)
        copyvalue("project_digital_tools", proj, data)
        copyvalue("project_legacy_management", proj, data)
        copyvalue("project_website", proj, data)
        copyvalue("preregistration", proj, data)

        # modules - funding
        proj.properties["funding"] = []
        obj = {}
        fields = ["funding_agency", "grant_ID", "grant_application", "grantee", "legal_signatory", "funding_start_date", "funding_end_date", "funding_amount", "funding_currency", "grant_website"]
        for fld in fields:
            obj[fld] = data["custom"]["project_funding"][fld]
        proj.properties["funding"].append(obj)

        # modules - output
        proj.properties["output"] = []
        obj = {}
        fields = ["project_website", "preregistration", "communication", "publications", "code_repository", "data_repository_xnat", "outreach", "digital_resources"]
        for fld in fields:
            obj[fld] = data["custom"]["project_output"][fld]
        proj.properties["output"].append(obj)

        # modules - ethics
        proj.properties["ethics"] = []
        fields = ["responsible_member", "responsible_institute", "protocol_number", "approving_committee", "start_date", "end_date", "required_certifications"]
        for eth in data["custom"]["project_ethics"]:
            obj = {}
            for fld in fields:
                obj[fld] = eth[fld]
            proj.properties["ethics"].append(obj)

        proj.save()

    print("Seeding data")
    # str(uuid.uuid4())

def doDevTest():
    q = "vans"
    q = "mills"
    mt = "researcher"
    flds = "name"
    r = core.data.search(q, mt, flds)
    print(r)
    #from faker import Faker
    # core.mdata.getStats()
    print("gen test")

def doConfigTest():
    print("= config test =")
    print(core.serializeConfig())

def doListResource():
    res = core.data.listResource("project")
    print(res)

def doListMtypes():
    res = core.mtypes.getMtypes
    print(res)

def doFaker():
    if core.envvar("ALLOW_FAKER") != "1":
        print("Faker is disabled")
        exit()

    doNuke(False)

    df = datafaker.GenemedeDataFaker()
    df.run()

def doGuidList():
    fname = core.config["folders"]["user_scratch"]
    fname = Path.joinpath(fname, 'guidlist.json')
    with open(fname, 'w') as f:
        for i in range(1, 10000):
            s = str(uuid.uuid4())
            f.write(s + "\n")

def doGuids():
    for i in range(10):
        print(str(uuid.uuid4()))

def doExport():
    res = core.data.exportData()
    fname = core.config["folders"]["user_scratch"]
    fname = Path.joinpath(fname, 'dbg_all_data.json')
    s = json.dumps(res, indent=4, ensure_ascii=False, cls=core.customEncoder)
    with open(fname, 'w') as f:
        f.write(s)

def doFindByGuid():
    res = core.data.findByGuid(options.guid)
    if res:
        print(res.serialize(4))
    else:
        print("Resource not found")

def doSearch():
    q = options.q
    mt = options.mt
    f = options.f
    res = core.data.search(q, mt, f)
    s = json.dumps(res, indent=4, ensure_ascii=False, cls=core.customEncoder)
    print(s)
    #print(res)

# =====================
argp = argparse.ArgumentParser()
subp = argp.add_subparsers()
subp.add_parser('test', help='used for quickly testing indev stuff').set_defaults(func=doDevTest)
subp.add_parser('config', help='tests configuration').set_defaults(func=doConfigTest)
subp.add_parser('dbgmtypes', help='dumps all mtypes into a json file').set_defaults(func=core.mtypes.dbgdump)
subp.add_parser('tstlist', help='lists resources').set_defaults(func=doListResource)
subp.add_parser('mtypes', help='lists mtypes').set_defaults(func=doListMtypes)
subp.add_parser('nuke', help='erases all current data').set_defaults(func=doNuke)
subp.add_parser('faker', help='creates fake data - WARNING: erases all current data first').set_defaults(func=doFaker)
subp.add_parser('guidlist', help='create a list of guids to use in seeding so that filenames stay the same').set_defaults(func=doGuidList)
subp.add_parser('seed', help='seed with predefined data').set_defaults(func=doSeeder)
subp.add_parser('subjects', help='test data with predefined subjects from arc-cogitate').set_defaults(func=doTestSubjects)
subp.add_parser('guid', help='outputs a number of guids').set_defaults(func=doGuids)
subp.add_parser('export', help='export the entire dataset into a single json file').set_defaults(func=doExport)

p = subp.add_parser('get', help='find resource by guid')
p.add_argument("guid", action="store")
p.set_defaults(func=doFindByGuid)

p = subp.add_parser('search', help='search data')
p.add_argument("q", action="store")
p.add_argument("-mt", type=str, action="store", help="specify mtypes to search, separated by commas")
p.add_argument("-f", type=str, action="store", help="specify fields to search, separated by commas")
p.set_defaults(func=doSearch)

if len(sys.argv) <= 1:
    sys.argv.append('--help')

options = argp.parse_args()

options.func()
