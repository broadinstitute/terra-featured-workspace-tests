import argparse
import re

from firecloud import api as fapi

from fiss_fns import call_fiss


def cleanup_workspaces(project, match_str=None, age_days=None, verbose=True):
    if verbose:
        print('searching for workspaces to clean up')

    # hard code any cloned workspaces we do NOT want to delete
    do_not_delete_workspaces = []

    # get a list of all workspaces in the project
    ws_json = call_fiss(fapi.list_workspaces, 200, fields='workspace.name,workspace.namespace')
    ws_all = []
    for ws in ws_json:
        ws_project = ws['workspace']['namespace']
        ws_name = ws['workspace']['name']
        if ws_project == project:
            ws_all.append(ws_name)

    if verbose:
        print(str(len(ws_all)) + ' workspaces found in project ' + project)

    ws_to_delete = {ws for ws in ws_all if
                    ws not in do_not_delete_workspaces and re.search(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$", ws)}

    # delete those old workspaces
    n_total = len(ws_to_delete)
    n_done = 0
    if verbose:
        print(f"Found {n_total} workspaces to delete")
    for ws in ws_to_delete:
        n_done += 1
        call_fiss(fapi.delete_workspace, 202, project, ws,
                  specialcodes=[404])  # a 404 means the workspace isn't found - already deleted
        if verbose:
            print(ws + ' deleted (' + str(n_done) + '/' + str(n_total) + ')')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--age_days', type=int, default=None, help='delete workspaces > age_days; enter -1 for all')
    parser.add_argument('--match_str', type=str, default=None, help='delete workspaces containing this string')
    parser.add_argument('--project', type=str, default='featured-workspace-testing',
                        help='delete workspaces only in this billing project')

    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    cleanup_workspaces(args.project, args.match_str, args.age_days, verbose=True)
