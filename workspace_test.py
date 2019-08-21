from firecloud import api
from datetime import datetime
import pprint
import json
import time

clone_project = "featured-workspace-testing"
clone_name = "Germline-SNPs-Indels-GATK4-hg38" +'_' + datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
res = api.clone_workspace("help-gatk",
                          "Sequence-Format-Conversion",
                          clone_project,
                          clone_name,
                        )

if res.status_code != 201:
    print("Not Cloning")
    print(res.text)
    exit(1)

res = api.list_workspace_configs(clone_project, clone_name, allRepos = True)
if res.status_code != 200:
    print(res.text)
    exit(1)

res = res.json()

for item in res:
    entityType = None
    if "rootEntityType" in item:
        entityType = item["rootEntityType"]
    namespace = item["namespace"]
    name = item["name"]
    entities = api.get_entities(clone_project, clone_name, entityType)
    entityName = None
    if len(entities.json()) != 0:
        entityName = entities.json()[0]["name"]
    ret = api.create_submission(clone_project, clone_name, namespace, name, entityName, entityType)
    if ret.status_code != 201:
        print(ret.text)
        exit(1)

breakOut = False
while not breakOut:
    res = api.list_submissions(clone_project, clone_name)
    res = res.json()
    terminal_states = set(["Succeeded", "Aborted", "Failed"])
    for item in res:
        if item["status"] in terminal_states:
           breakOut = True
    pprint.pprint(res)
    time.sleep(100)



