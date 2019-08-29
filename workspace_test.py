"""
Workspace_test.py is designed to clone and run Featured Workspaces,
Afterwards, the program generates an HTML report of failures and successes,
with links to their Workflow report(s) on Terra.bio
"""

from firecloud import api
from datetime import datetime
import json
import time

# TODO: add test.py things
methodNamesstr = ', '.join(workflow_names)
detailstr = "<br>".join(finish_workflows_details)
print(', '.join(workflow_names) + " all ran successfully!")

f = open('TerraFeatureWorkspaceReport.html','w')

message = """<html>
<head></head>
<body><p><center>Terra's Feature Workspace Report</center> <br>
<br>

Name for Feature Workspace: {Feature_Workspace}
<br><br> The Workflows Tested: {Workflows}
<br><br> The Notebooks Tested: 0
<br><br> Testing Project Name: {Project}
<br><br> Cloning Workspace to: {Clone_Workspace}
<br><br> Running: {Workflows}
<br><br> Details:
<br>{Details}
<br><br>Everything ran successfully!</p></body>
</html>"""

message = message.format(Feature_Workspace = original_name, 
                         Workflows = methodNamesstr, 
                         Project = clone_project, 
                         Clone_Workspace = clone_name, 
                         Details = detailstr)
f.write(message)
f.close()

