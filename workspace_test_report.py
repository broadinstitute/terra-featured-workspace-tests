from datetime import datetime
import json
import time
from wflow_class import wflow
from firecloud import api

def clone_workspace(original_project, original_name, clone_project):
    """ clone a given workspace
    """
    print("cloning " + original_name)

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
        error_message = "Cloning failed"
        print(error_message)
        print(res.text)
        exit(1)

    return clone_name

def run_workflow_submission(project, workspace, sleep_time=100):
    """ note: default sleep time (time to wait between checking whether 
    the submissions have finished) is 100 seconds
    """
    print("running workflow submission on "+workspace)

    # Get a list of workflows in the project
    res = api.list_workspace_configs(project, workspace, allRepos = True)

    # Catch if the cloned feature workspace had an error with loading
    if res.status_code != 200:
        print(res.text)
        exit(1)

    # run through the workspace and create a submission for each workflow
    res = res.json()    # convert to json
    for item in res:  # for each item (workflow)
        
        # identify the type of data (entity) being used by this workflow, if any
        if "rootEntityType" in item:
            entityType = item["rootEntityType"]
        else:
            entityType = None
        project_orig = item["namespace"]     # original billing project
        name_orig = item["name"]             # the name of the original workflow

        # get and store the name of the data (entity) being used, if any
        entities = api.get_entities(project, workspace, entityType)
        entityName = None
        if len(entities.json()) != 0:
            entityName = entities.json()[0]["name"]

        # create a submission to run for this workflow
        ret = api.create_submission(project, workspace, project_orig, name_orig, entityName, entityType)
        if ret.status_code != 201: # check for errors
            print(ret.text)
            exit(1)

    # wait for the submission to finish (i.e. submission status is Done or Aborted)
    break_out = False       # flag for being done
    count = 0               # count how many submissions are done; to check if all are done
    finish_workflows = []   # will be a list of finished workflows
    finish_workflows_details = []
    terminal_states = set(["Done", "Aborted"])

    while not break_out:
        # get the current list of submissions and their statuses
        res = api.list_submissions(project, workspace).json()
        
        for item in res: # for each workflow
            if item["status"] in terminal_states: # if the workflow status is Done or Aborted
                count += 1
                if item["methodConfigurationName"] not in finish_workflows:
                    details = str(item["methodConfigurationName"]) + " finished on "+ datetime.today().strftime('%m/%d/%Y at %H:%M')
                    finish_workflows.append(item["methodConfigurationName"])
                    finish_workflows_details.append(details)
            if count == len(res): # if all workflows are done, you're done!
                break_out = True
                sleep_time = 0
        
        # print progress
        print(datetime.today().strftime('%H:%M')+ " - finished " + str(count) + " of " + str(len(res)) + " workflows:" + str(finish_workflows))
        
        # if not all workflows are done yet, reset the count and wait sleep_time seconds to check again
        count = 0 
        time.sleep(sleep_time)

def run_notebook_submission(project, workspace, sleep_time=100):
    """ note: default sleep time (time to wait between checking whether 
    the submissions have finished) is 100 seconds
    """

    print("running notebook submission on "+workspace)
    print("note: this does nothing with notebooks yet.")

    # get a list of notebooks in the project
    # run each notebook
    # figure out when it's done

def generate_workspace_report(project, workspace, html_output="/tmp/workspace_report.html"):
    """ generate a failure/success report for each workflow in a workspace, 
    only reporting on the most recent submission for each report.
    this returns a string html_output that's currently not modified by this function but might be in future!
    """
    print("generating workspace report for "+workspace)

    workflow_dict = {} # this will collect all workflows, each of which contains sub_dict of submissions for that workflow
    res = api.list_submissions(project, workspace)
    res = res.json()

    count = 0
    Failed = False

    for item in res:
        # each item in res corresponds with a submission for one workflow that may contain multiple entities
        wf_name = item["methodConfigurationName"]
        submission_id = item["submissionId"]
        print("getting status and info for "+wf_name+" in submission "+submission_id)

        sub_dict = {} # this will collect wflow classes for all workflows within this submission (may be multiple if the workflow was run on multiple entities)

        FailedMess = []

        for i in api.get_submission(project, workspace, submission_id).json()["workflows"]:
            # each i in here corresponds with a single workflow with a given entity
            
            # if this workflow has an entity, store its name
            if "workflowEntity" in i:
                entity_name = i["workflowEntity"]["entityName"]
            else:
                entity_name = None

            # if the workflow has a workflowId, meaning the submission completed, then get and store it
            if "workflowId" in i:
                wfid = i["workflowId"]
                key = wfid                  # use the workflowId as the key for the dictionary

                # get more details from the workflow: status, error message
                resworkspace = api.get_workflow_metadata(project, workspace, submission_id, wfid).json()
                mess_details = None
                wf_status = resworkspace["status"]

                # in case of failure, pull out the error message
                if wf_status == "Failed":
                    for failed in resworkspace["failures"]:
                        for message in failed["causedBy"]:
                            mess_details = str(message["message"])
                            Failed = True
                elif wf_status == "Aborted":
                    mess_details = "Aborted"
                    Failed = True
                
            else: # if no workflowId
                count +=1                       # count of workflows with no workflowId
                wfid = None                     # store the wfid as None, since there is none
                key = "no_wfid_"+str(count)     # create a key to use in the dict

                if i["status"] == "Failed":
                    wf_status = "Failed"
                    # get the error message for why it failed
                    mess_details = str(i["messages"])[1:-1]
                    Failed = True
                elif i["status"] == "Aborted":
                    wf_status = "Aborted"
                    mess_details = "Aborted"
                    Failed = True
                else: # should probably never get here, but just in case
                    wf_status = i["status"]
                    mess_dtails = "unrecognized status"
                    Failed = True
            
            # store all this information in the dictionary containing workflow classes
            sub_dict[key]=wflow(workspace=workspace,
                                project=project,
                                wfid=wfid, 
                                subid=submission_id,
                                wfname=wf_name, 
                                entity=entity_name, 
                                status=wf_status, 
                                message=mess_details)

        workflow_dict[wf_name] = sub_dict



    ### the rest of this function sets up the html report
    # probably TODO: make the report its own function
    
    # if there were ANY failures
    if Failed:
        status_text = "FAILURE!"
        status_color = "red"
    else:
        status_text = "SUCCESS!"
        status_color = "green"

    # make a list of the workflows
    workflows_list = list(workflow_dict.keys())

    # make a list of the notebooks
    notebooks_list = ["No notebooks tested"]

    # generate detail text from workflows
    workflows_text = ""
    for wf in workflow_dict.keys():
        wf_name = wf
        workflows_text += "<h3>"+wf_name+"</h3>"
        workflows_text += "<blockquote>"
        sub_dict = workflow_dict[wf]
        for sub in sub_dict.values():
            workflows_text += sub.get_HTML()
        workflows_text += "</blockquote>"
    
    # generate detail text from notebooks
    notebooks_text = ""

    # open, generate, and write the html text for the report
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
    Featured Workspace Report</span></h1>

    <h1><font color={status_color}>{status_text}</font></h1></center> <br><br>
    
    <br><br><big><b> Featured Workspace: </b>""" + workspace + """ </big>
    <br><big><b> Billing Project: </b>""" + project + """ </big>
    <br><br><big><b> Workflows Tested: </b>""" + ", ".join(workflows_list) + """ </big>
    <br><big><b> Notebooks Tested: </b>""" + ", ".join(notebooks_list) + """ </big>
    <br>
    <h2>Workflows:</h2>
    <blockquote> """ + workflows_text + """ </blockquote>
    <br>
    <h2>Notebooks:</h2>
    <blockquote> """ + notebooks_text + """ </blockquote>
    </p>

    </p></body>
    </html>"""

    message = message.format(status_color = status_color,
                            status_text = status_text)
    f.write(message)
    f.close()

    return html_output

