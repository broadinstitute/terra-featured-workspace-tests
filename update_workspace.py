# import requests
# import json
import os
import subprocess
import ast
import shutil
import argparse
from fiss_fns import call_fiss
from firecloud import api as fapi
# from ws_class import Wspace
# from datetime import datetime


def update_notebooks(workspace_name, workspace_project, replace_this, with_this):
    print("Updating NOTEBOOKS for " + workspace_name)

    ## update notebooks
    # Getting the workspace bucket
    r = fapi.get_workspace(workspace_project, workspace_name)
    fapi._check_response_code(r, 200)
    workspace = r.json()
    bucket = workspace['workspace']['bucketName']

    # check if bucket is empty
    gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/']
    bucket_files = subprocess.check_output(gsutil_args)
    # Check output produces a string in Py2, Bytes in Py3, so decode if necessary
    if type(bucket_files) == bytes:
        bucket_files = bucket_files.decode().split('\n')
    # print(bucket_files)

    editingFolder = "../notebookEditingFolder"

    # if the bucket isn't empty, check for notebook files and copy them
    if 'gs://'+bucket+'/notebooks/' in bucket_files: #len(bucket_files)>0:
        # bucket_prefix = 'gs://' + bucket
        # Creating the Notebook Editing Folder
        if os.path.exists(editingFolder):
            shutil.rmtree(editingFolder)
        os.mkdir(editingFolder)
        # Runing a gsutil ls to list files present in the bucket
        gsutil_args = ['gsutil', 'ls', 'gs://' + bucket + '/notebooks/**']
        bucket_files = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
        # Check output produces a string in Py2, Bytes in Py3, so decode if necessary
        if type(bucket_files) == bytes:
            bucket_files = bucket_files.decode().split('\n')
        #Getting all notebook files
        notebook_files = []
        print("Copying files to local disk...")
        for bf in bucket_files:
            if ".ipynb" in bf:
                notebook_files.append(bf)
                # Downloading notebook to Notebook Editing Folder
                gsutil_args = ['gsutil', 'cp', bf, editingFolder]
                print('  copying '+bf)
                copyFiles = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
        #Does URL replacement
        print("Replacing text in files...")
        sed_command = "sed -i '' -e 's#{replace_this}#{with_this}#' {editing_folder}/*.ipynb".format(
                                        replace_this=replace_this,
                                        with_this=with_this,
                                        editing_folder=editingFolder)
        os.system(sed_command)
        #Upload notebooks back into workspace
        print("Uploading files to bucket...")
        for filename in os.listdir(editingFolder):
            if not filename.startswith('.'):
                if not filename.endswith(".ipynb"):
                    print("  WARNING: non notebook file, not replacing "+filename)
                else:
                    print('  uploading '+filename)
                    gsutil_args = ['gsutil', 'cp', editingFolder+'/'+filename,  'gs://' + bucket+"/notebooks/"+filename]
                    uploadfiles = subprocess.check_output(gsutil_args, stderr=subprocess.PIPE)
                    #Remove notebook from the Notebook Editing Folder
                    os.remove(editingFolder+'/'+filename)
        #Deleting Notebook Editing Folder to delete any old files lingering in the folder
        shutil.rmtree(editingFolder)
    else:
        print("Workspace has no notebooks folder")


def update_attributes(workspace_name, workspace_project, replace_this, with_this):
    ## update workspace data attributes
    print("Updating ATTRIBUTES for " + workspace_name)

    # get data attributes
    response = call_fiss(fapi.get_workspace, 200, workspace_project, workspace_name)
    attributes = response['workspace']['attributes']

    attrs_list = []
    for attr in attributes.keys():
        value = attributes[attr]
        if isinstance(value, str): # if value is just a string
            if replace_this in value:
                new_value = value.replace(replace_this, with_this)
                attrs_list.append(fapi._attr_set(attr, new_value))
        elif isinstance(value, dict):
            if replace_this in str(value):
                value_str = str(value)
                value_str_new = value_str.replace(replace_this, with_this)
                value_new = ast.literal_eval(value_str_new)
                attrs_list.append(fapi._attr_set(attr, value_new))
        elif isinstance(value, bool):
            pass
        else: # some other type, hopefully this doesn't exist
            if replace_this in value:
                print('unknown type of attribute')
                print('attr: '+attr)
                print('value: '+value)
                # value_new = value.replace(replace_this, with_this)
                # attrs_list.append(fapi._attr_set(attr, value_new))


    response = fapi.update_workspace_attributes(workspace_project, workspace_name, attrs_list)
    try_notebooks=True
    if response.status_code == 403: # insufficient permissions
        print('\nINSUFFICIENT PERMISSIONS TO EDIT '+workspace_name+' (project: '+workspace_project+')\n\n')
        try_notebooks=False
    elif response.status_code != 200:
        print(response.status_code)
        print(response.text)
        exit(1)

    return try_notebooks


def update_entities(workspace_name, workspace_project, replace_this, with_this):
    ## update workspace entities
    print("Updating DATA ENTITIES for " + workspace_name)

    # get data attributes
    response = call_fiss(fapi.get_entities_with_type, 200, workspace_project, workspace_name)
    entities = response


    for ent in entities:
        print('ent: ')
        print(ent)
        ent_name = ent['name']
        ent_type = ent['entityType']
        ent_attrs = ent['attributes']
        attrs_list = []
        for attr in ent_attrs.keys():
            value = ent_attrs[attr]
            print('attr: ')
            print(attr)
            print('value: ')
            print(value)
            if isinstance(value, str): # if value is just a string
                if replace_this in value:
                    new_value = value.replace(replace_this, with_this)
                    attrs_list.append(fapi._attr_set(attr, new_value))
            elif isinstance(value, dict):
                if replace_this in str(value):
                    value_str = str(value)
                    value_str_new = value_str.replace(replace_this, with_this)
                    value_new = ast.literal_eval(value_str_new)
                    attrs_list.append(fapi._attr_set(attr, value_new))
            elif isinstance(value, bool):
                pass
            elif value is None:
                pass
            else: # some other type, hopefully this doesn't exist
                # if replace_this in value:
                print('unknown type of attribute')
                print('attr: '+attr)
                print('value: '+value)
                # value_new = value.replace(replace_this, with_this)
                # attrs_list.append(fapi._attr_set(attr, value_new))

        response = fapi.update_entity(workspace_project, workspace_name, ent_type, ent_name, attrs_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--workspace_name', help='name of workspace in which to make changes')
    parser.add_argument('--workspace_project', help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('--replace_this', help='target string to be replaced')
    parser.add_argument('--with_this', help='replacement string for every instance of target string ("replace_this")')

    args = parser.parse_args()

    # update the workspace attributes
    # update_attributes(args.workspace_name, args.workspace_project, args.replace_this, args.with_this)
    # update_notebooks(args.workspace_name, args.workspace_project, args.replace_this, args.with_this)
    update_entities(args.workspace_name, args.workspace_project, args.replace_this, args.with_this)

    # {"file-name.bam": "gs://new/path/",
    # "file-name2.bam": "gs://new/path2"}
