from datetime import datetime
from firecloud import api
import json
import time
from wflow_class import wflow


def clone_workspace(original_project, original_name, clone_project):
    """ clone a given workspace
    """
 
    # define the name of the cloned workspace
    clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')     # time of clone
    clone_name = original_name +'_' + clone_time                    # cloned name is the original name + current date/time
    error_message = ""                                              # will be filled if there's an error

    # Clone the Featured Workspace
    res = api.clone_workspace(original_project,
                            original_name,
                            clone_project,
                            clone_name,
                            )

    # Catch if the Featured Workspace didn't clone
    if res.status_code != 201:
        error_message = "Not Cloning"
        print(error_message)
        print(res.text)
        exit(1)

    return clone_name

def run_workflow_submission(clone_project, clone_name):

    # Get a list of workflows in the project
    res = api.list_workspace_configs(clone_project, clone_name, allRepos = True)
    # Catch if the cloned feature workspace had an error with loading
    if res.status_code != 200:
        error_message = res.text
        print(error_message)
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




def generate_workflow_report(namespace, workspace):

    res = api.list_submissions(namespace, workspace)
    res = res.json()
    for item in res:
        count = 0
        Failed = False
        FailedMess = []
        Link = []
        for i in api.get_submission(namespace, workspace, item["submissionId"]).json()["workflows"]:
            count +=1
            if "workflowId" in i: 
                Link.append(str(count) + ". " + "https://job-manager.dsde-prod.broadinstitute.org/jobs/"+ str(i["workflowId"]))
                resworkspace = api.get_workflow_metadata(namespace, workspace, item["submissionId"], i["workflowId"]).json()
                if resworkspace["status"] == "Failed":
                    for failed in resworkspace["failures"]:
                        for message in failed["causedBy"]:
                            if str(message["message"]) not in FailedMess:
                                FailedMess.append(str(count) + ". " + str(message["message"]))
                            Failed = True
            else:
                if i["status"] == "Failed":
                    print(item["submissionId"])
                    if "No Workflow Id" not in FailedMess:
                        FailedMess.append("No Workflow Id")
                    Failed = True  
        
        print("End Results:")
        if Failed:
            print(str(item["methodConfigurationName"]) + " has failed. The error message is: \n \n -"  + "\n \n -".join(FailedMess))
            print("\n \n List of Links: - ")
            print("\n-".join(Link))
        else:
            print(str(item["methodConfigurationName"]) + " has run successfully.")
            print("\n \n List of Links: - ")
            print("\n-".join(Link))
        print("\n \n \n ")


    if Failed:
        status_text = "FAILURE!"
        status_color = "red"
    else:
        status_text = "SUCCESS!"
        status_color = "green"

    K =  datetime.today().strftime('%H:%M-%m/%d/%Y') + "<br>"

    f = open('hello.html','w')

    message = """<html>
    <head></head>
    <body><p><center><h1>Terra's Feature Workspace Report</h1>
    <h1><font color={status_color}>{status_text}</font></h1></center> 
    <br><br>

    Name for Feature Workspace:
    <br><br> The Workflows Tested:
    <br><br> The Notebooks Tested:

    <br><br> {Ka} Cloning Workspace to:
    <br><br> {Ka} Running:
    <br><br> {Ka} ________ are all completed.
    <br> Everything ran successfully!</p></body>
    </html>"""

    message = message.format(Ka = K, 
                            status_color = status_color,
                            status_text = status_text)
    f.write(message)
    f.close()


