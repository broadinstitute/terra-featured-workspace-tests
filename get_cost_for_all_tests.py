import os
from featured_workspaces_test import get_cost_of_test
# from datetime import datetime


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
        report_path, cost = get_cost_of_test(gcs_path, report_name, clone_project, verbose)
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