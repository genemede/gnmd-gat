import sys
import os
from src import core
from pathlib import Path
import json
import uuid
import csv
from src import datafaker

def nuker():
    # this nukes all data
    # useful for development, should be removed once data is imported / stabilized
    # or at least have some failsafes
    if (core.config["folders"]["user_data"]):
        print("Nuking data:\033[1m", core.config["folders"]["user_data"], "\033[0m")
        tot = 0
        for f in core.config["folders"]["user_data"].iterdir():
            if f.is_file():
                tot += 1
                os.remove(f)
        print(f"{tot} files deleted.")

def test_subjects():
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




def seeder():
    # seeds full data using existing json files as much as possible
    nuker()

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
            ppl = core.mdata.tmpSearchField("researcher", ["name"], n)
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

#print(sys.argv)
if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        #from faker import Faker
        # core.mdata.getStats()
        print("gen test")

    if sys.argv[1] == "config":
        print("= config test =")
        print(core.serializeConfig())
        #core.writeConfig()

    if sys.argv[1] == "dbgmtypes":
        core.mtypes.dbgdump()

    if sys.argv[1] == "tstlist":
        res = core.mdata.listResource("project")
        print(res)

    if sys.argv[1] == "tstsearch":
        if len(sys.argv) > 2:
            res = core.mdata.intExecSearch(sys.argv[2])
            print("result", res)

    if sys.argv[1] == "mtypes":
        res = core.mtypes.getMtypes()
        print(res)

    if sys.argv[1] == "findbyguid":
        if len(sys.argv) > 2:
            res = core.mdata.findByGuid(sys.argv[2])
            print(res.serialize())
            print(res.mtype)
            print(type(res))

    if sys.argv[1] == 'faker':
        df = datafaker.GenemedeDataFaker()
        df.run()

    if sys.argv[1] == 'nuke':
        if core.envvar("ALLOW_NUKER") != "1":
            print("Nuker is disabled")
            exit()

        print("Type \033[4mnuke\033[0m to confirm:")
        cn = input()
        if (cn == "nuke"):
            nuker()
        else:
            print("Cancelled")

    if sys.argv[1] == 'guidlist':
        # create fixed guids to use in seeding so that filenames stay the same
        fname = Path(Path().absolute(), 'misc')
        fname = Path.joinpath(fname, 'guidlist.json')
        with open(fname, 'w') as f:
            for i in range(1, 10000):
                s = str(uuid.uuid4())
                f.write(s + "\n")

    if sys.argv[1] == 'seed':
        if core.envvar("ALLOW_SEEDER") != "1":
            print("Seeder is disabled")
            exit()

        seeder()

    if sys.argv[1] == 'subjects':
        test_subjects()

    if sys.argv[1] == 'guid':
        for i in range(10):
            print(str(uuid.uuid4()))

else:
    print("no action")
