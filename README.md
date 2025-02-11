# TERRA FEATURED WORKSPACES TESTS
This code is to test that Terra Featured Workspaces are working properly. It generates individual reports for each workspace, as well as a master report listing all the tested workspaces with links to their individual reports. The reports live in a google bucket and are publicly viewable.

Note: Currently this code tests all workflows within a Featured Workspace, but it does not test notebooks.

### Development Notes

1. Tests are divided in 4 batches, there exists this parameter in code `batch_size = 18` that needs to be changed if number of featured workspaces. 
2. The tests run periodically every 14 days, but you can dispatch manually through Workflow Dispatcher

### Quickstart
Prerequisites: You will need python3 and may need to install some packages if you don't have them already. After installing python3 and pip3, you can import packages needed to run these scripts using `sudo pip3 install dataclasses firecloud tenacity`. Alternately, use a Docker instead.


To run a test of **all Featured Workspaces** (everything [here](https://app.terra.bio/#library/showcase)), from the command line, run:

    python3 featured_workspaces_test.py -v
- the `-v` flag (for verbose) will print progress

To run a test on a **single workspace**, from the command line, run:

    python3 workspace_test_report.py -v --original_name [name of workspace] --original_project [billing project]

For example:

    python3 workspace_test_report.py -v --original_name Sequence-Format-Conversion --original_project help-gatk
- note that the default setting for original_project is already 'help-gatk'

### Quickstart with Docker image
Enter Docker image interactively:

    docker run --rm -it -v "$HOME"/.config:/.config -v $PWD:/scripts broadinstitute/terra-featured-workspace-tests:latest

Then run test on all workspaces:

    python3 scripts/featured_workspaces_test.py -v


Or, run it all in Docker:

    docker run --rm -v "$HOME"/.config:/.config -v $PWD:/scripts broadinstitute/terra-featured-workspace-tests:latest python3 -u scripts/featured_workspaces_test.py -v

### Cleanup
To delete workspaces, use `cleanup_workspaces.py`. 
- You can delete all workspaces older than x days using `--age_days x` 
(and to delete all workspaces, use `--age_days -1`). 
- You can delete all workspaces whose name contains a string using `--match_str [string to match]`

For example, this line will delete all workspaces created in the 2019-10-23-17-48-44 test:
    python3 cleanup_workspaces.py --match_str 2019-10-23-17-48-44


Or using Docker:
    docker run --rm -v "$HOME"/.config:/.config -v $PWD:/scripts broadinstitute/terra-featured-workspace-tests:latest python3 -u scripts/cleanup_workspaces.py -v --match_str 2019-10-23-17-48-44


### The test on an individual workspace proceeds as follows:
- clone the Featured Workspaces you want to test
    - this generates a Wspace class (in ws_class.py)
- run workflow submissions for each workflow in the workspace
- query the job history of the completed submissions and generate a report
- publish the report to a google bucket and set permissions to be viewable by anyone
    - the default google bucket, which you can change using the `--gcs_path` flag, is [gs://terra-featured-workspace-tests-reports/fw_reports/](https://console.cloud.google.com/storage/browser/terra-featured-workspace-tests-reports/fw_reports/)



### Possible future improvements:
- Add notebook functionality - currently this is an empty function
- Add an optional json configuration input that allows the user to configure the test more specifically for a particular workspace, e.g. only run certain workflows, run on specific data entities, run workflows sequentially vs in parallel
