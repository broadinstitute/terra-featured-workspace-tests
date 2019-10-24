# terra-featured-workspace-tests
This code is to test that Terra Featured Workspaces are working properly. 

Note: Currently this code tests all workflows within a Featured Workspace, but it does not test notebooks.

### Quickstart
To run a test of **all Featured Workspaces** (everything [here](https://app.terra.bio/#library/showcase)), from the command line, run:
`python3 featured_workspaces_test.py -v`
- the `-v` flag (for verbose) will print progress

To run a test on a **single workspace**, from the command line, run:
`python3 workspace_test_report.py -v --original_name [name of workspace] --original_project [billing project]`
For example:
`python3 workspace_test_report.py -v --original_name Sequence-Format-Conversion --original_project help-gatk`
- note that the default setting for original_project is already 'help-gatk'


### The test on an individual workspace proceeds as follows:
- clone the Featured Workspaces you want to test
    - this generates a Wspace class (in ws_class.py)
- run workflow submissions for each workflow in the workspace
- query the job history of the completed submissions and generate a report
- publish the report to a google bucket and set permissions to be viewable by anyone
    - the default google bucket is gs://dsp-fieldeng/fw_reports/



### Possible future improvements:
- Add notebook functionality - currently this is an empty function
- Add an optional json configuration input that allows the user to configure the test more specifically for a particular workspace, e.g. only run certain workflows, run on specific data entities, run workflows sequentially vs in parallel