import os
class wflow:
    def __init__(self, workspace, project, wfid, subid, wfname, entity, status, message=None):
        self.workspace = workspace
        self.project = project
        self.wfid = wfid            # workflow id
        self.subid = subid          # submission id
        self.wfname = wfname        # workflow name
        self.entity = entity
        self.status = status
        self.message = message
        if wfid:
            self.link = "https://job-manager.dsde-prod.broadinstitute.org/jobs/"+ str(wfid)
        else:
            self.link = "https://app.terra.bio/#workspaces/" + project + "/" + workspace + "/job_history/" + subid
            
    

    
    def get_HTML(self):

        if self.status == "Failed":
            status_color = "red"
            error_message = "<br>" + str(self.message)
        elif self.status == "Aborted":
            status_color = "orange"
            error_message = ""
        else:
            status_color = "green"
            error_message = ""


        message_html = """
        Workflow Id: {wfid}
        <br>Submission Id: {subid}
        <br>Entity Name: {entity}
        <br>Status: <font color={status_color}>{status}{error_message}</font>
        <br><a href={link} target="_blank">Click Here For More Details</a>
        <br><br>
        """
        message_html = message_html.format(wfname = self.wfname, 
                            wfid = self.wfid,
                            subid = self.subid,
                            entity = self.entity,
                            status_color = status_color,
                            status = self.status,
                            error_message = error_message,
                            link = self.link)
        return message_html

if __name__ == "__main__":
    workflow_dict = {}
    workflow_dict["1"]=wflow(wfid="1", project="project", workspace="workspace", subid="a", wfname="first", entity="entity", status="Failed", message="None")
    workflow_dict["2"]=wflow(wfid="2", project="project", workspace="workspace", subid="b", wfname="second", entity="entity", status="Success")
    workflow_dict["3"]=wflow(wfid="3", project="project", workspace="workspace", subid="c", wfname="third", entity="entity", status="Failed", message="Yes")
    html_list = []
    for items in workflow_dict.values():
        html_list.append(items.get_HTML())

    html_add = "<br><br>".join(html_list)
    
    f = open('/tmp/hello.html','w')
    message = "<html><body><p>" + html_add + "</p></body></html>"
    f.write(message)
    f.close()
    os.system("open /tmp/hello.html")