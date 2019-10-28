from dataclasses import dataclass, field
from firecloud import api as fapi
from submission_class import Submission
from gcs_fns import upload_to_gcs
from fiss_fns import call_fiss

@dataclass
class Wspace:
    '''Class for keeping track of info for Terra workspaces.'''
    # TODO: make workspace, project immutable / set once
    # TODO: make a constructor that sets this up straight from the json from FISS
    workspace: str              # workspace name
    project: str                # billing project
    workspace_orig: str = None  # original name of workspace (if cloned)
    project_orig: str = None    # original billing project (if cloned)
    status: str = None          # status of test
    workflows: list = field(default_factory=lambda: []) # this initializes with an empty list
    notebooks: list = field(default_factory=lambda: [])
    active_submissions: list = field(default_factory=lambda: [])
    tested_workflows: list = field(default_factory=lambda: [])
    report_path: str = None

    def __post_init__(self):
        # create the Terra link
        self.link = 'https://app.terra.bio/#workspaces/{project}/{workspace}/job_history'\
                            .format(project=self.project.replace(' ','%20'),
                                    workspace=self.workspace.replace(' ','%20'))
        self.key = self.project + '/' + self.workspace
        #self.notebooks = list_notebooks(self.project, self.workspace, ipynb_only=True, verbose=False)

    def create_submissions(self, verbose=False):
        project = self.project
        workspace = self.workspace
        if verbose:
            print('\nRunning workflow submissions on '+workspace)
    
        # Get a list of workflows in the project
        res = call_fiss(fapi.list_workspace_configs, 200, project, workspace, allRepos = True)

        # set up submission classes and structure them as lists
        if len(res) > 0: # only proceed if there are workflows
            # get list of workflows to submit
            workflow_names = []
            submissions_unordered = {}

            for item in res:  # for each item (workflow)
                wf_name = item['name']              # the name of the workflow
                workflow_names.append(wf_name)
                # identify the type of data (entity) being used by this workflow, if any
                if 'rootEntityType' in item:
                    entityType = item['rootEntityType']
                else:
                    entityType = None
                project_orig = item['namespace']    # workflow billing project
                wf_name = item['name']              # the name of the workflow

                # get and store the name of the data (entity) being used, if any
                entities = call_fiss(fapi.get_entities, 200, project, workspace, entityType)
                entityName = None
                if len(entities) != 0:
                    allEntities = []
                    for ent in entities:
                        allEntities.append(ent['name'])
                    
                    # if there's a _test entity, use it
                    for ent in allEntities:
                        if '_test' in ent:
                            entityName = ent
                    # otherwise if there's a _small entity, use it
                    if entityName is None:
                        for ent in allEntities:
                            if '_small' in ent:
                                entityName = ent   
                    # otherwise just use the first entity 
                    if entityName is None:
                        entityName = allEntities[0] # use the first one
                    
                    # # sanity check
                    # print(allEntities)
                    # print(entityName)

                # populate dictionary of inputs for fapi.create_submission
                submissions_unordered[wf_name] = Submission(workspace = workspace,
                                                            project = project,     
                                                            wf_project = project_orig,  
                                                            wf_name = wf_name,      
                                                            entity_name = entityName,
                                                            entity_type = entityType)


            # check whether workflows are ordered, and structure list of submissions accordingly
            first_char = list(wf[0] for wf in workflow_names)
            submissions_list = []
            if ('1' in first_char) and ('2' in first_char):
                do_order = True
                workflow_names.sort()
                for wf_name in workflow_names:
                    submissions_list.append([submissions_unordered[wf_name]])
                if verbose:
                    print('[submitting workflows sequentially]')
            else:
                do_order = False
                sub_list = []
                for wf_name in workflow_names:
                    sub_list.append(submissions_unordered[wf_name])
                submissions_list = [sub_list]
                if verbose:
                    print('[submitting workflows in parallel]')
            
            self.active_submissions = submissions_list


    def check_submissions(self, verbose=True):
        # SUBMIT the submissions and check status
        
        # define terminal states
        terminal_states = set(['Done', 'Aborted', 'Nonstarter'])

        if len(self.active_submissions) > 0: # only proceed if there are still active submissions to do
            count = 0
            # the way active_submissions is structured, if workflows need to be run in order, they will be 
            # separate lists within active_submissions; if they can be run in parallel, there will be 
            # one list inside active_submissions containing all the workflow submissions to run.
            sublist = self.active_submissions[0]
            for sub in sublist: 
                # if the submission hasn't yet been submitted, do it
                if sub.status is None:
                    sub.create_submission(verbose=True)
                
                # if the submission hasn't finished, check its status
                if sub.status not in terminal_states: # to avoid overchecking
                    sub.check_status(verbose=True) # check and update the status of the submission
                
                # if the submission has finished, count it
                if sub.status in terminal_states:
                    count += 1
                    if sub.wf_name not in (wfsub.wf_name for wfsub in self.tested_workflows):
                        # get final status & error messages; append the full submission as a list item in tested_workflows
                        sub.get_final_status()
                        self.tested_workflows.append(sub)
            
            if verbose:
                print('    Finished ' + str(count) + ' of ' + str(len(sublist)) + ' workflows in this set of submissions')

            # if all submissions are done, remove this set of submissions from the master submissions_list
            if count == len(sublist):
                self.active_submissions.pop(0)
                # immediately submit the next submission if there is one
                self.check_submissions()

    
    def generate_workspace_report(self, gcs_path, verbose=False):
        ''' generate a failure/success report for each workflow in a workspace, 
        only reporting on the most recent submission for each report.
        this returns a string html_output that's currently not modified by this function but might be in future!
        '''
        if verbose:
            print('\nGenerating workspace report for '+self.workspace)
        
        failed = False
        # see if any tested workflow didn't succeed
        for wfsub in self.tested_workflows:
            if wfsub.status != 'Succeeded':
                failed = True
         
        ## set up the html report
        # if there were ANY failures
        if failed:
            status_text = 'FAILURE!'
            status_color = 'red'
        else:
            status_text = 'SUCCESS!'
            status_color = 'green'

        # make a list of the workflows
        workflows_list = list(wfsub.wf_name for wfsub in self.tested_workflows) #self.workflows #list(workflow_dict.keys())

        # make a list of the notebooks
        notebooks_list = ['These tests do not currently test notebooks'] #self.notebooks #list_notebooks(project, workspace, ipynb_only=True)
        # if len(notebooks_list) == 0:
        #     notebooks_list = ['No notebooks in workspace']
        
        # generate detail text from workflows
        workflows_text = ''
        for wfsub in self.tested_workflows:
            workflows_text += '<h3>{wf_name}</h3><blockquote>{html}</blockquote>'\
                                    .format(wf_name = wfsub.wf_name, 
                                            html = wfsub.get_HTML())
        
        # generate detail text from notebooks
        notebooks_text = notebooks_list

        html_output = self.workspace.replace(' ','_') + '.html'
        local_path = '/tmp/' + html_output
        # open, generate, and write the html text for the report
        f = open(local_path,'w')
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
        <br><br><h2><b> Cloned Workspace: </b>
        <a href={workspace_link} target='_blank'>{workspace}</a></h2>
        <big><b> Featured Workspace: </b>{workspace_orig}</big>
        <br>
        <big><b> Billing Project: </b>{project_orig}</big>
        <br><br><big><b> Workflows: </b>{wf_list}</big>
        <br><big><b> Notebooks: </b>{nb_list}</big>
        <br>
        <h2>Workflows:</h2>
        <blockquote>{wf_text}</blockquote>
        <br>
        <h2>Notebooks:</h2>
        <blockquote>{nb_text}</blockquote>
        </p>

        </p></body>
        </html>'''

        message = message.format(status_color = status_color,
                                status_text = status_text,
                                workspace_link = self.link,
                                workspace = self.workspace,
                                workspace_orig = self.workspace_orig,
                                project_orig = self.project_orig,
                                wf_list = ', '.join(workflows_list),
                                nb_list = ', '.join(notebooks_list),
                                wf_text = workflows_text,
                                nb_text = notebooks_text
                                )
        f.write(message)
        f.close()

        # upload report to google cloud bucket
        report_path = upload_to_gcs(local_path, gcs_path, verbose)

        self.report_path = report_path
        self.status = status_text


if __name__ == "__main__":
    # test this out
    a_workspace = Wspace(workspace = 'name_of_workspace',
                         project = 'billing_project')
    
    a_workspace.workflows = ['1-first workflow','2-second workflow']

    print(a_workspace.key)