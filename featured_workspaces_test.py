import os
import argparse
import time
from datetime import datetime
from workspace_test_report import clone_workspace
from get_fws import format_fws
from gcs_fns import upload_to_gcs
from ws_class import Wspace

# TODO: implement unit tests, use wiremock - to generate canned responses for testing with up-to-date snapshots of errors

def get_fws_dict_from_folder(args):
    ''' note this will NOT work except on a mac 
    '''
    # generate a master report from a folder of workspace reports that have already been run
    report_folder = args.gcs_path + args.test_master_report

    # make sure the folder name is formatted correctly
    if report_folder[-1] is '/':
        report_folder = report_folder[:-1]
    
    # get list of reports in gcs bucket
    system_command = "gsutil ls " + report_folder
    all_paths = os.popen(system_command).read()

    # pull out info
    fws_dict = {}

    for path in all_paths.split('\n'):
        ws_name = path.replace('.html','').replace(report_folder+'/','')
        ws_orig = ''.join(ws_name.split('_')[:-1]) # the original featured workspace name
        
        if args.verbose:
            print(ws_name)

        if len(ws_orig)>0: # in case of empty string
            system_command = 'gsutil cat ' + path
            contents = os.popen(system_command).read()

            for line in contents.split('\n'):
                # get original billing project
                if 'Billing Project:' in line:
                    project_orig = line.split('</b>')[-1].replace('</big>','')

                # get workspace test status
                if 'SUCCESS!' in line:
                    status = 'SUCCESS!'
                elif 'FAILURE!' in line:
                    status = 'FAILURE!'
            
            key = project_orig + '/' + ws_orig
                    
            fws_dict[key] = Wspace(workspace=ws_name,
                                    project=args.clone_project,
                                    workspace_orig=ws_orig,
                                    project_orig=project_orig,
                                    status=status,
                                    report_path=path.replace('gs://','https://storage.googleapis.com/'))

    return fws_dict


def generate_master_report(gcs_path, clone_time=None, ws_dict=None, verbose=False):
    ''' generate a report that lists all tested workspaces, the test result,
    and links to each workspace report.
    if ws_dict is passed, will use only the workspaces in the dict, 
    otherwise will return a report for all reports in the google bucket
    '''
    if verbose:
        if ws_dict is None:
            print('\nGenerating master report from '+gcs_path)
        else:
            print('\nGenerating master report')

    # define path for images
    # gcs_path_imgs = gcs_path.replace('gs://','https://storage.cloud.google.com/').replace('fw_reports/','imgs/')
    gcs_path_imgs = gcs_path.replace('gs://','https://storage.googleapis.com/').replace('fw_reports/','imgs/')
    print(gcs_path_imgs)

    fws_dict = ws_dict
    finished_report_keys = list(fws_dict.keys())

    # generate text for report
    workspaces_text = ''

    for key in finished_report_keys:

        # if there were ANY failures
        if 'FAIL' in fws_dict[key].status:
            status_color = 'red'
            status_text = '<img src="'+ gcs_path_imgs + 'fail.jpg" alt="FAILURE!" width=30>'
        elif 'SUCC' in fws_dict[key].status:
            status_color = 'green'
            status_text = '<img src="'+ gcs_path_imgs + 'success_kid.png" alt="SUCCESS!" width=30>'
        else:
            status_color = 'black'
            status_text = fws_dict[key].status

        workspaces_text += '''<big>{project}  /  {workspace} 
                    <font color={status_color}>{status}</font></big> 
                     ({n_wf} workflows tested) 
                    <a href={report_path} target='_blank'>[report]</a>
                    <br><br>
                    '''.format(project = fws_dict[key].project_orig,
                                workspace = fws_dict[key].workspace_orig,
                                status_color = status_color,
                                status = status_text,
                                n_wf = str(len(fws_dict[key].tested_workflows)),
                                report_path = fws_dict[key].report_path)
    
    if clone_time is None:
        report_name = 'master_report.html'
    else:
        report_name = 'master_report_'+clone_time+'.html'
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
    <h2>Workspaces tested:</h2>{workspaces_text}
    </p>

    <br><br>Test started: {clone_time}
    <br>Test finished: {done_time}
    </p></body>
    </html>'''

    message = message.format(workspaces_text = workspaces_text,
                            clone_time = clone_time,
                            done_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))

    f.write(message)
    f.close()

    # upload report to google cloud bucket
    report_path = upload_to_gcs(local_path, gcs_path, verbose)

    return report_path


def test_all(args):
    # make a folder for this set of tests (folder name is current timestamp)
    clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
    gcs_path_subfolder = args.gcs_path + clone_time + '/'

    # get dict of all Featured Workspaces
    fws = format_fws(verbose=False) 

    # # temporary for troubleshooting/testing
    # n_test = 1
    # copy_fws = {}
    # for key in fws.keys():
    #     if len(copy_fws) < n_test:
    #         copy_fws[key] = fws[key]
    # fws = dict(copy_fws)
    # print(fws.keys())


    fws_testing = {}
    # set up to run tests on all of them
    for ws in fws.values():
        # # FOR NOW (maybe forever): only test on help-gatk billing project workspaces!
        # if ws.project == 'help-gatk':
        clone_ws = clone_workspace(ws.project, ws.workspace, args.clone_project, clone_time=clone_time, verbose=args.verbose)
        clone_ws.create_submissions(verbose=args.verbose) # set up the submissions
        clone_ws.check_submissions(verbose=False) # start them
        fws_testing[ws.key] = clone_ws

    # monitor submissions
    break_out = False
    while not break_out:
        start = time.time() # to help not check too often
        if args.verbose:
            print('\n' + datetime.today().strftime('%H:%M') + ' status check:')
        count_done = 0

        # loop through all workspaces, do submissions / check status, and generate individual reports
        for clone_ws in fws_testing.values():
            if args.verbose:
                print('  ' + clone_ws.workspace + ':')
            
            # check status of all submissions
            if clone_ws.status is None:
                clone_ws.check_submissions()
                if len(clone_ws.active_submissions) == 0: # if all submissions in this workspace are DONE
                    # generate workspace report
                    clone_ws.generate_workspace_report(gcs_path_subfolder, args.verbose)
                    count_done += 1
            else:
                count_done += 1
                print('    ' + clone_ws.status)

        # track progress
        if args.verbose:
            print('Finished ' + str(count_done) + ' of ' + str(len(fws_testing)) + ' Featured Workspaces to be tested')
        
        if count_done == len(fws_testing): # if all the submissions in all workspaces are done 
            break_out = True
        else:
            # don't continue until at least args.sleep_time seconds have elapsed
            now = time.time()
            if now - start < args.sleep_time:
                time.sleep(args.sleep_time - (now - start))

    # generate & open the master report
    master_report_path = generate_master_report(args.gcs_path, clone_time=clone_time, ws_dict=fws_testing, verbose=args.verbose)
    os.system('open ' + master_report_path)

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    # parser.add_argument('--test_master_report', '-r', action='store_true', help='run master report on Featured Workspaces')
    parser.add_argument('--test_master_report', '-r', type=str, default=None, help='folder name in gcs bucket to use to generate report')

    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')

    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()
  

    
    if args.test_master_report is not None:
        fws_dict = get_fws_dict_from_folder(args)
        report_path = generate_master_report(args.gcs_path, 
                                            clone_time=args.test_master_report.replace('/',''), 
                                            ws_dict=fws_dict, 
                                            verbose=args.verbose)
        os.system('open ' + report_path)
    else:
        test_all(args)
    