import json
import time
import argparse
from datetime import datetime
from firecloud import api as fapi
from fiss_fns import call_fiss

def cleanup_workspaces(project, match_str=None, age_days=None, verbose=True):
    
    # hard code any cloned workspaces we do NOT want to delete
    exceptions = []
    
    # get a list of all workspaces in the project
    ws_json = call_fiss(fapi.list_workspaces, 200)
    ws_all = []
    for ws in ws_json:
        ws_project = ws['workspace']['namespace']
        ws_name = ws['workspace']['name']
        if ws_project == project:
            ws_all.append(ws_name)

    FMT = '%Y-%m-%d-%H-%M-%S'       # datetime format used in workspace_test_report.py > clone_workspace()
    
    # select the cloned workspaces older than [age_days] ago
    ws_to_delete = set()   # collect workspace names to delete in a set (to prevent duplicates)
    for ws in ws_all:
        if age_days is not None:
            # pull out the clone date and determine how many days ago the clone was made
            clone_date = ws.split('_')[-1]
            try:
                tdelta = datetime.now() - datetime.strptime(clone_date, FMT)
                tdelta_days = tdelta.days
            except: # if the workspace doesn't contain a datetime string, i.e. it wasn't cloned by us
                tdelta_days = -1

            # add workspace to the delete list if it's more than [age_days] old and not in our list of exceptions
            if tdelta_days > age_days:
                if ws not in exceptions:
                    ws_to_delete.add(ws)
                    if verbose:
                        print(ws +' is ' + str(tdelta_days)+ ' days old')

        if match_str is not None:
            # add workspace to the delete list if it contains the target string (match_str) and not in our list of exceptions
            if match_str in ws:
                if ws not in exceptions:
                    ws_to_delete.add(ws)
    
    # delete those old workspaces
    for ws in ws_to_delete:
        call_fiss(fapi.delete_workspace, 202, project, ws)
        if verbose:
            print(ws + ' deleted')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--age_days', type=int, default=None, help='delete workspaces > age_days; enter -1 for all')
    parser.add_argument('--match_str', type=str, default=None, help='delete workspaces containing this string')
    parser.add_argument('--project', type=str, default='featured-workspace-testing', help='delete workspaces only in this billing project')
    
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    cleanup_workspaces(args.project, args.match_str, args.age_days, args.verbose)