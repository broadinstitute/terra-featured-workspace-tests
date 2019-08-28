from datetime import datetime
from firecloud import api

# this will fail
namespace = "fccredits-curium-coral-4194"
workspace = "Germline-SNPs-Indels-GATK4-b37-EX06test"

# # this will succeed
# namespace = "fccredits-sodium-tan-9687"
# workspace = "Sequence-Format-Conversion_2019-08-28-14-54-18"


res = api.list_submissions(namespace, workspace)
res = res.json()
for item in res:
    count = 0
    Failed = False
    FailedMess = []
    Link = []
    for i in api.get_submission(namespace, workspace, item["submissionId"]).json()["workflows"]:
        count +=1
        if "workflowId" in i: 
            Link.append(str(count) + ". " + "https://job-manager.dsde-prod.broadinstitute.org/jobs/"+ str(i["workflowId"]))
            resworkspace = api.get_workflow_metadata(namespace, workspace, item["submissionId"], i["workflowId"]).json()
            if resworkspace["status"] == "Failed":
                for failed in resworkspace["failures"]:
                    for message in failed["causedBy"]:
                        if str(message["message"]) not in FailedMess:
                            FailedMess.append(str(count) + ". " + str(message["message"]))
                        Failed = True
        else:
            if i["status"] == "Failed":
                print(item["submissionId"])
                if "No Workflow Id" not in FailedMess:
                    FailedMess.append("No Workflow Id")
                Failed = True  
    
    print("End Results:")
    if Failed:
        print(str(item["methodConfigurationName"]) + " has failed. The error message is: \n \n -"  + "\n \n -".join(FailedMess))
        print("\n \n List of Links: - ")
        print("\n-".join(Link))
    else:
        print(str(item["methodConfigurationName"]) + " has run successfully.")
        print("\n \n List of Links: - ")
        print("\n-".join(Link))
    print("\n \n \n ")


if Failed:
    status_text = "FAILURE!"
    status_color = "red"
else:
    status_text = "SUCCESS!"
    status_color = "green"

K =  datetime.today().strftime('%H:%M-%m/%d/%Y') + "<br>"

f = open('hello.html','w')

message = """<html>
<head></head>
<body><p><center><h1>Terra's Feature Workspace Report</h1>
<h1><font color={status_color}>{status_text}</font></h1></center> 
<br><br>

Name for Feature Workspace:
<br><br> The Workflows Tested:
<br><br> The Notebooks Tested:

<br><br> {Ka} Cloning Workspace to:
<br><br> {Ka} Running:
<br><br> {Ka} ________ are all completed.
<br> Everything ran successfully!</p></body>
</html>"""

message = message.format(Ka = K, 
                        status_color = status_color,
                        status_text = status_text)
f.write(message)
f.close()
