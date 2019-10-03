import os
import json
import time
import argparse
import subprocess
from datetime import datetime
from wflow_class import Wflow
from dataclasses import dataclass, field
from firecloud import api as fapi
from submission_class import Submission


@dataclass
class Wspace:
    '''Class for keeping track of info for Terra workspaces.'''
    # TODO: probably want to store both original and cloned names/projects
    # TODO: make workspace, project immutable / set once
    # TODO: make a constructor that sets this up straight from the json from FISS
    workspace: str              # workspace name
    project: str                # billing project
    status: str = None          # status of test
    workflows: list = field(default_factory=lambda: []) # this initializes with an empty list
    notebooks: list = field(default_factory=lambda: [])
    active_submissions: list = field(default_factory=lambda: [])
    report_path: str = None

    def __post_init__(self):
        # create the Terra link
        self.link = 'https://app.terra.bio/#workspaces/' + self.project + '/' + self.workspace + '/job_history/'
        self.key = self.project + '/' + self.workspace
        #self.notebooks = list_notebooks(self.project, self.workspace, ipynb_only=True, verbose=False)

    # def submit_workflows(self):

    # def check_status(self):

    def run_workflow_submission(self, sleep_time=60, verbose=False):
        ''' 
        '''
        project = self.project
        workspace = self.workspace
        if verbose:
            print('\nRunning workflow submissions on '+workspace)
        
        # terminal states
        terminal_states = set(['Done', 'Aborted'])
    
        # Get a list of workflows in the project
        res = fapi.list_workspace_configs(project, workspace, allRepos = True)
        fapi._check_response_code(res, 200)
        res = res.json()    # convert to json

        if len(res) > 0: # only proceed if there are workflows
            # run through the workflows and get information to create submissions for each workflow
            submissions = {}    # dict to store info about submissions

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
                submission_input = Submission(workspace = workspace,
                                    project = project,     
                                    wf_project = project_orig,  
                                    wf_name = wf_name,      
                                    entity_name = entityName,
                                    entity_type = entityType)
                submissions[wf_name] = submission_input

            workflow_names = list(submissions.keys())
            workflow_names.sort()

            # check whether workflows are ordered, if so, run in order
            first_char = list(wf[0] for wf in workflow_names)
            if ('1' in first_char) and ('2' in first_char):
                do_order = True
                if verbose:
                    print('[submitting workflows sequentially]')
            else:
                do_order = False
                if verbose:
                    print('[submitting workflows in parallel]')

            for wf_name in workflow_names:
                wf = submissions[wf_name]
                wf.create_submission(verbose=True)
                # create a submission to run for this workflow
                # ret = fapi.create_submission(wf.ws_project, 
                #                             wf.workspace, 
                #                             wf.wf_project, 
                #                             wf.wf_name, 
                #                             wf.entity_name, 
                #                             wf.entity_type)
                # fapi._check_response_code(ret, 201)
                
               

                # if the workflows must be run sequentially, wait for each to finish
                if do_order:
                    # ret = ret.json()
                    # submissionId = ret['submissionId']
                    # wf.sub_id = submissionId
                    
                    break_out = False
                    while not break_out:
                        # sub_res = fapi.get_submission(project, workspace, submissionId)
                        # fapi._check_response_code(sub_res, 200)

                        # sub_res = sub_res.json()
                        # submission_status = sub_res['status']
                        # wf.status = submission_status
                        # if verbose:
                        #     print(' ' +datetime.today().strftime('%H:%M')+ ' status: '+ submission_status)

                        wf.check_status(verbose=True)
                        if wf.status in terminal_states:
                            break_out = True
                        else:
                            time.sleep(sleep_time)


            # wait for the submission to finish (i.e. submission status is Done or Aborted)
            break_out = False       # flag for being done
            count = 0               # count how many submissions are done; to check if all are done
            finished_workflows = []   # will be a list of finished workflows

            while not break_out:
                # get the current list of submissions and their statuses
                res = fapi.list_submissions(project, workspace)
                fapi._check_response_code(res, 200)
                res = res.json()
                
                for item in res: # for each workflow
                    if item['status'] in terminal_states: # if the workflow status is Done or Aborted
                        count += 1
                        if item['methodConfigurationName'] not in finished_workflows:
                            details = str(item['methodConfigurationName']) + ' finished on '+ datetime.today().strftime('%m/%d/%Y at %H:%M')
                            finished_workflows.append(item['methodConfigurationName'])
                
                if count == len(res): # if all workflows are done, you're done!
                    break_out = True
                    sleep_time = 0
                
                if verbose:
                    # print progress
                    print(datetime.today().strftime('%H:%M') \
                        + ' - finished ' + str(count) + ' of ' + str(len(res)) + ' workflows: ' \
                        + ', '.join(finished_workflows))
                
                # if not all workflows are done yet, reset the count and wait sleep_time seconds to check again
                count = 0 
                time.sleep(sleep_time)

        else: # if there are no workflows
            finished_workflows = None
        
        return finished_workflows


if __name__ == "__main__":
    # test this out
    a_workspace = Wspace(workspace = 'name_of_workspace',
                         project = 'billing_project')
    
    a_workspace.workflows = ['1-first workflow','2-second workflow']

    print(a_workspace.key)