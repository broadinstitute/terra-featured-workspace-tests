import os
from dataclasses import dataclass, field

@dataclass
class Wspace:
    '''Class for keeping track of info for Terra workspaces.'''
    # TODO: probably want to store both original and cloned names/projects
    workspace: str              # workspace name
    project: str                # billing project
    status: str = None          # status of test
    workflows: list = field(default_factory=lambda: []) # this initializes with an empty list
    notebooks: list = field(default_factory=lambda: [])
    status: str = None
    report_path: str = None

    def __post_init__(self):
        # create the Terra link
        self.link = 'https://app.terra.bio/#workspaces/' + self.project + '/' + self.workspace + '/job_history/'


if __name__ == "__main__":
    # test this out
    a_workspace = Wspace(workspace = 'name_of_workspace',
                         project = 'billing_project')
    
    a_workspace.workflows = ['1-first workflow','2-second workflow']

    print(a_workspace.link)