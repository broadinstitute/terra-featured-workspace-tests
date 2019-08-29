"""
Workspace_test.py is designed to clone and run Featured Workspaces,
Afterwards, the program generates an HTML report of failures and successes,
with links to their Workflow report(s) on Terra.bio
"""

from firecloud import api
from datetime import datetime
import json
import time

# Define project, workspace to test, and cloned workspace name
clone_project = "featured-workspace-testing"                    # billing project
original_name = "Sequence-Format-Conversion"                    # the workspace to test
clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')     # time of clone
clone_name = original_name +'_' + clone_time                    # cloned name is the original name + current date/time
error_message = ""                                              # will be filled if there's an error

# Clone the Featured Workspace
res = api.clone_workspace("help-gatk",
                          original_name,
                          clone_project,
                          clone_name,
                        )

# Catch if the Featured Workspace didn't clone
if res.status_code != 201:
    error_message = "Not Cloning"
    print("Not Cloning")
    print(res.text)
    exit(1)

# Get a list of workflows in the project
res = api.list_workspace_configs(clone_project, clone_name, allRepos = True)
# Catch if the cloned feature workspace had an error with loading
if res.status_code != 200:
    error_message = res.text
    print(res.text)
    exit(1)

# If cloning was successful, run through the workspace and create a submission for each workflow
res = res.json()    # convert to json
workflow_names = [] # store the names of the workflows
for item in res:  # for each item (workflow)
    
    # identify the type of data being used by this workflow
    if "rootEntityType" in item:
        entityType = item["rootEntityType"]
    else:
        entityType = None
    namespace = item["namespace"]   # billing project
    name = item["name"]             # the name of the workflow
    workflow_names.append(name) # will be deleted soon

    """question for Alex: is this next section necessary 
    or can we just set entityName to None if entityType is None? 
    if entityType is None, can entityName ever not be None?
    """
    entities = api.get_entities(clone_project, clone_name, entityType)
    entityName = None
    if len(entities.json()) != 0:
        entityName = entities.json()[0]["name"]
    
    # create a submission to run for this workflow
    ret = api.create_submission(clone_project, clone_name, namespace, name, entityName, entityType)
    if ret.status_code != 201: # check for errors
        print(ret.text)
        exit(1)

# wait for the submission to finish (i.e. submission status is Done or Aborted)
breakOut = False        # flag for being done
count = 0               # count how many submissions are done; to check if all are done
finish_workflows = []   # will be a list of finished workflows
finish_workflows_details = []
terminal_states = set(["Done", "Aborted"])
# TODO: handle Aborted workflows
sleep_time = 100 # seconds to sleep between loops

while not breakOut:
    # get the current list of submissions and their statuses
    res = api.list_submissions(clone_project, clone_name).json()
    
    for item in res: # for each workflow
        if item["status"] in terminal_states: # if the workflow status is Done or Aborted
            count += 1
            if item["methodConfigurationName"] not in finish_workflows:
                details = str(item["methodConfigurationName"]) + " finished on "+ datetime.today().strftime('%m/%d/%Y at %H:%M')
                finish_workflows.append(item["methodConfigurationName"])
                finish_workflows_details.append(details)
        if count == len(res): # if all workflows are done, you're done!
            breakOut = True
            sleep_time = 0.5
    
    print(datetime.today().strftime('%H:%M')+ " - finished workflows:" + str(finish_workflows)) # just a sanity check / progress meter
    # if not all workflows are done yet, reset the count and wait 100 seconds
    count = 0 
    time.sleep(sleep_time)

# TODO: add test.py things
methodNamesstr = ', '.join(workflow_names)
detailstr = "<br>".join(finish_workflows_details)
print(', '.join(workflow_names) + " all ran successfully!")

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

message = message.format(Feature_Workspace = original_name, 
                         Workflows = methodNamesstr, 
                         Project = clone_project, 
                         Clone_Workspace = clone_name, 
                         Details = detailstr)
f.write(message)
f.close()

