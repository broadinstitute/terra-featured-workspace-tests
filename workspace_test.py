# Workspace_test.py is design to clone and run feature workspaces,
# Afterwards, the program will generate a HTML report of failures and successes,
# with linkes to their Workflow report on Terra.bio

from firecloud import api
from datetime import datetime
import pprint
import json
import time

# The names of where the the project and workspace, The feature workspace is being clone to this:
clone_project = "featured-workspace-testing"
clone_name = "Sequence-Format-Conversion" +'_' + datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
Orginal_name = "Sequence-Format-Conversion"
Error_message = ""

# Cloning the feature workspace
res = api.clone_workspace("help-gatk",
                          "Sequence-Format-Conversion",
                          clone_project,
                          clone_name,
                        )

#Catches if the feature workspace didn't clone
if res.status_code != 201:
    Error_message = "Not Cloning"
    print("Not Cloning")
    print(res.text)
    exit(1)

#Catches if the cloned feature workspace had an error with loading
res = api.list_workspace_configs(clone_project, clone_name, allRepos = True)
if res.status_code != 200:
    Error_message = res.text
    print(res.text)
    exit(1)

#if cloning was successful, the program runs through the workspace and create a submission for each workflow
res = res.json()
workflow_names = []
for item in res:
    entityType = None
    if "rootEntityType" in item:
        entityType = item["rootEntityType"]
    namespace = item["namespace"]
    name = item["name"]
    workflow_names.append(name)
    entities = api.get_entities(clone_project, clone_name, entityType)
    entityName = None
    if len(entities.json()) != 0:
        entityName = entities.json()[0]["name"]
    ret = api.create_submission(clone_project, clone_name, namespace, name, entityName, entityType)
    if ret.status_code != 201:
        print(ret.text)
        exit(1)

breakOut = False
count = 0
finish_workflows = []
finish_workflows_details = []
while not breakOut:
    res = api.list_submissions(clone_project, clone_name)
    res = res.json()
    terminal_states = set(["Done", "Aborted", "Failed"])
    for item in res:
        if item["status"] in terminal_states:
            count += 1
            if item["methodConfigurationName"] not in finish_workflows:
                details = str(item["methodConfigurationName"]) + " is finish at "+ datetime.today().strftime('%H:%M-%m/%d/%Y')
                finish_workflows.append(item["methodConfigurationName"])
                finish_workflows_details.append(details)
        if count == len(res):
            breakOut = True
    count = 0
    time.sleep(100)
methodNamesstr = ', '.join(workflow_names)
detailstr = "<br>".join(finish_workflows_details)
print ', '.join(workflow_names) + " all ran successfully!"

f = open('TerraFeatureWorkspaceReport.html','w')

message = """<html>
<head></head>
<body><p><center>Terra's Feature Workspace Report</center> <br>
<br>

Name for Feature Workspace: {Feature_Workspace}
<br><br> The Workflows Tested: {Workflows}
<br><br> The Notebooks Tested: 0
<br><br> Testing Project Name: {Project}
<br><br> Cloning Workspace to: {Clone_Workspace}
<br><br> Running: {Workflows}
<br><br> Details:
<br>{Details}
<br><br>Everything ran successfully!</p></body>
</html>"""

message = message.format(Feature_Workspace = Orginal_name, Workflows = methodNamesstr, Project = clone_project, Clone_Workspace = clone_name, Details = detailstr)
f.write(message)
f.close()

