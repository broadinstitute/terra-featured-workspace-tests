# terra-featured-workspace-tests
This code is to test that terra featured workspaces are working properly 

The main code to run is in Test.py, which will call functions from workspace_test_report.py and wflow_class.py.
This code should be compatible with Python2 and Python3.

### The full test proceeds as follows:
- clone the Featured Workspace you want to test (function clone_workspace)
- run workflow submissions for each workflow in the workspace (function run_workflow_submission)
- query the job history of the completed submissions and generate a report (function generate_workspace_report)
    - the report currently is printed to a temporary local html file

The above steps can be performed as a whole or individually/separately, depending on the input arguments to Test.py. For example:

**To run the full sequence**, enter:
`python3 Test.py --original_name [name of workspace to clone] --original_project [project of workspace to clone] --do_submission -v`

**To run new workflow submissions on a cloned workspace**, enter:
`python3 Test.py --clone_name [name of cloned workspace] --do_submission -v`

**To run a report on completed workflow submissions**, enter:
`python3 Test.py --clone_name [name of cloned workspace] -v`


### Input argument info & defaults:
`--clone_name` 
- this allows you to specify a workspace that's already been cloned; if not specified, then the workspace will be freshly cloned
- no default

`--clone_project` 
- this should not need to be changed
- default="featured-workspace-testing"

`--original_name` 
- specify the workspace to be tested
- default="Sequence-Format-Conversion"

`--original_project` 
- specify the project of the workspace to be tested
- default="help-gatk"


`--do_submission` 
- run the workflows
- default=False

`--do_order`
- run workflows sequentially in order (waiting for one to finish before submitting the next) 
- default=False

`--sleep_time` 
- time (in seconds) to wait before checking whether a submission has completed. for workflows that take a long time, this could be set to much longer
- default=100

`--html_output` 
- path to write the report
- default="/tmp/workspace_report.html"


`--test_notebook` 
- a test for running notebooks - currently not working
- default=False 

`--test_fail` 
- a test to create a report from a workspace that has failures
- default=False

`--verbose, -v` 
- flag to print out progress text and extra info in the terminal
- default=False



### Planned improvements:
- Add notebook functionality - currently this is an empty function
- Add an optional json configuration input that allows the user to configure the test more specifically for a particular workspace, e.g. only run certain workflows, run on specific data entities, run workflows sequentially vs in parallel