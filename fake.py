import sys
from faker import Faker
from src import core
from datetime import datetime

if core.envvar("ALLOW_FAKER") != "1":
    print("Faker is disabled")
    exit()

fake = Faker()

def fillData(res):
    status = False
    if res.mtype.startswith("lab"):
        res.name = fake.company()
        res.description = fake.catch_phrase()
        res.properties["official_name"] = res.name
        res.properties["contact_phone"] = fake.phone_number()
        res.properties["contact_email"] = fake.email()
        res.properties["contact_website"] = fake.hostname(3)
        res.properties["contact_address"] = fake.address()
        status = True

    elif res.mtype.startswith("project"):
        res.name = fake.company()
        res.description = fake.catch_phrase()
        res.properties["project_lead"] = fake.name()
        res.properties["project_manager"] = fake.name()
        res.properties["data_manager"] = fake.name()
        status = True

    elif res.mtype.startswith("subject"):
        res.properties["creator"] = fake.name()
        res.name = res.properties["creator"]

    elif res.mtype.startswith("researcher"):
        res.description = fake.catch_phrase()
        d = datetime.now()
        res.properties["date_joined"] = d.isoformat()
        res.properties["first_name"] = fake.first_name()
        res.properties["last_name"] = fake.last_name()
        res.properties["contact_phone"] = fake.phone_number()
        res.properties["contact_email"] = fake.email()
        res.properties["contact_website"] = fake.hostname(3)
        res.properties["contact_address"] = fake.address()
        res.properties["position"] = fake.job()

        res.name = res.properties["first_name"] + " " + res.properties["last_name"]
        status = True

    return status

# create researchers
researchers = []
for i in range(1, 50):
    rs = core.mdata.new("researcher")
    fillData(rs)
    researchers.append(rs)
    rs.save()

# create a lab
lab = core.mdata.new("lab")
fillData(lab)
lab.properties["test"] = [{"a": 123}, {"b": 456}]
lab.save()

labGuid = lab.guid

# create some projects
for i in range(1, 5):
    proj = core.mdata.new("project")
    fillData(proj)
    proj.properties["labs"] = [{"guid": labGuid}]
    proj.save()


