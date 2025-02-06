import os
import subprocess
import tenacity as tn
import logging
import sys

from google.auth import default
from google.cloud import storage

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)


def my_before_sleep(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logger.log(
        loglevel, 'Retrying %s with %s in %s seconds; attempt #%s ended with: %s',
        retry_state.fn, retry_state.args, str(int(retry_state.next_action.sleep)), retry_state.attempt_number,
        retry_state.outcome)


@tn.retry(wait=tn.wait_chain(*[tn.wait_fixed(5)] +
                              [tn.wait_fixed(10)] +
                              [tn.wait_fixed(30)] +
                              [tn.wait_fixed(60)]),
          stop=tn.stop_after_attempt(5),
          before_sleep=my_before_sleep)
def run_subprocess(cmd, errorMessage):
    if isinstance(cmd, list):
        cmd = ' '.join(cmd)
    try:
        # print("running command: " + cmd)
        return subprocess.check_output(
            cmd, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(errorMessage)
        print("Exited with " + str(e.returncode) + "-" + e.output)
        exit(1)


def convert_to_public_url(gs_input):
    return gs_input.replace('gs://', 'https://storage.googleapis.com/')


def upload_to_gcs(local_path, gcs_path, verbose=True):
    """
    Uploads a file to Google Cloud Storage and makes it publicly accessible.

    Args:
        local_path (str): Path to the local file to upload.
        gcs_path (str): Destination GCS path (e.g., 'gs://my-bucket/path/').
        verbose (bool): Whether to print upload status messages.

    Returns:
        str: Public URL of the uploaded file.
    """
    credentials, project_id = default()
    print(f"Authenticated with project: {project_id}")
    client = storage.Client()
    bucket_name = gcs_path.replace("gs://", "").split("/")[0]
    destination_blob_name = "/".join(gcs_path.replace("gs://", "").split("/")[1:])

    # Extract file name
    file_name = os.path.basename(local_path)  # Ensures correct filename extraction
    destination_blob_name = destination_blob_name.rstrip('/') + '/' + file_name  # Ensure proper path

    if verbose:
        print(f"Uploading {local_path} to gs://{bucket_name}/{destination_blob_name}...")

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"

    if verbose:
        print(f"✅ Report uploaded successfully. View at: {public_url}")

    return public_url
