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
    parser.add_argument("--do_report", action='store_true',
                        help="run a report")
    parser.add_argument("--do_submission", action='store_true',
                        help="run the workflow submission")

    args = parser.parse_args()
    # print(args)


    clone_name = args.clone_name # this is None unless you entered one

    if clone_name is None:
        print("cloning "+args.original_name)
        clone_name = clone_workspace(args.original_project, args.original_name, args.clone_project)
        print(clone_name)

    if args.do_submission:
        print("running submission on "+clone_name)
        run_workflow_submission(args.clone_project, clone_name)

    if args.do_report:
        print("running report on "+clone_name)
        namespace = args.clone_project
        workspace = clone_name

        # test_fail = False
        # test_succeed = False
        
        # if test_fail:
        #     # this will fail
        #     namespace = "fccredits-curium-coral-4194"
        #     workspace = "Germline-SNPs-Indels-GATK4-b37-EX06test"

        # if test_succeed:
        #     # this will succeed
        #     namespace = "fccredits-sodium-tan-9687"
        #     workspace = "Sequence-Format-Conversion_2019-08-28-14-54-18"

        generate_workflow_report(namespace, workspace)
        os.system("open hello.html")