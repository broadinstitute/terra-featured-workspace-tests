import requests
import json
import csv
import os
import pprint
import subprocess
from firecloud import api as fapi
from dataclasses import dataclass
from workspace_test_report import list_notebooks

@dataclass
class featured_ws:
    '''Class for keeping track of info for Featured Terra workflows.'''
    project: str      
    name: str
    workflows: str = None
    notebooks: str = None
    has_wf: bool = False
    has_nb: bool = False
    status: str = None
    report_path: str = None




def get_fw_json():
    request_url = 'https://storage.googleapis.com/firecloud-alerts/featured-workspaces.json'
    fws_json = requests.get(request_url).json()

    return fws_json


def format_fws(verbose=True):
    ''' format json file of featured workspaces into fws class
    '''
    # call api
    fws_json = get_fw_json()

    fws = []

    for ws in fws_json:
        ws_project = ws['namespace']
        ws_name = ws['name']

        if verbose:
            print(ws_name + '\t (billing project: ' + ws_project + ')')
        
        ### Extract workflows
        res_wf = fapi.list_workspace_configs(ws_project, ws_name, allRepos = True)

        # check for errors
        if res_wf.status_code != 200:
            print(res_wf.text)
            exit(1)

        wfs = []
        for wf in res_wf.json():
            wf_name = wf['name']
            wfs.append(wf_name)
        
        if len(wfs) > 0:
            has_wf = True
            if verbose:
                print('\tWorkflows:')
                print('\t\t'+'\n\t\t'.join(wfs))
        else:
            wfs = None
            has_wf = False

        ### Extract notebooks
        nbs = list_notebooks(ws_project, ws_name)
        
        if len(nbs) > 0:
            has_nb = True
            if verbose:
                print('\tNotebooks: ')
                print('\t\t'+'\n\t\t'.join(nbs))
        else:
            nbs = None
            has_nb = False



        ### load into featured_ws class object
        fw = featured_ws(ws_project, ws_name, 
                         workflows = wfs, has_wf = has_wf,
                         notebooks = nbs, has_nb = has_nb)
        fws.append(fw)

    return fws


def get_fw_tsv(verbose):
    fws = format_fws(verbose)

    fws_file = '/tmp/fws.tsv'
    with open(fws_file, 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow(['name', 'project', 'has_workflows', 'has_notebooks', 'workflows', 'notebooks'])
        for fw in fws:
            tsv_writer.writerow([fw.name, fw.project, fw.has_wf, fw.has_nb, fw.workflows, fw.notebooks])
            # if verbose:
            #     print(ws['namespace'] + '\t\t\t' + ws['name'])

    return fws_file


if __name__ == '__main__':

    open_file = True

    fws_file = get_fw_tsv(verbose = True)

    if open_file:
        os.system('open ' + fws_file)
