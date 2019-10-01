import os
from dataclasses import dataclass

@dataclass
class Submission:
    '''Class for keeping track of info for Terra workflows.'''
    workspace: str      # workspace name
    ws_project: str     # workspace project/namespace
    wf_project : str    # workflow project/namespace
    wf_name: str        # workflow name
    entity_name: str    # data entity name
    entity_type: str    # data entity type
    sub_id: str = None  # submission Id
    status: str = None  # status of submission 
    
