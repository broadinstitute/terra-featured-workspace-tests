import os
import argparse
from workspace_test_report import *
from get_fws import *
# from ws_class import Wspace




# TODO: implement unit tests, use wiremock - to generate canned responses for testing with up-to-date snapshots of errors

# def test_all_fw(clone_project, base_path, sleep_time=60, verbose=True):
#     ''' clone and run tests on ALL featured workspaces
#     '''

#     # collect list of all featured workspaces (and their billing projects)
#     fws = format_fws(verbose) # this returns a list of featured_ws class objects
#     master_ws_list = []
#     for ws in fws.values()[:2]: # test on the first 2 featured ws for now
#         processed_ws = test_single_ws(ws.name, ws.project, clone_project, base_path, sleep_time)
#         master_ws_list.append(processed_ws)
    
#     # make the html output
#     report_path = generate_master_report(master_ws_list, base_path, verbose)

#     return report_path



def generate_master_report(gcs_path, verbose=False):
    ''' generate a report that lists all tested workspaces, the test result,
    and links to each workspace report.
    '''
    if verbose:
        print('\nGenerating master report from '+gcs_path)

    workspaces_text = ''

    # get list of reports in gcs bucket
    system_command = "gsutil ls " + gcs_path
    all_paths = os.popen(system_command).read()

    # get the list of featured workspaces
    fws_dict = format_fws(get_info=False, verbose=False)

    fws_keys = fws_dict.keys()

    finished_report_keys = []
    # parse a list of the report names
    for f in all_paths.split('\n'):
        if '.html' in f:
            # kludgy for now, but pull out workspace name and report path from the full bucket path
            ws_name = f.replace(gcs_path,'')
            ws_orig = ''.join(ws_name.split('_')[:-1]) # the original featured workspace name

            if len(ws_orig)>0: # in case of empty string
                for key in fws_keys:
                    if ws_orig in key:
                        finished_report_keys.append(key)
                        # populate the Wspace class with report_path
                        fws_dict[key].report_path = f.replace('gs://','https://storage.googleapis.com/')


    # generate text for report

    workspaces_text = ''

    for key in finished_report_keys:
        workspaces_text += '''<a href=''' + fws_dict[key].report_path + ''' target='_blank'>''' + fws_dict[key].workspace + '''</a>'''
        workspaces_text += '<br><br>'

    
    report_name = 'master_report.html'
    local_path = '/tmp/' + report_name
    # open, generate, and write the html text for the report
    f = open(local_path,'w')
    message = '''<html>
    <head><link href='https://fonts.googleapis.com/css?family=Lato' rel='stylesheet'>
    </head>
    <body style='font-family:'Lato'; font-size:18px; padding:30; background-color:#FAFBFD'>
    <p>
    <center><div style='background-color:#82AA52; color:#FAFBFD; height:100px'>
    <h1>
    <img src='https://app.terra.bio/static/media/logo-wShadow.c7059479.svg' alt='Terra rocks!' style='vertical-align: middle;' height='100'>
    <span style='vertical-align: middle;'>
    Featured Workspace Report: Master list</span></h1></center></div>
  
    <br><br>
    <h2>Workspaces:</h2>
    ''' + workspaces_text + '''
    <br>
    </p>

    </p></body>
    </html>'''

    f.write(message)
    f.close()

    # upload report to google cloud bucket
    report_path = upload_to_gcs(local_path, gcs_path, verbose)

    return report_path


def test_all(args):
    # WIP
    # get list of all Featured Workspaces
    fws = format_fws(verbose = args.verbose)

    fws_testing = {}
    # run tests on all of them
    for ws in fws.values():
        print(ws.key)
        fws_testing[ws.key] = clone_workspace(ws.project, ws.workspace, args.clone_project, args.verbose)

    # create and monitor submissions
    clone_ws.run_workflow_submission(sleep_time, verbose)
    # if verbose:
    #     print(clone_ws.tested_workflows)

    # generate workspace report
    clone_ws.generate_workspace_report(gcs_path, verbose)

    return clone_ws


    # open the master report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--test_all', '-a', action='store_true', help='test all Featured Workspaces')

    parser.add_argument('--clone_name', type=str, help='name of cloned workspace')
    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--original_name', type=str, default='Sequence-Format-Conversion', help='name of workspace to clone')
    parser.add_argument('--original_project', type=str, default='help-gatk', help='project for original workspace')

    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--html_output', type=str, default='workspace_report.html', help='address to create html doc for report')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')


    # these things are quasi-unit tests:
    parser.add_argument('--do_submission', action='store_true', help='run the workflow submission')
    parser.add_argument('--test_notebook', action='store_true', help='test notebooks')
    parser.add_argument('--test_fail', action='store_true', help='run a report on a failed submission')
    parser.add_argument('--test_master', action='store_true', help='run a master report on everything in the google bucket')
    
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()


    # # testing, for now
    # clone_name = args.clone_name # this is None unless you entered one
    # if args.test_fail:
    #     clone_name = 'do not clone'
    # if args.test_notebook:
    #     clone_name = 'do not clone'

    if args.test_all:
        test_all(args)
    
    else:
        if args.do_submission:
            run_workflow_submission(args.clone_project, clone_name, args.sleep_time, args.verbose)

        if args.test_notebook: # work in progress!
            # # # clone a workspace that has notebooks
            # args.original_project = 'fc-product-demo'
            # args.original_name = 'Terra_Quickstart_Workspace'
            # clone_name = clone_workspace(args.original_project, args.original_name, args.clone_project)
            
            clone_name = 'Terra_Quickstart_Workspace_2019-09-03-15-19-28'

            run_workflow_submission(args.clone_project, clone_name, args.sleep_time, args.verbose)
            run_notebook_submission(args.clone_project, clone_name, args.verbose)
    
        if args.test_fail:
            # this submission has failures
            project = 'fccredits-curium-coral-4194'
            workspace = 'Germline-SNPs-Indels-GATK4-b37-EX06test'

            # # this submission has failures and successes
            # project = 'featured-workspace-testing'
            # workspace = 'Germline-SNPs-Indels-GATK4-hg38_2019-08-20-14-11-56'
        # else:
        #     project = args.clone_project
        #     workspace = clone_name

        if args.test_master:
            report_path = generate_master_report(args.gcs_path, args.verbose)
            os.system('open ' + report_path)
        else:
            # run the report and open it
            html_output, status = generate_workspace_report(project, workspace, args.gcs_path, args.verbose)
            os.system('open ' + html_output)




        # # test the master report

        # master_ws_list = []
        # master_ws_list.append(Wspace(workspace = 'clone_name1',
        #                             project = 'clone_project1',
        #                             workflows = ['finished_workflows1'],
        #                             status='FAILURE!',
        #                             report_path='some_path1.html'))
        # master_ws_list.append(Wspace(workspace = 'clone_name2',
        #                             project = 'clone_project2',
        #                             workflows = ['finished_workflows2'],
        #                             status='SUCCESS!',
        #                             report_path='some_path2.html'))
        # report_path = generate_master_report(master_ws_list, '/tmp/', verbose=True)
        # os.system('open ' + report_path)