import argparse
import csv
import os

import requests
from firecloud import api as fapi

from fiss_api_addons import get_workspace_cloudPlatform
from fiss_fns import call_fiss
from workspace_test_report import list_notebooks, clone_workspace
from ws_class import Wspace


def get_fws_dict_from_folder(gcs_path, test_master_report, clone_project, verbose=True):
    ''' note this will NOT work except on a mac 
    '''
    # generate a master report from a folder of workspace reports that have already been run
    report_folder = gcs_path + test_master_report

    # make sure the folder name is formatted correctly
    report_folder = report_folder.rstrip('/')

    # get list of reports in gcs bucket
    system_command = "gsutil ls " + report_folder
    all_paths = os.popen(system_command).read()

    # pull out info
    fws_dict = {}

    for path in all_paths.split('\n'):
        ws_name = path.replace('.html', '').replace(report_folder + '/', '')
        ws_orig = ''.join(ws_name.split('_')[:-1])  # the original featured workspace name

        if verbose:
            print(ws_name)

        if len(ws_orig) > 0:  # in case of empty string
            system_command = 'gsutil cat ' + path
            contents = os.popen(system_command).read()

            for line in contents.split('\n'):
                # get original billing project
                if 'Billing Project:' in line:
                    project_orig = line.split('</b>')[-1].replace('</big>', '')

                # get workspace test status
                if 'SUCCESS!' in line:
                    status = 'SUCCESS!'
                elif 'FAILURE!' in line:
                    status = 'FAILURE!'

            key = project_orig + '/' + ws_orig

            fws_dict[key] = Wspace(workspace=ws_name,
                                   project=clone_project,
                                   workspace_orig=ws_orig,
                                   project_orig=project_orig,
                                   status=status,
                                   report_path=path.replace('gs://', 'https://storage.googleapis.com/'))

    return fws_dict


def get_fw_json():
    request_url = 'https://storage.googleapis.com/firecloud-alerts/featured-workspaces.json'
    fws_json = requests.get(request_url).json()

    return fws_json


def get_cloudPlatform(namespace, name):
    """get cloud platform of workspace"""
    fws_response = get_workspace_cloudPlatform(namespace, name)
    if fws_response.status_code != 200:
        print(f'Error retrieving workspace information for workspace {namespace}/{name}')
        print(fws_response.text)

    fws_cloudplatform = fws_response.json()
    try:
        return fws_cloudplatform['workspace']['cloudPlatform']
    except KeyError:
        print(f'Error retrieving workspace information for workspace {namespace}/{name} -> {fws_response.text}')
        pass


def format_fws(get_info=False, verbose=True):
    ''' format json file of featured workspaces into dictionary of workspace classes 
    '''
    # call api
    fws_json = get_fw_json()

    fws = {}

    for ws in fws_json:
        ws_project = ws['namespace']
        ws_name = ws['name']

        try:
            cloudplatform = get_cloudPlatform(ws_project, ws_name)
        except Exception as e:
            print(f'Error retrieving workspace information for workspace {ws_project}/{ws_name}')
            print(e)
            continue

        if cloudplatform == 'Azure':
            print(f'Skipping Azure workspace {ws_project}/{ws_name}')
            continue

        if ws_project == 'broad-firecloud-dsde-methods' and ws_name == 'GATK-Structural-Variants-Joint-Calling':
            print(f'Skipping {ws_project}/{ws_name} for cost savings (FE-359)')
            continue

        if verbose:
            print(ws_name + '\t (billing project: ' + ws_project + ')')

        ### load into Wspace class object
        fw = Wspace(workspace=ws_name,
                    project=ws_project)

        if get_info:
            ### Extract workflows
            res_wf = call_fiss(fapi.list_workspace_configs, 200, ws_project, ws_name, allRepos=True)

            wfs = []
            for wf in res_wf:
                wf_name = wf['name']
                wfs.append(wf_name)

            if len(wfs) > 0:
                if verbose:
                    print('\tWorkflows:')
                    print('\t\t' + '\n\t\t'.join(wfs))
            else:
                wfs = None

            ### Extract notebooks
            nbs = list_notebooks(ws_project, ws_name, ipynb_only=True)

            if len(nbs) > 0:
                if verbose:
                    print('\tNotebooks: ')
                    print('\t\t' + '\n\t\t'.join(nbs))
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


def clone_all_fws():
    # clone all featured workspaces 

    clone_project = 'update-fw-bucket-paths-backup'
    clone_string = 'BACKUP'

    featured_ws_dict = format_fws()

    for ws in featured_ws_dict.values():
        clone_ws = clone_workspace(ws.project, ws.workspace, clone_project,
                                   clone_time=clone_string, verbose=True, copy_bucket=True)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--get_info', action='store_true', help='pulls the names of notebooks and workflows')
    parser.add_argument('--output_format', '-of', default='dict', help='formating the output file to tsv or dictionary')
    parser.add_argument('--open_file', '-o', action='store_true',
                        help='open the tsv file listing all of the workspaces')
    parser.add_argument('--clone_all', action='store_true', help='clone all featured workspaces')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/',
                        help='google bucket path to save reports')
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()

    if args.clone_all:
        clone_all_fws()
    else:
        if args.output_format == 'dict':
            fws = format_fws(args.get_info, args.verbose)
        elif args.output_format == 'tsv':
            fws_file = get_fw_tsv(args.get_info, args.verbose)
            if args.open_file:
                os.system('open ' + fws_file)
        else:
            print("output string not recognized, set --output_format to 'dict' or 'tsv'")
