from datetime import datetime
import json
import time
from firecloud import api
# import pprint

# # for troubleshooting
# pp = pprint.PrettyPrinter(indent=4)

def cleanup_workspaces(project, age_days, verbose=False):
    
    # hard code any cloned workspaces we do NOT want to delete
    exceptions = []
    
    # get a list of all workspaces in the project
    ws_json = api.list_workspaces().json()
    ws_all = []
    for ws in ws_json:
        ws_project = ws["workspace"]["namespace"]
        ws_name = ws["workspace"]["name"]
        if ws_project == project:
            ws_all.append(ws_name)

    FMT = "%Y-%m-%d-%H-%M-%S"       # datetime format used in workspace_test_report.py > clone_workspace()
    
    # select the cloned workspaces older than [age_days] ago
    ws_to_delete = []   # collect workspace names to delete in a list
    for ws in ws_all:
        # pull out the clone date and determine how many days ago the clone was made
        clone_date = ws.split('_')[-1]
        try:
            tdelta = datetime.now() - datetime.strptime(clone_date, FMT)
            tdelta_days = tdelta.days
        except: # if the workspace doesn't contain a datetime string, i.e. it wasn't cloned by us
            tdelta_days = -1
        
        if verbose:
            print(ws +" is " + str(tdelta_days)+ " days old")

        # add workspace to the delete list if it's more than [age_days] old and not in our list of exceptions
        if tdelta_days > age_days:
            if ws not in exceptions:
                ws_to_delete.append(ws)
    
    # delete those old workspaces
    for ws in ws_to_delete:
        api.delete_workspace(project, ws)
        if verbose:
            print(ws + " deleted")




if __name__ == "__main__":

    project = "featured-workspace-testing"
    age_days = -1 # in days

    cleanup_workspaces(project, age_days, verbose=True)