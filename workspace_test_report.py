from datetime import datetime
import json
import time
from wflow_class import wflow
from firecloud import api

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

def run_workflow_submission(clone_project, clone_name, sleep_time=100):
    """ note: default sleep time is 100 seconds
    """

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
        project = item["namespace"]     # billing project
        name = item["name"]             # the name of the workflow
        workflow_names.append(name)     # will be deleted soon

        """question for Alex: is this next section necessary 
        or can we just set entityName to None if entityType is None? 
        if entityType is None, can entityName ever not be None?
        """
        entities = api.get_entities(clone_project, clone_name, entityType)
        entityName = None
        if len(entities.json()) != 0:
            entityName = entities.json()[0]["name"]
        
        # create a submission to run for this workflow
        ret = api.create_submission(clone_project, clone_name, project, name, entityName, entityType)
        if ret.status_code != 201: # check for errors
            print(ret.text)
            exit(1)

    # wait for the submission to finish (i.e. submission status is Done or Aborted)
    breakOut = False        # flag for being done
    count = 0               # count how many submissions are done; to check if all are done
    finish_workflows = []   # will be a list of finished workflows
    finish_workflows_details = []
    terminal_states = set(["Done", "Aborted"])

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




def generate_workflow_report(project, workspace):
    """ this will generate a failure/success report for each workflow in a workspace, 
    only running on the most recent submission for each report.
    """
    workflow_dict = {} # this will collect all workflows, each of which contains entity_dict of entities for that workflow
    res = api.list_submissions(project, workspace)
    res = res.json()

    count = 0
    Failed = False

    for item in res:
        # each item in res corresponds with a submission that may contain multiple workflows and entities
        wf_name = item["methodConfigurationName"]
        submission_id = item["submissionId"]
        print("getting status and info for "+wf_name+" in submission "+submission_id)

        sub_dict = {} # this will collect wflow classes for all entities for this workflow

        FailedMess = []

        for i in api.get_submission(project, workspace, submission_id).json()["workflows"]:
            # each i in here corresponds with a single workflow with a given entity
            

            if "workflowEntity" in i:
                entity_name = i["workflowEntity"]["entityName"]
            else:
                entity_name = None

            if "workflowId" in i:
                wfid = i["workflowId"]
                key = wfid

                resworkspace = api.get_workflow_metadata(project, workspace, submission_id, wfid).json()
                mess_details = None
                wf_status = resworkspace["status"]
                if wf_status == "Failed":
                    for failed in resworkspace["failures"]:
                        for message in failed["causedBy"]:
                            mess_details = str(message["message"])
                            Failed = True
                # TODO: find whether it's possible to Abort but still have a workflow ID? if so, need to adjust this
                
            else:
                count +=1
                wfid = None
                key = "no_wfid_"+str(count)

                if i["status"] == "Failed":
                    wf_status = "Failed"
                    mess_details = "No Workflow ID"
                    Failed = True
                elif i["status"] == "Aborted":
                    wf_status = "Aborted"
                    mess_details = "Aborted"
                    Failed = True
            
            sub_dict[key]=wflow(workspace=workspace,
                                project=project,
                                wfid=wfid, 
                                subid=submission_id,
                                wfname=wf_name, 
                                entity=entity_name, 
                                status=wf_status, 
                                message=mess_details)

        workflow_dict[wf_name] = sub_dict

    if Failed:
        status_text = "FAILURE!"
        status_color = "red"
    else:
        status_text = "SUCCESS!"
        status_color = "green"

    # make a list of the workflows
    workflows_list = list(workflow_dict.keys())
    print(workflows_list)

    # make a list of the notebooks
    notebooks_list = ["No notebooks tested"]

    # generate detail text from workflows
    html_text = ""
    for wf in workflow_dict.keys():
        wf_name = wf
        html_text += "<h3>"+wf_name+"</h3>"
        html_text += "<blockquote>"
        sub_dict = workflow_dict[wf]
        for sub in sub_dict.values():
            html_text += sub.get_HTML()
        html_text += "</blockquote>"

    html_output = "/tmp/hello.html" #TODO make this nice

    f = open(html_output,'w')

    message = """<html>
    <head><link href='https://fonts.googleapis.com/css?family=Lato' rel='stylesheet'>
    </head>
    <body style="font-family:'Lato'; font-size:18px; padding:30; background-color:#FAFBFD">
    <p>
    <center><div style="background-color:#82AA52; color:#FAFBFD; height:100px">
    <h1>
    <img src="https://app.terra.bio/static/media/logo-wShadow.c7059479.svg" alt="Terra rocks!" style="vertical-align: middle;" height="100">
    <span style="vertical-align: middle;">
    Terra's Featured Workspace Report</span></h1>

    <h1><font color={status_color}>{status_text}</font></h1></center> <br><br>
    
    <br><br><big><b> Feature Workspace: </b>""" + workspace + """ </big>
    <br><br><big><b> Feature Billing Project: </b>""" + project + """ </big>
    <br><br><big><b> Workflows Tested: </b>""" + ", ".join(workflows_list) + """ </big>
    <br><br><big><b> Notebooks Tested: </b>""" + ", ".join(notebooks_list) + """ </big>
    <br>
    <h2>Workflows:</h2>
    <blockquote> """ + html_text + """ </blockquote>
    
    
    </p>

    </p></body>
    </html>"""

    message = message.format(status_color = status_color,
                            status_text = status_text)
    f.write(message)
    f.close()

    return html_output

