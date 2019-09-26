import requests
import json
import csv
import os
import pprint
import subprocess
from firecloud import api as fapi
from dataclasses import dataclass
from workspace_test_report import list_notebooks
from ws_class import Wspace

# @dataclass
# class FeaturedWs:
#     '''Class for keeping track of info for Featured Terra workflows.'''
#     project: str      
#     name: str
#     workflows: str = None
#     notebooks: str = None
#     has_wf: bool = False
#     has_nb: bool = False
#     status: str = None
#     report_path: str = None




def get_fw_json():
    request_url = 'https://storage.googleapis.com/firecloud-alerts/featured-workspaces.json'
    fws_json = requests.get(request_url).json()

    return fws_json


def format_fws(get_info=False, verbose=True):
    ''' format json file of featured workspaces into ws class
    '''
    # call api
    fws_json = get_fw_json()

    fws = {}


    for ws in fws_json:
        ws_project = ws['namespace']
        ws_name = ws['name']

        if verbose:
            print(ws_name + '\t (billing project: ' + ws_project + ')')
        
        ### load into Wspace class object
        fw = Wspace(workspace = ws_name,
                    project = ws_project) 

        if get_info:
            ### Extract workflows
            res_wf = fapi.list_workspace_configs(ws_project, ws_name, allRepos = True)
            fapi._check_response_code(res_wf, 200)

            wfs = []
            for wf in res_wf.json():
                wf_name = wf['name']
                wfs.append(wf_name)
            
            if len(wfs) > 0:
                if verbose:
                    print('\tWorkflows:')
                    print('\t\t'+'\n\t\t'.join(wfs))
            else:
                wfs = None

            ### Extract notebooks
            nbs = list_notebooks(ws_project, ws_name)
            
            if len(nbs) > 0:
                if verbose:
                    print('\tNotebooks: ')
                    print('\t\t'+'\n\t\t'.join(nbs))
            else:
                nbs = None

            # save workflows and notebooks to Wspace 
            fw.workflows = wfs
            fw.notebooks = nbs

        fws[fw.key] = fw

    return fws


def get_fw_tsv(get_info, verbose):
    fws = format_fws(get_info, verbose)

    fws_file = '/tmp/fws.tsv'
    with open(fws_file, 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        if get_info:
            tsv_writer.writerow(['name', 'project', 'workflows', 'notebooks'])
            for fw in fws.values():
                tsv_writer.writerow([fw.workspace, fw.project, fw.workflows, fw.notebooks])
        else:
            tsv_writer.writerow(['name', 'project'])
            for fw in fws.values():
                tsv_writer.writerow([fw.workspace, fw.project])

    return fws_file


if __name__ == '__main__':

    open_file = True

    fws_file = get_fw_tsv(get_info=False, verbose=True)

    if open_file:
        os.system('open ' + fws_file)
