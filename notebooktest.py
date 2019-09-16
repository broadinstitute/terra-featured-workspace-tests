from firecloud import api as fapi
import json
import subprocess

#"featured-workspace-testing", "Terra_Quickstart_Workspace_MORGAN_manualclone" - 4 Notebooks
#fc-product-demo", "Terra_Quickstart_Workspace" - 4 Notebooks
#"gmqltobroad" , "gmql" - 0 Notbooks
r = fapi.get_workspace("gmqltobroad" , "gmql")

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
    bucket_files = bucket_files.decode().split('\n')
notebook_files = []
print("Testing")
#TODO: Add a use case that if the bucket doesn't have notebooks

for f in bucket_files:
    if "notebook" in f:
        notebook_files.append(f)

if len(notebook_files) == 0:
    print("Workspace has no notebooks")
else: 
    print('\n'.join(notebook_files))
