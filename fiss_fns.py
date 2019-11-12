import json
import sys
import logging
import tenacity as tn
from firecloud import api as fapi
from firecloud import errors as ferrors

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

@tn.retry(wait=tn.wait_chain(*[tn.wait_fixed(1)] +
                       [tn.wait_fixed(5)] +
                       [tn.wait_fixed(10)] +
                       [tn.wait_fixed(30)] +
                       [tn.wait_fixed(60)]),
          stop=tn.stop_after_attempt(5),
          before_sleep=my_before_sleep)
def call_fiss(fapifunc, okcode, *args, **kwargs):
    ''' call FISS (firecloud api), check for errors, return json response

    function inputs:
        fapifunc : fiss api function to call, e.g. `fapi.get_workspace`
        okcode : fiss api response code indicating a successful run
        *args : args to input to api call
        **kwargs : kwargs to input to api call

    function returns:
        response.json() : json response of the api call

    example use:
        output = call_fiss(fapi.get_workspace, 200, 'help-gatk', 'Sequence-Format-Conversion')
    '''
    # call the api 
    response = fapifunc(*args, **kwargs) 

    # check for errors; this is copied from _check_response_code in fiss
    if type(okcode) == int:
        codes = [okcode]
    if response.status_code not in codes:
        print(response.content)
        raise ferrors.FireCloudServerError(response.status_code, response.content)

    # return the json response if all goes well
    return response.json()


if __name__ == "__main__":

    test_func = fapi.get_workspace
    okcode_correct = 200
    okcode_error = 201

    # this should work
    output = call_fiss(test_func, okcode_correct, 'help-gatk', 'Sequence-Format-Conversion')
    print(output['workspace']['bucketName'])

    # this should not work
    output = call_fiss(test_func, okcode_error, 'help-gatk', 'Sequence-Format-Conversion')
