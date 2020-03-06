import os
import time
import argparse
import subprocess
from datetime import datetime
from ws_class import Wspace
from firecloud import api as fapi
from fiss_fns import call_fiss
from gcs_fns import run_subprocess


def get_ws_bucket(project, name):
    ''' get the google bucket path name for the given workspace
    '''
    # call the api, check for errors, pull out the bucket name
    workspace = call_fiss(fapi.get_workspace, 200, project, name)
    bucket = workspace['workspace']['bucketName']
    return bucket


def clone_workspace(original_project, original_name, clone_project, clone_name=None,
                    clone_time=None, share_with=None, 
                    call_cache=True, verbose=False, 
                    copy_bucket=False):
    ''' clone a workspace, including everything in the notebooks folder in the google bucket
    this also shares the workspace with emails/groups listed in share_with
    '''
    
    # define the name of the cloned workspace
    if clone_name is None:
        if clone_time is None:
            clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')     # time of clone
        clone_name = original_name +'_' + clone_time                    # cloned name is the original name + current date/time

    if verbose:
        print('\nCloning ' + original_name + ' to ' + clone_name)


    # get email address(es) of owner(s) of original workspace
    response = call_fiss(fapi.get_workspace, 200, original_project, original_name)
    original_owners = response['owners']

    # clone the Featured Workspace & check for errors
    call_fiss(fapi.clone_workspace, 201, original_project,
                            original_name,
                            clone_project,
                            clone_name)
    
    # share cloned workspace with anyone listed in share_with
    if share_with is not None:
        acl_updates = [{
                "email": share_with,
                "accessLevel": "READER",
                "canShare": True,
                "canCompute": False
            }]
        call_fiss(fapi.update_workspace_acl, 200, # def update_workspace_acl(namespace, workspace, acl_updates, invite_users_not_found=False)
                    clone_project,
                    clone_name,
                    acl_updates,
                    True) # set invite_users_not_found=True
    
    # optionally copy entire bucket, including notebooks
    # get gs addresses of original & cloned workspace buckets
    original_bucket = get_ws_bucket(original_project, original_name)
    clone_bucket = get_ws_bucket(clone_project, clone_name)
    
    if copy_bucket: # copy everything in the bucket
        bucket_files = run_subprocess(['gsutil', 'ls', 'gs://' + original_bucket + '/'], 'Error listing bucket contents')
        # bucket_files = subprocess.check_output(['gsutil', 'ls', 'gs://' + original_bucket + '/'])
        if len(bucket_files)>0:
            # gsutil_args = ['gsutil', 'cp', 'gs://' + original_bucket + '/**', 'gs://' + clone_bucket + '/']
            gsutil_args = ['gsutil', '-m', 'rsync', '-r', 'gs://' + original_bucket, 'gs://' + clone_bucket]
            bucket_files = run_subprocess(gsutil_args, 'Error copying over original bucket to clone bucket')
            # bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
            # # check output produces a string in Py2, Bytes in Py3, so decode if necessary
            # if type(bucket_files) == bytes:
            #     bucket_files = bucket_files.decode().split('\n')
    else: # only copy notebooks
        if len(list_notebooks(original_project, original_name, ipynb_only=False, verbose=False)) > 0: # if the notebooks folder isn't empty
            # gsutil_args = ['gsutil', 'cp', 'gs://' + original_bucket + '/notebooks/**', 'gs://' + clone_bucket + '/notebooks/']
            gsutil_args = ['gsutil', '-m', 'rsync', '-r', 'gs://' + original_bucket + '/notebooks', 'gs://' + clone_bucket + '/notebooks']
            bucket_files = run_subprocess(gsutil_args, 'Error copying over original bucket to clone bucket')
            # bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
    if verbose:
        print('Notebook files copied:')
        list_notebooks(clone_project, clone_name, ipynb_only=False, verbose=True)

    clone_ws = Wspace(  workspace = clone_name,
                        project = clone_project,
                        workspace_orig = original_name,
                        project_orig = original_project,
                        owner_orig = original_owners,
                        call_cache = call_cache,
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
    bucket_files = run_subprocess(gsutil_args, 'Error listing bucket contents')
    # bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
    
    # if the bucket isn't empty, check for notebook files and copy them
    if len(bucket_files)>0: 
        # list files present in the bucket
        gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/**']
        bucket_files = run_subprocess(gsutil_args, 'Error listing bucket contents')
        # bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
        
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


def test_single_ws(workspace, project, clone_project, gcs_path, call_cache, abort_hr, sleep_time=60, share_with=None, mute_notifications=True, verbose=True):
    ''' clone, run submissions, and generate report for a single workspace
    '''
    # determine whether to email notifications of failures
    send_notifications = ~args.mute_notifications

    # clone workspace
    clone_ws = clone_workspace(project, workspace, clone_project, share_with=share_with, call_cache=call_cache, verbose=verbose)

    # create and monitor submissions
    clone_ws.create_submissions(verbose=verbose)
    clone_ws.start_timer()

    break_out = False
    while not break_out:
        clone_ws.check_submissions(abort_hr=abort_hr, verbose=verbose)
        if len(clone_ws.active_submissions) > 0: # if there are still active submissions
            time.sleep(sleep_time) # note - TODO to fix: this currently has unintended behavior of waiting to submit the next submission when run in order
        else:
            clone_ws.stop_timer()
            break_out = True

    # generate workspace report
    # total_cost = clone_ws.get_workspace_run_cost()
    # print(total_cost)
    clone_ws.generate_workspace_report(gcs_path, send_notifications, verbose)

    return clone_ws


def test_one(args):
    # run the test on a single workspace
    ws = test_single_ws(args.original_name, args.original_project, args.clone_project, 
                                    args.gcs_path, args.call_cache, args.abort_hr, args.sleep_time, 
                                    args.share_with, args.mute_notifications, args.verbose)
    report_path = ws.report_path
    
    # open the report
    os.system('open ' + report_path)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--clone_name', type=str, help='name of cloned workspace')
    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--original_name', type=str, default='Sequence-Format-Conversion', help='name of workspace to clone')
    parser.add_argument('--original_project', type=str, default='help-gatk', help='project for original workspace')
    parser.add_argument('--share_with', type=str, default='GROUP_FireCloud-Support@firecloud.org', help='email address of person or group with which to share cloned workspace')

    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--html_output', type=str, default='workspace_report.html', help='address to create html doc for report')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')
    parser.add_argument('--abort_hr', type=int, default=None, help='# of hours after which to abort submissions (default None). set to None if you do not wish to abort ever.')
    parser.add_argument('--call_cache', type=bool, default=True, help='whether to call cache the submissions (default True)')

    parser.add_argument('--mute_notifications', '-m', action='store_true', help='do NOT send emails to workspace owners in case of failure (default is do send)')

    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    test_one(args)
    
    
    