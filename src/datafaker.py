import sys
from src import core
from faker import Faker
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

class GenemedeDataFaker:
    def __init__(self):
        self.faker = None
        self.total_researchers = 500
        self.total_subjects = 5000
        self.total_labs = 10
        self.total_projects = 50
        self.total_labs_per_project = 3
        self.total_researchers_per_project = 20
        self.total_subjects_per_project = 1000

        self.total_researchers = 50
        self.total_subjects = 500
        self.total_labs = 5
        self.total_projects = 10
        self.total_labs_per_project = 2
        self.total_researchers_per_project = 10
        self.total_subjects_per_project = 100

        self.total_researchers = 10
        self.total_subjects = 50
        self.total_labs = 5
        self.total_projects = 10
        self.total_labs_per_project = 2
        self.total_researchers_per_project = 3
        self.total_subjects_per_project = 5
        self.total_ethics_per_project = 3

        # use prepared guids
        gfl = open(Path(Path().absolute(), 'seed/guidlist.json'))
        self.guids = gfl.read().splitlines()
        self.gidx = 0

        self.basedate = datetime(2024, 1, 1, 12, 0, 0, 0)

    def popguid(self):
        s = self.guids[self.gidx]
        self.gidx += 1
        return s

    def intRandomFromSource(self, src):
        x = core.mtypes.getSource(src)
        if x:
            r = self.faker.random.randrange(0, len(x["codes"]))
            l = list(x["codes"])
            res = l[r] + "|" + x["codes"][l[r]]["value"]
            return res
        # if not found
        return ""

    def hlpFakeField(self, obj, fld, func):
        fn = getattr(self.faker, func)
        if fn:
            obj.properties[fld] = fn()

    def createResearchers(self):
        # creates a pool of researchers
        print("Creating", self.total_researchers, "researchers :", end =" ")
        for i in range(self.total_researchers):
            g = self.popguid()
            obj = core.data.new("researcher", guid=g)
            obj.name = self.faker.name()
            obj.description = "Description for " + obj.name
            d = self.basedate

            obj.properties["subject_fields"] = self.faker.text()
            obj.properties["latest_educational_qualification"] = self.intRandomFromSource("researcher.latest_educational_qualification")
            obj.properties["education_level"] = self.intRandomFromSource("researcher.education_level")
            obj.properties["certifications"] = self.faker.text()

            obj.properties["contact_phone"] = self.faker.phone_number()
            obj.properties["contact_email"] = self.faker.email()
            obj.properties["contact_website"] = self.faker.uri()
            obj.properties["contact_address"] = self.faker.address()

            obj.properties["projects"] = self.faker.text()
            #obj.properties["project_role"] = self.faker.job()

            obj.properties["sex"] = self.intRandomFromSource("sex")
            obj.properties["age"] = self.faker.random.randrange(18, 100)
            obj.properties["handedness"] = self.intRandomFromSource("researcher.handedness")
            obj.properties["handedness_value"] = self.intRandomFromSource("ehi-10")
            obj.properties["primary_language"] = self.intRandomFromSource("iso639-1")
            obj.properties["secondary_language"] = self.intRandomFromSource("iso639-1")
            obj.properties["additional_comments"] = self.faker.text()

            obj.save()
        print("Done")

    def createSubjects(self):
        # creates a pool of subjects
        print("Creating", self.total_subjects, "subjects :", end =" ")
        for i in range(self.total_subjects):
            g = self.popguid()
            obj = core.data.new("subject", guid=g)
            obj.name = self.faker.name()

            # module - human
            obj.properties["module.human"]= {}
            mod = obj.properties["module.human"]
            mod["sex"] = self.intRandomFromSource("sex")
            mod["age"] = self.faker.random.randrange(18, 100)
            mod["education_level"] = self.intRandomFromSource("subject.education_level")
            mod["handedness"] = self.intRandomFromSource("subject.handedness")
            mod["handedness_value"] = self.intRandomFromSource("ehi-10")
            mod["primary_language"] = self.intRandomFromSource("iso639-1")
            mod["secondary_language"] = self.intRandomFromSource("iso639-1")
            mod["visual_acuity"] = self.intRandomFromSource("subject.visual_acuity")
            mod["auditory_sensitivity"] = self.faker.text()
            mod["compensation"] = self.intRandomFromSource("subject.compensation")
            mod["compensation_value"] = self.intRandomFromSource("subject.compensation_value")
            mod["additional_comments"] = self.faker.text()

            # module - mpi
            obj.properties["module.mpi"]= {}
            mod = obj.properties["module.mpi"]
            mod["race"] = self.intRandomFromSource("race-nih")
            mod["health_history_of_medical_conditions"] = self.faker.text()
            mod["psychiatric_history"] = self.faker.text()
            mod["substance_use"] = self.faker.text()
            mod["history_of_medication"] = self.faker.text()
            mod["musical_training"] = self.intRandomFromSource("subject.musical_training")

            # module - visual
            obj.properties["module.visual"]= {}
            mod = obj.properties["module.visual"]
            mod["visual_correction_method"] = self.intRandomFromSource("subject.visual_correction_method")
            mod["visual_eye_dominance"] = self.intRandomFromSource("subject.visual_eye_dominance")
            mod["visual_lens_power_left"] = round(self.faker.random.uniform(0,3), 2)
            mod["visual_lens_power_right"] = round(self.faker.random.uniform(0,3), 2)
            mod["visual_colorblind"] = self.intRandomFromSource("subject.visual_colorblind")
            obj.save()

        print("Done")

    def createLabs(self):
        # creates a pool of labs
        print("Creating", self.total_labs, "labs :", end =" ")
        for i in range(self.total_labs):
            g = self.popguid()
            obj = core.data.new("lab", guid=g)
            obj.name = self.faker.company()
            obj.description = self.faker.catch_phrase()
            obj.properties["official_name"] = self.faker.name()
            obj.properties["contact_phone"] = self.faker.phone_number()
            obj.properties["contact_email"] = self.faker.email()
            obj.properties["contact_website"] = self.faker.uri(),
            obj.properties["contact_address"] = self.faker.address()
            obj.save()
        print("Done")

    def createProjects(self):
        # creates a pool of projects
        print("Creating", self.total_projects, "projects :", end =" ")
        for i in range(self.total_projects):
            g = self.popguid()
            obj = core.data.new("project", guid=g)
            obj.name = self.faker.company()
            obj.description = self.faker.catch_phrase()
            obj.properties["project_lead"] = self.faker.name()
            obj.properties["project_manager"] = self.faker.name()
            obj.properties["data_manager"] = self.faker.name()
            d = self.basedate
            obj.properties["project_start_date"] = d - relativedelta(months=self.faker.random.randrange(12, 24))
            obj.properties["project_end_date"] = d + relativedelta(months=self.faker.random.randrange(24, 36))
            obj.properties["project_digital_tools"] = self.faker.text()
            obj.properties["project_legacy_management"] = self.faker.text()

            # picks random labs to assign to project
            lst = core.data.listResource("lab")
            for n in range(self.total_labs_per_project):
                idx = self.faker.random.randrange(len(lst))
                vg = lst[idx]["guid"]
                obj.addLink("labs", vg)
                lst.pop(idx)

            # picks random researchers to assign to project
            lst = core.data.listResource("researcher")
            for n in range(self.total_researchers_per_project):
                idx = self.faker.random.randrange(len(lst))
                vg = lst[idx]["guid"]
                obj.addLink("members", vg)
                lst.pop(idx)

            # picks random subjects to assign to project
            lst = core.data.listResource("subject")
            lstlen = len(lst)
            for n in range(self.total_subjects_per_project):
                idx = self.faker.random.randrange(len(lst))
                vg = lst[idx]["guid"]
                obj.addLink("subjects", vg)
                relobj = core.data.findByGuid(vg)
                lst.pop(idx)

            # adds ethics blocks
            obj.properties["module.ethics"] = []
            for n in range(self.total_ethics_per_project):
                eth = {
                    "responsible_member": self.faker.name(),
                    "responsible_institute": self.faker.company(),
                    "protocol_number": self.faker.isbn13(),
                    "approving_committee": self.faker.company(),
                    "start_date": self.basedate - relativedelta(months=self.faker.random.randrange(12, 24)),
                    "end_date": self.basedate + relativedelta(months=self.faker.random.randrange(24, 36)),
                    "required_certifications": self.faker.text()
                }
                obj.properties["module.ethics"].append(eth)

            # add a funding block
            obj.properties["module.funding"] = []
            tmp = {
                "funding_agency": self.faker.company(),
                "grant_ID": self.faker.isbn13(),
                "grant_application": self.faker.text(),
                "grantee": self.faker.name(),
                "legal_signatory": self.faker.name(),
                "funding_start_date": self.basedate - relativedelta(months=self.faker.random.randrange(12, 24)),
                "funding_end_date": self.basedate + relativedelta(months=self.faker.random.randrange(24, 36)),
                "funding_amount": self.faker.random.randrange(100000, 10000000, step=50000),
                "funding_currency": "EUR",
                "grant_website": self.faker.uri(),
            }
            obj.properties["module.funding"].append(tmp)

            # add a outputs block
            obj.properties["module.outputs"] = []
            tmp = {
                "project_website": self.faker.uri(),
                "preregistration": self.faker.uri(),
                "communication": "posters",
                "publications": self.faker.text(),
                "code_repository": self.faker.uri(),
                "data_repository": self.faker.uri(),
                "outreach": self.faker.text(),
                "digital_resources": self.faker.text(),
            }
            obj.properties["module.outputs"].append(tmp)

            obj.save()

        print("Done")

    def run(self):
        if core.envvar("ALLOW_FAKER") != "1":
            print("Faker is disabled")
            exit()

        self.faker = Faker()
        Faker.seed(2024)
        print("Faking data")
        self.createResearchers()
        self.createSubjects()
        self.createLabs()
        self.createProjects()

        # links:
        # subject: creator, person_responsible
        # lab: members




