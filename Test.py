import os
import argparse
from workspace_test_report import *
from get_fws import format_fws
from ws_class import Wspace




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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--clone_name', type=str, help='name of cloned workspace')
    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--original_name', type=str, default='Sequence-Format-Conversion', help='name of workspace to clone')
    parser.add_argument('--original_project', type=str, default='help-gatk', help='project for original workspace')

    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--html_output', type=str, default='workspace_report.html', help='address to create html doc for report')
    # parser.add_argument('--base_path', type=str, default='/tmp/', help='path or folder where reports will be generated')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')


    # these things are quasi-unit tests:
    parser.add_argument('--do_submission', action='store_true', help='run the workflow submission')
    parser.add_argument('--test_notebook', action='store_true', help='test notebooks')
    parser.add_argument('--test_fail', action='store_true', help='run a report on a failed submission')
    
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()


    # testing, for now
    clone_name = args.clone_name # this is None unless you entered one
    if args.test_fail:
        clone_name = 'do not clone'
    if args.test_notebook:
        clone_name = 'do not clone'

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
    else:
        project = args.clone_project
        workspace = clone_name

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