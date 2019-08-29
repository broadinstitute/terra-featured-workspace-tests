class wflow:
    def __init__(self, wfid, name, entity, status, message, link):
        self.wfid = wfid
        self.name = name
        self.entity = entity
        self.status = status
        self.message = message
        self.link = link

workflows = {}
for i in range(3):
    wfid = "wfid_"+str(i)
    workflows[wfid] = (wflow(wfid=wfid,
                      name="test",
                      entity="data",
                      status="awesome",
                      message="hello there",
                      link="some kinda link"))
    

print(workflows)