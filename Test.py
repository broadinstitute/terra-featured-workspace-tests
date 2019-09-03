import os
import argparse
from workspace_test_report import *



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--clone_name", type=str, help="name of cloned workspace")
    parser.add_argument("--clone_project", type=str, default="featured-workspace-testing",
                        help="project for cloned workspace")
    parser.add_argument("--original_name", type=str, default="Sequence-Format-Conversion",
                        help="name of workspace to clone")
    parser.add_argument("--original_project", type=str, default="help-gatk",
                        help="project for original workspace")
    parser.add_argument("--do_submission", action='store_true',
                        help="run the workflow submission")
    parser.add_argument("--sleep_time", type=int, default=100,
                        help="time to wait between checking whether the submissions are complete")
    parser.add_argument("--test_fail", action='store_true',
                        help="run a report on a failed submission")
    parser.add_argument("--html_output", type=str, default="/tmp/workspace_report.html",
                        help="address to create html doc for report")

    args = parser.parse_args()
    # print(args)


    clone_name = args.clone_name # this is None unless you entered one
    if args.test_fail:
        clone_name = "do not clone"
        
    if clone_name is None:
        print("cloning "+args.original_name)
        clone_name = clone_workspace(args.original_project, args.original_name, args.clone_project)
        print(clone_name)

    if args.do_submission:
        print("running submission on "+clone_name)
        run_workflow_submission(args.clone_project, clone_name)

 
    if args.test_fail:
        # this submission has failures
        project = "fccredits-curium-coral-4194"
        workspace = "Germline-SNPs-Indels-GATK4-b37-EX06test"

        # # this submission has failures and successes
        # project = "featured-workspace-testing"
        # workspace = "Germline-SNPs-Indels-GATK4-hg38_2019-08-20-14-11-56"
    else:
        project = args.clone_project
        workspace = clone_name

    # run the report and open it
    print("running report on "+workspace)
    html_output = generate_workflow_report(project, workspace, args.html_output)
    os.system("open "+html_output)