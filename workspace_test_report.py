import os
import json
import time
import argparse
import subprocess
from datetime import datetime
from wflow_class import Wflow
from ws_class import Wspace
from firecloud import api as fapi
from submission_class import Submission

# from tenacity import retry

## for troubleshooting
# import pprint
# pp = pprint.PrettyPrinter(indent=4)

# TODO: add tenacity @retry for api calls

def get_ws_bucket(project, name):
    ''' get the google bucket path name for the given workspace
    '''
    # call the api, check for errors, pull out the bucket name
    res = fapi.get_workspace(project, name)
    fapi._check_response_code(res, 200)
    workspace = res.json()
    bucket = workspace['workspace']['bucketName']
    return bucket


def clone_workspace(original_project, original_name, clone_project, verbose=False):
    ''' clone a workspace, including everything in the notebooks folder in the google bucket
    '''
    if verbose:
        print('\nCloning ' + original_name)

    # define the name of the cloned workspace
    clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')     # time of clone
    clone_name = original_name +'_' + clone_time                    # cloned name is the original name + current date/time
    error_message = ''                                              # will be filled if there's an error

    # clone the Featured Workspace & check for errors
    res = fapi.clone_workspace(original_project,
                            original_name,
                            clone_project,
                            clone_name)
    fapi._check_response_code(res, 201)
    
    # get gs addresses of original & cloned workspace buckets
    original_bucket = get_ws_bucket(original_project, original_name)
    clone_bucket = get_ws_bucket(clone_project, clone_name)
    
    # TODO: check if the gsutil cp command is supposed to return something because it currently does not
    if len(list_notebooks(original_project, original_name, ipynb_only=False, verbose=False)) > 0: # if the bucket isn't empty
        gsutil_args = ['gsutil', 'cp', 'gs://' + original_bucket + '/notebooks/**', 'gs://' + clone_bucket + '/notebooks/']
        bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
        # # check output produces a string in Py2, Bytes in Py3, so decode if necessary
        # if type(bucket_files) == bytes:
        #     bucket_files = bucket_files.decode().split('\n')
        
        if verbose:
            print('Notebook files copied: ')
            # print(bucket_files)
            list_notebooks(clone_project, clone_name, ipynb_only=False, verbose=True)

    clone_ws = Wspace(  workspace = clone_name,
                        project = clone_project,
                        notebooks = list_notebooks(clone_project, clone_name, ipynb_only=True, verbose=False))
                            

    return clone_ws


def list_notebooks(project, workspace, ipynb_only=True, verbose=False):
    ''' get a list of everything in the notebooks folder (if ipynb_only = False) 
    or of only jupyter notebook files (if ipynb_only = True) in the workspace
    '''
    # get the bucket for this workspace
    bucket = get_ws_bucket(project, workspace)

    notebooks_list = []

    # check if bucket is empty
    gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/']
    bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
    
    # if the bucket isn't empty, check for notebook files and copy them
    if len(bucket_files)>0: 
        # list files present in the bucket
        gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/**']
        bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
        
        # check output produces a string in Py2, Bytes in Py3, so decode if necessary
        if type(bucket_files) == bytes:
            bucket_files = bucket_files.decode().split('\n')

        # select which files to list
        if ipynb_only:
            keyword = '.ipynb'       # returns only .ipynb files
        else:
            keyword = 'notebooks/'   # returns all files in notebooks/ folder

        # pull out the notebook names from the full file paths
        for f in bucket_files:
            if keyword in f:
                f = f.split('/')[-1]
                notebooks_list.append(f)
    
    if verbose:
        if len(notebooks_list) == 0:
            print('Workspace has no notebooks')
        else: 
            print('\n'.join(notebooks_list))
    
    return notebooks_list


def test_single_ws(workspace, project, clone_project, gcs_path, sleep_time=60, verbose=True):
    ''' clone, run submissions, and generate report for a single workspace
    TODO: move this function into the Wspace class
    '''

    # clone workspace
    clone_ws = clone_workspace(project, workspace, clone_project, verbose)

    # create and monitor submissions
    clone_ws.run_workflow_submission(sleep_time, verbose)
    if verbose:
        print(clone_ws.tested_workflows)

    # generate workspace report
    clone_ws.generate_workspace_report(gcs_path, verbose)

    return clone_ws


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--clone_name', type=str, help='name of cloned workspace')
    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--original_name', type=str, default='Sequence-Format-Conversion', help='name of workspace to clone')
    parser.add_argument('--original_project', type=str, default='help-gatk', help='project for original workspace')

    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--html_output', type=str, default='workspace_report.html', help='address to create html doc for report')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')

    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    # run the test on a single workspace
    ws = test_single_ws(args.original_name, args.original_project, args.clone_project, 
                                    args.gcs_path, args.sleep_time, args.verbose)
    report_path = ws.report_path
    
    # open the report
    os.system('open ' + report_path)
    
    