import requests
import json
import csv
import os
import pprint
import subprocess
import argparse
from firecloud import api as fapi
from dataclasses import dataclass
from workspace_test_report import list_notebooks
from ws_class import Wspace


def get_fw_json():
    request_url = 'https://storage.googleapis.com/firecloud-alerts/featured-workspaces.json'
    fws_json = requests.get(request_url).json()

    return fws_json


def format_fws(get_info=False, verbose=True):
    ''' format json file of featured workspaces into dictionary of workspace classes 
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
            nbs = list_notebooks(ws_project, ws_name, ipynb_only=True)
            
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
    ''' convert dictionary into a tsv file
    '''

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

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--get_info', action='store_true', help='pulls the names of notebooks and workflows')
    parser.add_argument('--output_format', '-of', default='dict', help='formating the output file to tsv or dictionary')
    parser.add_argument('--open_file','-o', action='store_true', help='open the tsv file listing all of the workspaces')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    if args.output_format == 'dict':
        fws = format_fws(args.get_info, args.verbose)
    elif args.output_format == 'tsv':
        fws_file = get_fw_tsv(args.get_info, args.verbose)
        if args.open_file:
            os.system('open ' + fws_file)
    else:
        print("output string not recognized, set --output_format to 'dict' or 'tsv'")
