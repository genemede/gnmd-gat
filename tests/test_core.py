import unittest
import sys, os, json
from datetime import datetime
import copy
import random

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from src import core

def load_ordered_tests(loader, standard_tests, pattern):
    """
    Test loader that keeps the tests in the order they were declared in the class.
    nice QOL hack from https://codereview.stackexchange.com/questions/122532/controlling-the-order-of-unittest-testcases
    """
    ordered_cases = []
    for test_suite in standard_tests:
        ordered = []
        for test_case in test_suite:
            test_case_type = type(test_case)
            method_name = test_case._testMethodName
            testMethod = getattr(test_case, method_name)
            line = testMethod.__code__.co_firstlineno
            ordered.append( (line, test_case_type, method_name) )
        ordered.sort()
        for line, case_type, name in ordered:
            ordered_cases.append(case_type(name))
    return unittest.TestSuite(ordered_cases)

# ===========================================
# Some testes were useful for initial development and might be phased out

class TestTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_findMtype(self):
        mt = core.mtypes.getMType("project")
        self.assertFalse(mt == None, "MType not found")
        #s = core.mtypes.listSources()
        #s = mt.serialize(4)
        #print(s)

class TestData(unittest.TestCase):
    def setUp(self):
        self.tst_researchers = [
            {"guid": "6c5d7021-843f-4dc8-97f1-c1b4744d5ede", "name":"Researcher 1"},
            {"guid": "599bdbd0-51f6-405a-894a-911538039512", "name":"Researcher 2"},
            {"guid": "61a058f4-c555-45ee-8ae4-11e4f09f5cd2", "name":"Researcher 3"},
            {"guid": "02ae7cfa-6a23-46fb-a9f5-9ec7b96c50d7", "name":"Researcher 4"},
            {"guid": "567fac31-0fa9-40ca-8370-35010ea59ed2", "name":"Researcher 5"}
        ]
        self.tst_subjects = [
            {"guid": "6994c90b-52c4-4335-bc65-0891419809c6", "name":"Subject 1"},
            {"guid": "8eea794b-d310-4087-b0e2-d80af9dbfa8c", "name":"Subject 2"},
            {"guid": "b9ecae3b-3d1a-4eb7-85a0-2db0ed8660db", "name":"Subject 3"},
            {"guid": "a2e0f378-0eb6-4f3d-8c9e-09b14e86e0d6", "name":"Subject 4"},
            {"guid": "5893a520-56c8-4d1f-991c-f902b2979be0", "name":"Subject 5"}
        ]

        self.labguid = "73436796-1273-40d5-a8a0-c6c60776dc1c"
        self.projectguid = "267c6239-9d22-4a01-a73d-2aaddea11f80"

    def test_sources(self):
        x = core.mtypes.getSourceValue("iso4217", "eur")
        self.assertFalse(x == "Euro", "Source lookup failed")

        x = core.mtypes.getSource("researcher.latest_educational_qualification")
        self.assertIsNotNone(x, "Researcher random source failed")

        '''
        if x:
            r = random.randrange(1, len(x["codes"]))
            l = list(x["codes"])
            print("Random source", l[r], x["codes"][l[r]]["value"])
        '''

    def test_createRecords(self):
        # create researchers
        for i in self.tst_researchers:
            obj = core.data.new("researcher", guid=i["guid"])
            obj.name = i["name"]

            # some fields
            obj.properties["latest_educational_qualification"] = core.mtypes.getRandomSourceValue("researcher.latest_educational_qualification")
            obj.properties["education_level"] = core.mtypes.getRandomSourceValue("researcher.education_level")
            obj.properties["subject_fields"] = f"Subjects of {obj.name}"

            obj.save()

        # create subjects
        for i in self.tst_subjects:
            obj = core.data.new("subject", guid=i["guid"])
            obj.name = i["name"]

            # some fields
            obj.properties["human.education_level"] = core.mtypes.getRandomSourceValue("subject.education_level")

            obj.save()

        # create 1 lab
        obj = core.data.new("lab", guid=self.labguid)
        obj.name = "Test Lab"
        obj.description = "Original Lab Description"
        obj.properties["official_name"] = "Test suite lab"
        obj.save()

        # create 1 project
        obj = core.data.new("project", guid=self.projectguid)
        obj.name = "Test Project"
        obj.description = "Original Project Description"
        obj.save()

    def test_retrieveRecords(self):
        for i in self.tst_researchers:
            obj = core.data.findByGuid(i["guid"])
            self.assertEqual(obj.name, i["name"])

    def test_alterRecords(self):
        lab = core.data.findByGuid(self.labguid)
        lab.description = "Changed Lab Description"
        lab.properties["official_name"] = "Test suite lab (changed)"
        lab.save()
        lab = core.data.findByGuid(self.labguid)
        self.assertEqual(lab.description, "Changed Lab Description")

    def test_links(self):
        # add links to lab
        lab = core.data.findByGuid(self.labguid)
        props = {
            "position": core.mtypes.getRandomSourceValue("lab.position"),
            "date_joined": datetime.now(),
            "is_active": "yes"
        }
        for i in self.tst_researchers:
            lab.addLink("members", i["guid"], props)
        lab.save()

        # add links to project
        proj = core.data.findByGuid(self.projectguid)
        for i in self.tst_researchers:
            proj.addLink("members", i["guid"])

        for i in self.tst_subjects:
            proj.addLink("subjects", i["guid"])

        proj.addLink("labs", self.labguid)
        proj.save()

        # retrieve record after save and check for links
        lab = core.data.findByGuid(self.labguid)
        self.assertEqual(len(lab.properties["members"]), 5)

        idx = 0
        for i in lab.properties["members"]:
            l = core.data.getLinksTo(i["to"])
            # 2 links, 1 to lab and 1 to project
            self.assertEqual(len(l), 2, "Invalid link count")
            if len(l) == 2:
                self.assertEqual(l[0]["to"], self.tst_researchers[idx]["guid"], "Member / lab linked guid do not match")
            idx += 1

    def test_api(self):
        pass

    def test_deleteRecords(self):
        lst = copy.deepcopy(core.data.data)
        ok = True
        for i in lst:
            if not core.data.deleteByGuid(i):
                print("Guid not found for deletion:", i)
                ok = False
                break

        self.assertEqual(ok, True, "Error deleting objects")
        pass


if core.envvar("ALLOW_TESTS") != "1":
    print("Testing is disabled")
    exit()

load_tests = load_ordered_tests
unittest.main()
'''
move repos to genemede

define questions for beta testing
basic documentation for ui functions

'''
