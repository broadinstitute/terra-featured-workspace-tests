import os
class wflow:
    def __init__(self, wfid, name, entity, status, message=None):
        self.wfid = wfid
        self.name = name
        self.entity = entity
        self.status = status
        self.message = message
        self.link = "https://job-manager.dsde-prod.broadinstitute.org/jobs/"+ str(wfid)
    

    
    def get_HTML(self):

        if self.status == "Failed":
            status_color = "red"
            error_message = "<br>" + str(self.message)
        else:
            status_color = "green"
            error_message = ""

        message_html = """

        Name: {name}
        <br>Workflow Id: {wfid}
        <br>Entity Name: {entity}
        <br>Status: <font color={status_color}>{status}{error_message}</font>
        <br><a href={link}>Click Here For More Details</a>
        """
        message_html = message_html.format(name = self.name, 
                            wfid = self.wfid,
                            entity = self.entity,
                            status_color = status_color,
                            status = self.status,
                            error_message = error_message,
                            link = self.link)
        return message_html

if __name__ == "__main__":
    workflow_dict = {}
    workflow_dict["1"]=wflow(wfid="1", name="first", entity="entity", status="Failed", message="None")
    workflow_dict["2"]=wflow(wfid="2", name="second", entity="entity", status="Success")
    workflow_dict["3"]=wflow(wfid="3", name="third", entity="entity", status="Failed", message="Yes")
    html_list = []
    for items in workflow_dict.values():
        html_list.append(items.get_HTML())

    html_add = "<br><br>".join(html_list)
    
    f = open('/tmp/hello.html','w')
    message = "<html><body><p>" + html_add + "</p></body></html>"
    f.write(message)
    f.close()
    os.system("open /tmp/hello.html")