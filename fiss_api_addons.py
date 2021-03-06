"""
This module provides python bindings for the Firecloud API.
For more details see https://software.broadinstitute.org/firecloud/

To see how the python bindings map to the RESTful endpoints view
the README at https://pypi.python.org/pypi/firecloud.
"""

from firecloud import api as fapi
import json
from six.moves.urllib.parse import urlencode, urljoin

def get_workflow_metadata_withInclude(namespace, workspace, submission_id, workflow_id, *keysToInclude):
    """Request the metadata for a workflow in a submission.

    Args:
        namespace (str): project to which workspace belongs
        workspace (str): Workspace name
        submission_id (str): Submission's unique identifier
        workflow_id (str): Workflow's unique identifier.
        *keysToInclude (strs): any number of keys to INCLUDE, to restrict values returned

    Swagger:
        https://api.firecloud.org/#!/Submissions/workflowMetadata
    """
    includeKeyStr = '&'.join(['includeKey='+item for item in keysToInclude])
    uri = "workspaces/{0}/{1}/submissions/{2}/workflows/{3}?{4}&expandSubWorkflows=false".format(namespace,workspace, 
                submission_id, workflow_id, includeKeyStr)
    return fapi.__get(uri)

def get_workflow_metadata_withExclude(namespace, workspace, submission_id, workflow_id, *keysToExclude):
    """Request the metadata for a workflow in a submission.

    Args:
        namespace (str): project to which workspace belongs
        workspace (str): Workspace name
        submission_id (str): Submission's unique identifier
        workflow_id (str): Workflow's unique identifier.
        *keysToExclude (strs): any number of keys to EXCLUDE, to restrict values returned

    Swagger:
        https://api.firecloud.org/#!/Submissions/workflowMetadata
    """
    excludeKeyStr = '&'.join(['excludeKey='+item for item in keysToExclude])
    uri = "workspaces/{0}/{1}/submissions/{2}/workflows/{3}?{4}&expandSubWorkflows=false".format(namespace,workspace, 
                submission_id, workflow_id, excludeKeyStr)
    return fapi.__get(uri)

def export_workspace_attributes_TSV(namespace, workspace): 
    """Export workspace attributes.

    Args:
        namespace (str): project to which workspace belongs
        workspace (str): Workspace name

    Swagger:
        https://api.firecloud.org/#!/Workspaces/exportAttributesTSV
    """
    uri = "workspaces/{0}/{1}/exportAttributesTSV".format(namespace, workspace)
    return fapi.__get(uri)


def import_workspace_attributes_TSV(namespace, workspace, attrs): 
    """Import workspace attributes.

    Args:
        namespace (str): project to which workspace belongs
        workspace (str): Workspace name
        attrs (list(dict)): List of update operations for workspace attributes.
            Use the helper dictionary construction functions to create these:

            _attr_set()      : Set/Update attribute
            _attr_rem()     : Remove attribute
            _attr_ladd()    : Add list member to attribute
            _attr_lrem()    : Remove list member from attribute

    Swagger:
        https://api.firecloud.org/#!/Workspaces/importAttributesTSV
    """
    headers = fapi._fiss_agent_header({"Content-type":  "application/x-www-form-urlencoded"})
    body = urlencode({"attributes" : attrs})
    uri = "workspaces/{0}/{1}/importAttributesTSV".format(namespace, workspace)

    return fapi.__post(uri, headers=headers, data=body)
