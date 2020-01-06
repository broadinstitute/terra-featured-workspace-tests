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
'''
curl 'https://api.firecloud.org/api/workspaces/broad-firecloud-dsde/cnn-variant-filter%20copy%20MORGAN/importAttributesTSV' 
-H 'authority: api.firecloud.org' 
-H 'authorization: Bearer ***REMOVED***' 
-H 'x-app-id: Saturn' 
-H 'origin: https://app.terra.bio' 
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36' 
-H 'content-type: multipart/form-data; boundary=----WebKitFormBoundaryauSAqB33tLV9mkg5' 
-H 'accept: */*' 
-H 'sec-fetch-site: cross-site' 
-H 'sec-fetch-mode: cors' 
-H 'referer: https://app.terra.bio/' 
-H 'accept-encoding: gzip, deflate, br' 
-H 'accept-language: en-US,en;q=0.9' --data-binary $'------WebKitFormBoundaryauSAqB33tLV9mkg5\r\nContent-Disposition: form-data; name="attributes"; filename="cnn-variant-filter-workspace-attributes.tsv"\r\nContent-Type: text/tab-separated-values\r\n\r\n\r\n------WebKitFormBoundaryauSAqB33tLV9mkg5--\r\n' --compressed
'''



'''
def get_entities_with_type(namespace, workspace):
    """List entities in a workspace.

    Args:
        namespace (str): project to which workspace belongs
        workspace (str): Workspace name

    Swagger:
        https://api.firecloud.org/#!/Entities/getEntitiesWithType
    """
    uri = "workspaces/{0}/{1}/entities_with_type".format(namespace, workspace)
    return __get(uri)

def update_workspace_attributes(namespace, workspace, attrs): # morgan
    """Update or remove workspace attributes.

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
        https://api.firecloud.org/#!/Workspaces/updateAttributes
    """
    headers = _fiss_agent_header({"Content-type":  "application/json"})
    uri = "{0}workspaces/{1}/{2}/updateAttributes".format(fcconfig.root_url,
                                                        namespace, workspace)
    body = json.dumps(attrs)

    # FIXME: create __patch method, akin to __get, __delete etc
    return __SESSION.patch(uri, headers=headers, data=body)

'''