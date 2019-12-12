import os
import argparse
import time
from datetime import datetime
from workspace_test_report import clone_workspace
from get_fws import format_fws
from gcs_fns import upload_to_gcs, convert_to_public_url
from ws_class import Wspace
from firecloud import api as fapi
from fiss_fns import call_fiss
from cleanup_workspaces import cleanup_workspaces

# TODO: implement unit tests, use wiremock - to generate canned responses for testing with up-to-date snapshots of errors

def get_fws_dict_from_folder(gcs_path, test_master_report, clone_project, verbose=True):
    ''' note this will NOT work except on a mac 
    '''
    # generate a master report from a folder of workspace reports that have already been run
    report_folder = gcs_path + test_master_report

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
        
        if verbose:
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
                                    project=clone_project,
                                    workspace_orig=ws_orig,
                                    project_orig=project_orig,
                                    status=status,
                                    report_path=path.replace('gs://','https://storage.googleapis.com/'))

    return fws_dict


def get_cost_of_test(gcs_path, report_name, clone_project, verbose=True):
    clone_time = report_name.replace('master_report_','').replace('.html','')
    if verbose:
        print('generating cost report for '+report_name)


    # get the folder where the individual reports live
    report_folder = gcs_path + clone_time
    # get a list of the individual reports for this master report
    system_command = "gsutil ls " + report_folder
    all_paths = os.popen(system_command).read()

    # get a dict of all workspaces
    ws_to_check = get_fws_dict_from_folder(gcs_path, clone_time, clone_project, False)

    # get a list of all workspaces & projects
    ws_json = call_fiss(fapi.list_workspaces, 200)
    project_dict = {}
    for ws in ws_json:
        project_dict[ws['workspace']['name']] = ws['workspace']['namespace']
    names_with_spaces = [key for key in project_dict.keys() if ' ' in key]
    
    total_cost = 0
    # for each workspace, get a list of submissions run
    for ws in ws_to_check.values(): 
        # find unformatted workspace name (where spaces are really spaces)
        for key in names_with_spaces:
            if key.replace(' ','_') == ws.workspace:
                ws.workspace = key
        if verbose:
            print(ws.workspace)
        
        # get & store cost of each submission, and track total cost for the workspace in ws_cost
        ws_cost = 0
        submissions_json = call_fiss(fapi.list_submissions, 200, ws.project, ws.workspace)
        submissions_dict = {}
        for sub in submissions_json:
            wf_name = sub['methodConfigurationName']
            if verbose:
                print('  '+wf_name)
            subID = sub['submissionId']
            sub_json = call_fiss(fapi.get_submission, 200, ws.project, ws.workspace, subID, specialcodes=[404])
            if sub_json.status_code != 404: # 404 means submission not found
                sub_json = sub_json.json()
                cost = sub_json['cost']
                submissions_dict[wf_name] = '${:.2f}'.format(cost)
                total_cost += cost
                ws_cost += cost
                if verbose:
                    print('    cost '+'${:.2f}'.format(cost))

        ws.submissions_cost=submissions_dict
        ws.total_cost=ws_cost

    if verbose:
        print(str(len(ws_to_check)) + ' workspaces in report')
        print('${:.2f}'.format(total_cost))

    # format a report
    report_path = generate_cost_report(gcs_path, report_name, total_cost, ws_to_check, verbose)

    return report_path, total_cost


def generate_cost_report(gcs_path, report_name, total_cost, ws_dict, verbose=True):
    ''' generate a report that lists all tested workspaces, the test COST,
    and links to each workspace report for all workspaces in ws_dict
    '''
    if verbose:
        print('\nGenerating master cost report')


    # list reports in alphabetical order, with failed reports first
    finished_report_keys = sorted(ws_dict.keys())

    # generate text for report
    link = convert_to_public_url(gcs_path + report_name)
    total_cost_text = 'For Master Report <a href=' + link + '>' + report_name + '</a>' \
                        + '<br>Total cost: '+'${:,.2f}'.format(total_cost)
    
    table_style_text = '''
                    <style>
                    table {
                    font-family: Montserrat, sans-serif;
                    border-collapse: collapse;
                    width: 100%;
                    }
                    td, th {
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                    }
                    </style>
                    '''

    workspaces_text = '''
                    <table>
                    <col width="10%">
                    <col width="30%">
                    <tr>
                        <th>Orig. Project</th>
                        <th>Featured Workspace</th>
                        <th>Report link</th>
                        <th># Workflows</th>
                        <th>Total cost</th>
                        <th>Breakdown</th>
                    </tr>
                    '''
    for key in finished_report_keys:
        breakdown_text = ''
        for wf_name, cost in ws_dict[key].submissions_cost.items():
            breakdown_text += wf_name + ': ' + cost + '<br>'

        workspaces_text += '''
                            <tr>
                                <td>{project}</td>
                                <td><big>{workspace}</big></td>
                                <td><a href={report_path} target='_blank'>[open report for details]</a></td>
                                <td>{num_wf}</td>
                                <td>{ws_cost}</td>
                                <td>{breakdown_text}</td>
                            </tr>                        
                    '''.format(project = ws_dict[key].project_orig,
                                workspace = ws_dict[key].workspace_orig,
                                report_path = ws_dict[key].report_path,
                                num_wf = str(len(ws_dict[key].submissions_cost)),
                                ws_cost = '${:,.2f}'.format(ws_dict[key].total_cost),
                                breakdown_text = breakdown_text)
    workspaces_text += '</table>'

    
    
    message = '''<html>
    <head>
    {table_style_text}
    </head>
    <body style='font-family:Montserrat,sans-serif; font-size:18px; padding:30; background-color:#FAFBFD'>
    <p>
    <center><div style='background-color:#82AA52; color:#FAFBFD; height:100px'>
    <h1>
    <img src='https://app.terra.bio/static/media/logo-wShadow.c7059479.svg' alt='Terra rocks!' style='vertical-align: middle;' height='100'>
    <span style='vertical-align: middle;'>
    Featured Workspace Test Cost Report</span></h1></center></div>

    <br><center><big>{total_cost_text}</big></center>
    <br><br>
    {workspaces_text}<br>
    </p>
    </p></body>
    </html>'''

    message = message.format(table_style_text = table_style_text,
                            total_cost_text = total_cost_text,
                            workspaces_text = workspaces_text)

    
    
    # open, generate, and write the html text for the report
    local_path = '/tmp/' + report_name.replace('.html','_COST.html')
    f = open(local_path,'w')
    f.write(message)
    f.close()

    # upload report to google cloud bucket
    report_path = upload_to_gcs(local_path, gcs_path, verbose)

    return report_path

def generate_master_report(gcs_path, clone_time, report_name, ws_dict=None, verbose=False):
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
    gcs_path_imgs = gcs_path.replace('gs://','https://storage.googleapis.com/').replace('fw_reports/','imgs/')

    fws_dict = ws_dict

    # list reports in alphabetical order, with failed reports first
    failed_list = []
    succeeded_list = []
    fail_count = 0
    call_cached = None
    for key in fws_dict.keys():
        if 'FAIL' in fws_dict[key].status:
            fail_count += 1
            failed_list.append(key)
        else:
            succeeded_list.append(key)
        if call_cached is None: # only set this once
            call_cached = fws_dict[key].call_cache
    finished_report_keys = sorted(failed_list)+sorted(succeeded_list)

    # generate text for report
    fail_count_text = '<font color=red>'+str(fail_count)+'</font> failed, out of '+str(len(fws_dict))+' tested'
    
    # generate the call cache setting used for the test
    if call_cached:
        call_cache_text = 'Call Caching ON (enabled)'
    else:
        call_cache_text = 'Call Caching OFF (disabled)'

    table_style_text = '''
                    <style>
                    table {
                    font-family: Montserrat, sans-serif;
                    border-collapse: collapse;
                    width: 100%;
                    }
                    td, th {
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                    }
                    </style>
                    '''

    workspaces_text = '''
                    <table>
                    <col width="10%">
                    <col width="30%">
                    <col width="5%">
                    <col width="5%">
                    <tr>
                        <th>Project</th>
                        <th>Featured Workspace</th>
                        <th># WFs tested</th>
                        <th>Status</th>
                        <th>Report link</th>
                        <th>Failed Workflows</th>
                        <th>Runtime</th>
                    </tr>
                    '''
    for key in finished_report_keys:
        # if there were ANY failures
        if 'FAIL' in fws_dict[key].status:
            status_color = 'red'
            status_text = '<img src="'+ gcs_path_imgs + 'fail.jpg" alt="FAILURE!" title="sucks to suck!" width=30>'
            failures_list = fws_dict[key].generate_failed_list()
        elif 'SUCC' in fws_dict[key].status:
            status_color = 'green'
            status_text = '<img src="'+ gcs_path_imgs + 'success_kid.png" alt="SUCCESS!" title="success kid is proud of you!" width=30>'
            failures_list = ''
        else:
            status_color = 'black'
            status_text = fws_dict[key].status
            failures_list = ''

        # generate the time elapsed for the test
        time_text = fws_dict[key].test_time

        workspaces_text += '''
                            <tr>
                                <td>{project}</td>
                                <td><big>{workspace}</big></td>
                                <td>{n_wf}</td>
                                <td><font color={status_color}>{status}</font></td>
                                <td><a href={report_path} target='_blank'>[open report for details]</a></td>
                                <td>{failures_list}</td>
                                <td>{runtime}</td>
                            </tr>                        
                    '''.format(project = fws_dict[key].project_orig,
                                workspace = fws_dict[key].workspace_orig,
                                status_color = status_color,
                                status = status_text,
                                n_wf = str(len(fws_dict[key].tested_workflows)),
                                report_path = fws_dict[key].report_path,
                                failures_list = failures_list,
                                runtime = time_text)
    workspaces_text += '</table>'

    
    message = '''<html>
    <head>
    {table_style_text}
    </head>
    <body style='font-family:Montserrat,sans-serif; font-size:18px; padding:30; background-color:#FAFBFD'>
    <p>
    <center><div style='background-color:#82AA52; color:#FAFBFD; height:100px'>
    <h1>
    <img src='https://app.terra.bio/static/media/logo-wShadow.c7059479.svg' alt='Terra rocks!' style='vertical-align: middle;' height='100'>
    <span style='vertical-align: middle;'>
    Featured Workspace Report: Master list</span></h1></center></div>

    <br><center><big>{fail_count_text}</big><br>{call_cache_text}</center>
    <br><br>
    {workspaces_text}<br>
    </p>

    <br><br>Test started: {clone_time}
    <br>Test finished: {done_time}
    </p></body>
    </html>'''

    message = message.format(table_style_text = table_style_text,
                            fail_count_text = fail_count_text,
                            call_cache_text = call_cache_text,
                            workspaces_text = workspaces_text,
                            clone_time = clone_time,
                            done_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))

    
    
    # open, generate, and write the html text for the report
    local_path = '/tmp/' + report_name
    f = open(local_path,'w')
    f.write(message)
    f.close()

    # upload report to google cloud bucket
    report_path = upload_to_gcs(local_path, gcs_path, verbose)

    return report_path


def test_all(args):
    # make a folder for this set of tests (folder name is current timestamp)
    if args.report_name is None:
        clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        report_name = 'master_report_' + clone_time + '.html'
    else:
        report_name = args.report_name
        clone_time = report_name.replace('master_report_','').replace('.html','')
        if len(clone_time) == 0: # in case the input name was poorly formatted
            clone_time = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')

    gcs_path_subfolder = args.gcs_path + clone_time + '/'

    # get dict of all Featured Workspaces
    fws = format_fws(verbose=False) 

    # temporary for troubleshooting/testing
    if args.troubleshoot:
        copy_fws = {}
        for key in fws.keys():
            if 'Terra Notebooks Playground' in key: # this fails fast
                copy_fws[key] = fws[key]
            elif 'GATKTutorials-Pipelining' in key: # this succeeds fast
                copy_fws[key] = fws[key]
            elif 'GATKTutorials-Somatic' in key: # this succeeds fast
                copy_fws[key] = fws[key]
            elif 'Introduction-to-TCGA-Dataset' in key: # this fails fast
                copy_fws[key] = fws[key]
            elif 'Terra_Quickstart_Workspace' in key: # one workflow fails in a few minutes
                copy_fws[key] = fws[key]
        fws = dict(copy_fws)
        print(fws.keys())


    fws_testing = {}
    # set up to run tests on all of them
    for ws in fws.values():
        clone_ws = clone_workspace(ws.project, ws.workspace, args.clone_project, 
                                    clone_time=clone_time, share_with=args.share_with, 
                                    call_cache=args.call_cache, verbose=args.verbose)
        clone_ws.create_submissions(verbose=args.verbose) # set up the submissions
        clone_ws.start_timer() # start a timer for this workspace's submissions
        clone_ws.check_submissions(abort_hr=args.abort_hr, verbose=False) # start them
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
                clone_ws.check_submissions(abort_hr=args.abort_hr)
                if len(clone_ws.active_submissions) == 0: # if all submissions in this workspace are DONE
                    clone_ws.stop_timer()
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
    master_report_path = generate_master_report(args.gcs_path, clone_time=clone_time, report_name=report_name, ws_dict=fws_testing, verbose=args.verbose)
    os.system('open ' + master_report_path)

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--test_master_report', '-r', type=str, default=None, help='folder name in gcs bucket to use to generate report')
    parser.add_argument('--report_name', '-n', type=str, default=None, help='name of master report (ideally with a timestamp)')

    parser.add_argument('--cost_report', '-c', type=str, default=None, help='name of original master test report to query for cost' )

    parser.add_argument('--clone_project', type=str, default='featured-workspace-testing', help='project for cloned workspace')
    parser.add_argument('--share_with', type=str, default='GROUP_FireCloud-Support@firecloud.org', help='email address of person or group with which to share cloned workspace')
    parser.add_argument('--sleep_time', type=int, default=60, help='time to wait between checking whether the submissions are complete')
    parser.add_argument('--gcs_path', type=str, default='gs://dsp-fieldeng/fw_reports/', help='google bucket path to save reports')
    parser.add_argument('--abort_hr', type=int, default=24, help='# of hours after which to abort submissions (default 24). set to None if you do not wish to abort ever.')
    parser.add_argument('--call_cache', type=bool, default=False, help='whether to call cache the submissions (default False for FW tests)')
    
    parser.add_argument('--troubleshoot', '-t', action='store_true', help='run on a subset of FWs that go quickly, to test the report')
    parser.add_argument('--verbose', '-v', action='store_true', help='print progress text')

    args = parser.parse_args()
  
    # delete any workspaces older than 2 months
    cleanup_workspaces(args.project, age_days=60, verbose=args.verbose)

    if args.test_master_report is not None:
        fws_dict = get_fws_dict_from_folder(args.gcs_path, args.test_master_report, args.clone_project, args.verbose)
        report_path = generate_master_report(args.gcs_path, 
                                            clone_time=args.test_master_report.replace('/',''), 
                                            ws_dict=fws_dict, 
                                            verbose=args.verbose)
        os.system('open ' + report_path)
    elif args.cost_report is not None:
        report_path, total_cost = get_cost_of_test(args.gcs_path, args.cost_report, args.clone_project)
        os.system('open ' + report_path)
    else:
        test_all(args)
    