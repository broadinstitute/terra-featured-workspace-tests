"""
This module provides python bindings for the Firecloud API.
For more details see https://software.broadinstitute.org/firecloud/

To see how the python bindings map to the RESTful endpoints view
the README at https://pypi.python.org/pypi/firecloud.
"""

from firecloud import api as fapi
import json

from six import string_types
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

def get_workspace_cloudPlatform(namespace, name):
    """get cloud platform of workspace"""
    request_url = f'https://api.firecloud.org/api/workspaces/{namespace}/{name}?fields=workspace.cloudPlatform'

    return fapi.__get(request_url)

def clone_workspace_with_bucket_location(from_namespace, from_workspace, to_namespace, to_workspace, bucketLocation, authorizationDomain="", copyFilesWithPrefix=None):
    """Clone a Terra workspace.

    A clone is a shallow copy of a Terra workspace, enabling
    easy sharing of data, such as TCGA data, without duplication.

    Args:
        from_namespace (str):  project (namespace) to which source workspace belongs
        from_workspace (str): Source workspace's name
        to_namespace (str):  project to which target workspace belongs
        to_workspace (str): Target workspace's name
        bucketLocation (str): Target workspace's bucket location
        authorizationDomain: (str) required authorization domains
        copyFilesWithPrefix: (str) prefix of bucket objects to copy to the destination workspace

    Swagger:
        https://api.firecloud.org/#!/Workspaces/cloneWorkspace
    """

    if authorizationDomain:
        if isinstance(authorizationDomain, string_types):
            authDomain = [{"membersGroupName": authorizationDomain}]
        else:
            authDomain = [{"membersGroupName": authDomain} for authDomain in authorizationDomain]
    else:
        authDomain = []

    body = {
        "namespace": to_namespace,
        "name": to_workspace,
        "attributes": dict(),
        "bucketLocation": bucketLocation,
        "authorizationDomain": authDomain,
    }

    if copyFilesWithPrefix is not None:
        body["copyFilesWithPrefix"] = copyFilesWithPrefix

    uri = "workspaces/{0}/{1}/clone".format(from_namespace, from_workspace)
    return fapi.__post(uri, json=body)