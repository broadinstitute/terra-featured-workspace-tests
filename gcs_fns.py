import os
import subprocess
import tenacity as tn
import logging
import sys


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

def my_before_sleep(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logger.log(
        loglevel, 'Retrying %s with %s in %s seconds; attempt #%s ended with: %s',
        retry_state.fn, retry_state.args, str(int(retry_state.next_action.sleep)), retry_state.attempt_number, retry_state.outcome)

@tn.retry(wait=tn.wait_chain(*[tn.wait_fixed(5)] +
                       [tn.wait_fixed(10)] +
                       [tn.wait_fixed(30)] +
                       [tn.wait_fixed(60)]),
          stop=tn.stop_after_attempt(5),
          before_sleep=my_before_sleep)
def run_subprocess(cmd, errorMessage):
    try:
        print("running command: " + cmd)
        return subprocess.check_output(
            cmd, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(errorMessage)
        print("Exited with " + str(e.returncode) + "-" + e.output)
        exit(1)

def convert_to_public_url(gs_input):
    return gs_input.replace('gs://','https://storage.googleapis.com/')

def upload_to_gcs(local_path, gcs_path, verbose=True):

    file_name = local_path.split('/')[-1] # this should be the name of the cloned workspace + '.html'

    # write file to google cloud 
    system_command = "gsutil cp " + local_path + " " + gcs_path
    os.system(system_command)

    # make file publicly accessible
    system_command = "gsutil acl ch -u AllUsers:R " + gcs_path + file_name
    os.system(system_command)

    # get report path (link to report on google cloud)
    public_path = convert_to_public_url(gcs_path)
    report_path = public_path + file_name

    if verbose:
        print("Report can be viewed at " + report_path)

    return report_path

