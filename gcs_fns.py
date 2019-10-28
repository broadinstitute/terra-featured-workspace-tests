import os
import subprocess
# from google.cloud import storage

def upload_to_gcs(local_path, gcs_path, verbose=True):

    file_name = local_path.split('/')[-1] # this should be the name of the cloned workspace + '.html'

    # write file to google cloud 
    system_command = "gsutil cp " + local_path + " " + gcs_path
    os.system(system_command)

    # make file publicly accessible
    system_command = "gsutil acl ch -u AllUsers:R " + gcs_path + file_name
    os.system(system_command)

    # get report path (link to report on google cloud)
    public_path = gcs_path.replace('gs://','https://storage.googleapis.com/')
    report_path = public_path + file_name

    if verbose:
        print("Report can be viewed at " + report_path)

    return report_path

# def list_blobs(bucket_name):
#     """Lists all the blobs in the bucket."""
#     storage_client = storage.Client()

#     # Note: Client.list_blobs requires at least package version 1.17.0.
#     blobs = storage_client.list_blobs(bucket_name)

#     blobs_list = []
#     for blob in blobs:
#         blobs_list.append(blob.name)

#     return blobs_list