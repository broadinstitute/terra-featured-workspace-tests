import os
from get_fws import get_fws_dict_from_folder
from fiss_fns import call_fiss
from gcs_fns import convert_to_public_url, upload_to_gcs
from firecloud import api as fapi


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
    abort = False
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
        submissions_json = call_fiss(fapi.list_submissions, 200, ws.project, ws.workspace, specialcodes=[404])
        if submissions_json.status_code == 404: # error 404 means workspace does not exist
            abort = True
            break
        else:
            submissions_json = submissions_json.json()
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

    if abort:
        print('At least one workspace did not exist. Cost reporting aborted.')
        report_path = None
    else:
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

def get_cost_of_all_tests(gcs_path, project, verbose):
    system_command = "gsutil ls " + gcs_path
    all_paths = os.popen(system_command).read()

    master_report_list = [] # accumulate all master reports to test
    cost_report_list = [] # accumulate existing cost reports
    for path in all_paths.split('\n'):
        if ('master_report' in path) and ('COST' not in path):
            if path.replace('.html','_COST.html') in all_paths.split('\n'): 
                # don't redo a report you've already done
                cost_report_list.append(path.replace('.html','_COST.html').split('/')[-1])
            else:
                master_report_list.append(path.split('/')[-1])

    costs_over_time = []
    # get new reports
    for report_name in master_report_list:
        report_path, cost = get_cost_of_test(gcs_path, report_name, project, verbose)
        # clone_time = report_name.replace('master_report_','').replace('.html','')
        costs_over_time.append('${:,.2f}'.format(cost))
    # accumulate previously calculated reports
    for report_name in cost_report_list:
        system_command = 'gsutil cat ' + gcs_path+report_name
        contents = os.popen(system_command).read()
        for line in contents.split('\n'):
            # get cost
            if 'Total cost:' in line:
                cost = line.split('cost: ')[-1].split('</big>')[0]
        costs_over_time.append(cost)


    all_reports = master_report_list + cost_report_list
    for i in range(len(all_reports)):
        print(all_reports[i], costs_over_time[i])


if __name__ == "__main__":

    # params
    clone_project = 'featured-workspace-testing'
    gcs_path = 'gs://terra-featured-workspace-tests-reports/fw_reports/'
    verbose = True

    get_cost_of_all_tests(gcs_path, clone_project, verbose)