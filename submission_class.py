from dataclasses import dataclass
from datetime import datetime
from firecloud import api as fapi
from fiss_fns import call_fiss, format_timedelta
from fiss_api_addons import get_workflow_metadata_withExclude


@dataclass
class Submission:
    '''Class for keeping track of info for Terra workflow submissions.'''
    workspace: str              # workspace name
    project: str                # workspace project/namespace
    wf_project: str            # workflow project/namespace
    wf_name: str                # workflow name
    entity_name: str            # data entity name
    entity_type: str            # data entity type
    call_cache: bool = True     # use call cache (default True)
    expression: str = None      # expression to use (optional)
    wf_id: str = None           # workflow ID
    sub_id: str = None          # submission ID
    status: str = None          # status of submission
    final_status: str = None    # final status of submission
    message: str = None         # error message
    runtime: str = ''           # runtime for a submission - WIP - defined in get_final_status
    cost: int = None            # cost of submission

    def create_submission(self, verbose=False):
        ''' create a workflow submission using fiss
        '''
        # only run if status is None
        # create a submission to run for this workflow
        if self.status is None:
            # include list of specialcodes to handle the 400/404 errors with output
            res = call_fiss(fapi.create_submission, 201,
                            self.project,
                            self.workspace,
                            self.wf_project,
                            self.wf_name,
                            self.entity_name,
                            self.entity_type,
                            specialcodes=[400, 404],
                            use_callcache=self.call_cache,
                            expression=self.expression)

            # because we included specialcodes input, call_fiss returns the un-parsed json
            if res.status_code in [400, 404]:
                self.status = 'Submission Failed'
                try:
                    self.message = res.json()['message']
                except Exception:
                    self.message = 'UNKNOWN FAILURE!'
                if verbose:
                    print('SUBMISSION FAILED (error ' + str(res.status_code)
                          + ', status marked Submission Failed) - ' + self.wf_name)
                    print(self.message)
            else:
                # fapi._check_response_code(res, 201) # don't need to check, since this will only pass here if the response code = 201
                res = res.json()

                self.sub_id = res['submissionId']
                self.status = 'submission initialized in Python'  # this will be set to the Terra status when check_status() is called
                if verbose:
                    print('NEW SUBMISSION: ' + self.wf_name)

    def check_status(self, verbose=False):
        ''' check the status of a workflow submission using fiss
        '''
        res = call_fiss(fapi.get_submission, 200, self.project, self.workspace, self.sub_id)

        # try to get the wf_id
        if self.wf_id is None:
            for i in res['workflows']:
                if 'workflowId' in i:
                    self.wf_id = i['workflowId']

        self.status = res['status']
        if verbose:
            print('    ' + datetime.today().strftime('%H:%M') + ' ' + self.status + ' - ' + self.wf_name)

    def abort_submission(self):
        ''' abort submission
        '''
        res = call_fiss(fapi.abort_submission, 204, self.project, self.workspace, self.sub_id, specialcodes=[404])

    def get_final_status(self):
        ''' once a submission is done: update submission with finished status and error messages
        '''

        # 3 cases: 1) has wfID & subID; 2) has subID (submission happened but wf failed); 3) has neither (submission failed)
        if self.wf_id is not None:  # has wf_id and sub_id
            # get info about workflow submission - but exclude info about calls & inputs (which can make the json too big and cause an error)
            res = call_fiss(get_workflow_metadata_withExclude, 200, self.project, self.workspace, self.sub_id, self.wf_id, 'calls', 'inputs')
            self.final_status = res['status']

            start_time = res['start']  # overwrite status from submission tracking
            end_time = res['end']  # overwrite status from submission tracking
            terra_time_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            elapsed = datetime.strptime(end_time, terra_time_fmt) - datetime.strptime(start_time, terra_time_fmt)
            self.runtime = format_timedelta(elapsed, 2)  # 2 hours threshold for marking in red

            # in case of failure, pull out the error message
            if self.final_status == 'Failed':
                self.message = ''
                for failed in res['failures']:
                    for message in failed['causedBy']:
                        self.message += str(message['message'])

        elif self.sub_id is not None:  # no wf_id but has sub_id
            res = call_fiss(fapi.get_submission, 200, self.project, self.workspace, self.sub_id)
            for i in res['workflows']:
                self.final_status = i['status']
            if self.final_status == 'Failed':
                # get the error message(s) for why it failed
                self.message = ''
                for i in res['workflows']:
                    self.message += str(i['messages'])[1:-1]
            else:  # should probably never get here, but just in case
                self.message = 'unrecognized status'

        else:  # no wf_id or sub_id
            self.final_status = self.status
            # pass # you should already have the info needed from the submission failure

    def get_cost(self, verbose=True):
        sub_json = call_fiss(fapi.get_submission, 200, self.project, self.workspace, self.sub_id, specialcodes=[404])
        if sub_json.status_code != 404:  # 404 means submission not found
            sub_json = sub_json.json()
            cost = sub_json['cost']
            self.cost = cost
            if verbose:
                print(f'    cost ${cost:.2f}')
        return cost

    def get_link(self):
        # create the tracking link - ideally job manager, otherwise point to Terra job history
        if self.wf_id:
            # link = 'https://job-manager.dsde-prod.broadinstitute.org/jobs/' + self.wfid
            link = f'https://job-manager.dsde-prod.broadinstitute.org/jobs/{self.wf_id}'
        elif self.sub_id:
            # link = 'https://app.terra.bio/#workspaces/' + self.project.replace(' ','%20') + '/' + self.workspace.replace(' ','%20') + '/job_history/' + self.sub_id
            link = 'https://app.terra.bio/#workspaces/{project}/{workspace}/job_history/{subid}'\
                   .format(project=self.project.replace(' ', '%20'),
                           workspace=self.workspace.replace(' ', '%20'),
                           subid=self.sub_id)
        else:
            # link = 'https://app.terra.bio/#workspaces/' + self.project.replace(' ','%20') + '/' + self.workspace.replace(' ','%20') + '/job_history/'
            link = 'https://app.terra.bio/#workspaces/{project}/{workspace}/job_history/'\
                   .format(project=self.project.replace(' ', '%20'),
                           workspace=self.workspace.replace(' ', '%20'))
        self.link = link

        return link

    def get_HTML(self):
        # check status of submission
        if (self.final_status == 'Failed') or (self.final_status == 'Submission Failed'):
            status_color = 'red'
            error_message = '<br>Error message: <font color=' + status_color + '>' + str(self.message) + '</font>'
        elif self.status == 'Aborted':
            status_color = 'orange'
            error_message = ''
        elif self.final_status == 'Not tested':
            status_color = 'orange'
            error_message = f'<br>Note: {str(self.message)}'
        else:
            status_color = 'green'
            error_message = ''

        if self.runtime == '':
            runtime_text = ''
        else:
            runtime_text = f'<br>Runtime: {self.runtime}'

        message_html = '''
        Workflow Id: {wfid}
        <br>Submission Id: {subid}
        <br>Entity Name: {entity}
        <br>Status: <font color={status_color}>{status}</font>
        {error_message}
        {runtime}
        <br><a href={link} target='_blank'>Click here for more details</a>
        <br><br>
        '''
        message_html = message_html.format(wfname=self.wf_name,
                                           wfid=self.wf_id,
                                           subid=self.sub_id,
                                           entity=self.entity_name,
                                           status_color=status_color,
                                           status=self.final_status,
                                           error_message=error_message,
                                           runtime=runtime_text,
                                           link=self.get_link())

        return message_html
