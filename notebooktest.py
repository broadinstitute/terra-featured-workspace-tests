from firecloud import api as fapi
import json
import subprocess

#"featured-workspace-testing", "Terra_Quickstart_Workspace_MORGAN_manualclone"
r = fapi.get_workspace("fc-product-demo", "Terra_Quickstart_Workspace")
fapi._check_response_code(r, 200)
workspace = r.json()
bucket = workspace['workspace']['bucketName']
bucket_prefix = 'gs://' + bucket
workspace_name = workspace['workspace']['name']

# # Now run a gsutil ls to list files present in the bucket
gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/**']
bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
# Check output produces a string in Py2, Bytes in Py3, so decode if necessary
if type(bucket_files) == bytes:
    bucket_files = bucket_files.decode()
print(bucket_files)
print(" ")
print("Testing")
gsutil_args = ['gsutil', 'cp', 'gs://' + bucket + '/notebooks/**', "gs://fc-324abe6c-3229-4e18-abcf-32c126de6bfd/notebooks"] 
bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)

#print(fapi.list_entity_types("featured-workspace-testing", "Terra_Quickstart_Workspace_MORGAN_manualclone").json())