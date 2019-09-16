from datetime import datetime
import json
import time
from wflow_class import wflow
from firecloud import api as fapi
import subprocess
# import pprint



def clone_workspace(original_project, original_name, clone_project, verbose=False):
    ''' clone a given workspace
    '''
    if verbose:
        print('cloning ' + original_name)

    # define the name of the cloned workspace
    clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')     # time of clone
    clone_name = original_name +'_' + clone_time                    # cloned name is the original name + current date/time
    error_message = ''                                              # will be filled if there's an error

    # Clone the Featured Workspace
    res = fapi.clone_workspace(original_project,
                            original_name,
                            clone_project,
                            clone_name,
                            )

    # Catch if the Featured Workspace didn't clone
    if res.status_code != 201:
        error_message = 'Cloning failed'
        print(error_message)
        print(res.text)
        exit(1)
    #Original Bucket    
    r = fapi.get_workspace(original_project, original_name)
    fapi._check_response_code(r, 200)
    workspace = r.json()
    original_bucket = workspace['workspace']['bucketName']

    #Clone Bucket    
    r = fapi.get_workspace(clone_project, clone_name)
    fapi._check_response_code(r, 200)
    workspace = r.json()
    clone_bucket = workspace['workspace']['bucketName']
    
    gsutil_args = ['gsutil', 'cp', 'gs://' + original_bucket + '/notebooks/**', 'gs://' + clone_bucket + '/notebooks/']

    bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
    # Check output produces a string in Py2, Bytes in Py3, so decode if necessary
    if type(bucket_files) == bytes:
        bucket_files = bucket_files.decode().split('\n')
    if verbose:
        print("Notebooks copied")

    return clone_name

def run_workflow_submission(project, workspace, sleep_time=100, do_order=False, verbose=False):
    ''' note: default sleep time (time to wait between checking whether 
    the submissions have finished) is 100 seconds
    '''
    if verbose:
        print('running workflow submissions on '+workspace)
    
    # # for troubleshooting
    # pp = pprint.PrettyPrinter(indent=4)
    
    # terminal states
    terminal_states = set(['Done', 'Aborted'])

    # Get a list of workflows in the project
    res = fapi.list_workspace_configs(project, workspace, allRepos = True)

    # Catch if the cloned feature workspace had an error with loading
    if res.status_code != 200:
        print(res.text)
        exit(1)

    # run through the workflows and get information to create submissions for each workflow
    submissions = {}    # dict to store info about submissions
    res = res.json()    # convert to json
    for item in res:  # for each item (workflow)
        
        # identify the type of data (entity) being used by this workflow, if any
        if 'rootEntityType' in item:
            entityType = item['rootEntityType']
        else:
            entityType = None
        project_orig = item['namespace']    # original billing project
        wf_name = item['name']              # the name of the workflow

        # get and store the name of the data (entity) being used, if any
        entities = fapi.get_entities(project, workspace, entityType)
        entityName = None
        if len(entities.json()) != 0:
            entityName = entities.json()[0]['name']

        # create dictionary of inputs for fapi.create_submission - TODO: this could be a class?
        submission_input = {'project':project,
                            'workspace':workspace,
                            'project_orig':project_orig,
                            'wf_name':wf_name,
                            'entity_name':entityName,
                            'entity_type':entityType}
        submissions[wf_name] = submission_input

    workflow_names = list(submissions.keys())
    workflow_names.sort()

    for wf_name in workflow_names:
        wf = submissions[wf_name]

        # create a submission to run for this workflow
        ret = fapi.create_submission(wf['project'], 
                                    wf['workspace'], 
                                    wf['project_orig'], 
                                    wf['wf_name'], 
                                    wf['entity_name'], 
                                    wf['entity_type'])

        if verbose:
            print('submitted '+wf_name)

        if ret.status_code != 201: # check for errors
            print(ret.text)
            exit(1)

        # if the workflows must be run sequentially, wait for each to finish
        if do_order:
            ret = ret.json()
            submissionId = ret['submissionId']
            
            break_out = False
            while not break_out:
                sub_res = fapi.get_submission(project, workspace, submissionId).json()
                submission_status = sub_res['status']
                if verbose:
                    print(' ' +datetime.today().strftime('%H:%M')+ ' status: '+ submission_status)
                if submission_status in terminal_states:
                    break_out = True
                else:
                    time.sleep(sleep_time)


    # wait for the submission to finish (i.e. submission status is Done or Aborted)
    break_out = False       # flag for being done
    count = 0               # count how many submissions are done; to check if all are done
    finish_workflows = []   # will be a list of finished workflows
    finish_workflows_details = []

    while not break_out:
        # get the current list of submissions and their statuses
        res = fapi.list_submissions(project, workspace).json()
        
        for item in res: # for each workflow
            if item['status'] in terminal_states: # if the workflow status is Done or Aborted
                count += 1
                if item['methodConfigurationName'] not in finish_workflows:
                    details = str(item['methodConfigurationName']) + ' finished on '+ datetime.today().strftime('%m/%d/%Y at %H:%M')
                    finish_workflows.append(item['methodConfigurationName'])
                    finish_workflows_details.append(details)
            if count == len(res): # if all workflows are done, you're done!
                break_out = True
                sleep_time = 0
        
        if verbose:
            # print progress
            print(datetime.today().strftime('%H:%M')+ ' - finished ' + str(count) + ' of ' + str(len(res)) + ' workflows:' + str(finish_workflows))
        
        # if not all workflows are done yet, reset the count and wait sleep_time seconds to check again
        count = 0 
        time.sleep(sleep_time)

def get_notebook(project, workspace, verbose=False):
    '''
        Geting the list of notebooks in the workspace
    '''
    res = fapi.get_workspace(project, workspace)
    fapi._check_response_code(res, 200)
    workspace = res.json()
    bucket = workspace['workspace']['bucketName']

    # # Now run a gsutil ls to list files present in the bucket
    gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/**']
    bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
    # Check output produces a string in Py2, Bytes in Py3, so decode if necessary
    if type(bucket_files) == bytes:
        bucket_files = bucket_files.decode().split('\n')
    notebook_files = []

    for f in bucket_files:
        if 'notebook' in f:
            f = f.split('/')[-1]
            notebook_files.append(f)
    if verbose:
        if len(notebook_files) == 0:
            print('Workspace has no notebooks')
        else: 
            print('\n'.join(notebook_files))
    return notebook_files

def generate_workspace_report(project, workspace, html_output='/tmp/workspace_report.html', verbose=False):
    ''' generate a failure/success report for each workflow in a workspace, 
    only reporting on the most recent submission for each report.
    this returns a string html_output that's currently not modified by this function but might be in future!
    '''
    if verbose:
        print('generating workspace report for '+workspace)

    workflow_dict = {} # this will collect all workflows, each of which contains sub_dict of submissions for that workflow
    res = fapi.list_submissions(project, workspace)
    if res.status_code != 200:
        print(res.text)
        exit(1)

    res = res.json()

    count = 0
    Failed = False

    for item in res:
        # each item in res corresponds with a submission for one workflow that may contain multiple entities
        wf_name = item['methodConfigurationName']
        submission_id = item['submissionId']
        if verbose:
            print('getting status and info for '+wf_name+' in submission '+submission_id)

        sub_dict = {} # this will collect wflow classes for all workflows within this submission (may be multiple if the workflow was run on multiple entities)

        FailedMess = []

        for i in fapi.get_submission(project, workspace, submission_id).json()['workflows']:
            # each i in here corresponds with a single workflow with a given entity
            
            # if this workflow has an entity, store its name
            if 'workflowEntity' in i:
                entity_name = i['workflowEntity']['entityName']
            else:
                entity_name = None

            # if the workflow has a workflowId, meaning the submission completed, then get and store it
            if 'workflowId' in i:
                wfid = i['workflowId']
                key = wfid                  # use the workflowId as the key for the dictionary

                # get more details from the workflow: status, error message
                resworkspace = fapi.get_workflow_metadata(project, workspace, submission_id, wfid).json()
                mess_details = None
                wf_status = resworkspace['status']

                # in case of failure, pull out the error message
                if wf_status == 'Failed':
                    for failed in resworkspace['failures']:
                        for message in failed['causedBy']:
                            mess_details = str(message['message'])
                            Failed = True
                elif wf_status == 'Aborted':
                    mess_details = 'Aborted'
                    Failed = True
                
            else: # if no workflowId
                count +=1                       # count of workflows with no workflowId
                wfid = None                     # store the wfid as None, since there is none
                key = 'no_wfid_'+str(count)     # create a key to use in the dict

                if i['status'] == 'Failed':
                    wf_status = 'Failed'
                    # get the error message for why it failed
                    mess_details = str(i['messages'])[1:-1]
                    Failed = True
                elif i['status'] == 'Aborted':
                    wf_status = 'Aborted'
                    mess_details = 'Aborted'
                    Failed = True
                else: # should probably never get here, but just in case
                    wf_status = i['status']
                    mess_dtails = 'unrecognized status'
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
        status_text = 'FAILURE!'
        status_color = 'red'
    else:
        status_text = 'SUCCESS!'
        status_color = 'green'

    # make a list of the workflows
    workflows_list = list(workflow_dict.keys())

    # make a list of the notebooks
    notebooks_list = get_notebook(project, workspace)
    if len(notebooks_list) == 0:
        notebooks_list = ["No notebooks in workspace"]
    
    # generate detail text from workflows
    workflows_text = ''
    for wf in workflow_dict.keys():
        wf_name = wf
        workflows_text += '<h3>'+wf_name+'</h3>'
        workflows_text += '<blockquote>'
        sub_dict = workflow_dict[wf]
        for sub in sub_dict.values():
            workflows_text += sub.get_HTML()
        workflows_text += '</blockquote>'
    
    # generate detail text from notebooks
    notebooks_text = ''

    # open, generate, and write the html text for the report
    f = open(html_output,'w')
    message = '''<html>
    <head><link href='https://fonts.googleapis.com/css?family=Lato' rel='stylesheet'>
    </head>
    <body style='font-family:'Lato'; font-size:18px; padding:30; background-color:#FAFBFD'>
    <p>
    <center><div style='background-color:#82AA52; color:#FAFBFD; height:100px'>
    <h1>
    <img src='https://app.terra.bio/static/media/logo-wShadow.c7059479.svg' alt='Terra rocks!' style='vertical-align: middle;' height='100'>
    <span style='vertical-align: middle;'>
    Featured Workspace Report</span></h1>

    <h1><font color={status_color}>{status_text}</font></h1></center> <br><br>
    
    <br><br><big><b> Featured Workspace: </b>''' + workspace + ''' </big>
    <br><big><b> Billing Project: </b>''' + project + ''' </big>
    <br><br><big><b> Workflows Tested: </b>''' + ', '.join(workflows_list) + ''' </big>
    <br><big><b> Notebooks Tested: </b>''' + ', '.join(notebooks_list) + ''' </big>
    <br>
    <h2>Workflows:</h2>
    <blockquote> ''' + workflows_text + ''' </blockquote>
    <br>
    <h2>Notebooks:</h2>
    <blockquote> ''' + notebooks_text + ''' </blockquote>
    </p>

    </p></body>
    </html>'''

    message = message.format(status_color = status_color,
                            status_text = status_text)
    f.write(message)
    f.close()

    return html_output

