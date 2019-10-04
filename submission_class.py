import os
import json
from dataclasses import dataclass
from datetime import datetime
from firecloud import api as fapi

@dataclass
class Submission:
    '''Class for keeping track of info for Terra workflows.'''
    workspace: str      # workspace name
    project: str        # workspace project/namespace
    wf_project : str    # workflow project/namespace
    wf_name: str        # workflow name
    entity_name: str    # data entity name
    entity_type: str    # data entity type
    sub_id: str = None  # submission Id
    status: str = None  # status of submission 
    
    def create_submission(self, verbose=False): 
        ''' create a workflow submission using fiss
        '''
        #TODO: Only run if status is None 
        # create a submission to run for this workflow
        if self.status is None:
            ret = fapi.create_submission(self.project, 
                                        self.workspace, 
                                        self.wf_project, 
                                        self.wf_name, 
                                        self.entity_name, 
                                        self.entity_type)
            fapi._check_response_code(ret, 201)
            ret = ret.json()

            self.sub_id = ret['submissionId']
            self.status = 'submission initialized in Python' # this will be set to the Terra status when check_status() is called
            if verbose:
                print(' submitted '+ self.wf_name)

    def check_status(self, verbose=False):
        ''' check the status of a workflow submission using fiss
        '''
        sub_res = fapi.get_submission(self.project, self.workspace, self.sub_id)
        fapi._check_response_code(sub_res, 200)
        sub_res = sub_res.json()

        self.status = sub_res['status']
        if verbose:
            print('   ' + self.wf_name + ' status at ' +datetime.today().strftime('%H:%M')+ ' is '+ self.status)
                        
                       