import requests
import time
import argparse
import os
import shutil
from datetime import datetime
import json

start_time = time.time()

# Define your Jenkins URL and credentials
jenkins_url = "xxxxx"
username = "xxxxx"
api_token = "xxxxx"

def make_get_request_with_retries(api_url, retries=3, backoff_factor=2):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(api_url, auth=(username, api_token))
            if response.status_code == 404:
                print("Job deleted")
            else:
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"\n Attempt {attempt + 1} failed with reason: \n  {e}")
            attempt += 1
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
    print(f"All {retries} attempts failed.")
    return None

def create_directory_in_current_path(directory_name):
    current_path = os.getcwd()
    new_directory_path = os.path.join(current_path, directory_name)

    try:
        os.makedirs(new_directory_path, exist_ok=True)
        print(f"Directory '{new_directory_path}' created successfully")
        return new_directory_path
    except OSError as error:
        print(f"Error creating directory '{new_directory_path}': {error}")

def copy_file_to_directory(source_file_path, target_directory_path):
    # Ensure the source file exists
    if not os.path.isfile(source_file_path):
        print(f"Source file '{source_file_path}' does not exist")
        return
    
    # Ensure the target directory exists
    os.makedirs(target_directory_path, exist_ok=True)
    
    # Construct the full target file path
    target_file_path = os.path.join(target_directory_path, os.path.basename(source_file_path))
    
    # Copy the file
    shutil.copy(source_file_path, target_file_path)
    print(f"File '{source_file_path}' copied successfully to '{target_file_path}'")


def zip_directory(directory_path, output_zip_path):
    current_timestamp = datetime.now().strftime('%Y-%m-%dD_T%H-%M-%S')

    # Ensure the directory exists
    if not os.path.isdir(directory_path):
        print(f"Directory '{directory_path}' does not exist")
        return

    # Create a zip archive of the directory
    shutil.make_archive(f"{output_zip_path}_{current_timestamp}", 'zip', directory_path)
    print(f"\nDirectory '{directory_path}' zipped successfully to '{output_zip_path}.zip'")

def uncheck_keep_forever_build(item_url):

    doNotKeepBuildForever_api_url = f"{item_url}/toggleLogKeep"
    response = requests.post(doNotKeepBuildForever_api_url, auth=(username, api_token))

    # Check the unchecked response status
    if response.status_code == 200:
        print(f" Build was successfully unchecked.")
        # time.sleep(3)
    else:
        print(f" Failed to uncheck build with status code: {response.status_code}")


def print_text_between_slashes(line):
    # Remove the newline character
    cleaned_line = line.strip()

    # Find the index of the last '/'
    last_slash_index = cleaned_line.rfind('/')

    # Find the index of the second last '/'
    second_last_slash_index = cleaned_line.rfind('/', 0, last_slash_index)

    # Extract the text between the second last and last '/'
    if second_last_slash_index != -1 and last_slash_index != -1:
        text_between_slashes = cleaned_line[second_last_slash_index + 1:last_slash_index]
        return text_between_slashes
    else:
        print("Not enough slashes in the string")


def backup(item_url, item_name, backup_directory_path):
    backup_api_url = f"{item_url}/config.xml"
    response = requests.get(backup_api_url, auth=(username, api_token))
    
    # Check the backup response status
    if response.status_code == 200:
        create_directory_in_current_path(f"{backup_directory_path}/{item_name}")
        backup_file = open(f"{backup_directory_path}/{item_name}/jenkins_job_config.xml", "w")
        backup_file.write(response.text)
        backup_file.close()
        
        job_api_url = f"{item_url}api/json"
        # Function to get jobs recursively
        job_api_response = make_get_request_with_retries(job_api_url)
    
        if job_api_response.status_code == 200:
            data = job_api_response.json()
            # Convert the parsed data to a JSON formatted string with indentation
            formatted_json = json.dumps(data, indent=4)
            # job_class = data['_class']

        backup_file = open(f"{backup_directory_path}/{item_name}/jenkins_job_backup_meta.json", "w")
        # backup_file.write(f"Job class: {job_class}\nURL: {item_url}")
        backup_file.write(f"{formatted_json}")
        backup_file.close()

        print(f"\n Item was successfully backed up in the below filepath \n  {item_name}/jenkins_job_backup.txt")

        success_file = open("jenkins_item_backup_success.txt", "a")
        success_file.write(f"{item_url}\n")
        success_file.close()

        return("success")
        # time.sleep(30)
    else:
        print(f" Failed to backup item with status code: {response.status_code}")
        error_file = open("jenkins_item_backup_error.txt", "a")
        error_file.write(f"{item_url}\n")
        error_file.close()

def delete(item_url):
    delete_api_url = f"{item_url}/doDelete"
    response = requests.post(delete_api_url, auth=(username, api_token))

    # Check the delete response status
    if response.status_code == 200:
        print(f"\n Item was successfully deleted.")
        # time.sleep(30)
        success_file = open("jenkins_item_deletion_success.txt", "a")
        success_file.write(f"{item_url}\n")
        success_file.close()
    else:
        print(f"\n Failed to delete item with status code: {response.status_code}")
        error_file = open("jenkins_item_deletion_error.txt", "a")
        error_file.write(f"{item_url}\n")
        error_file.close()


# Main code
parser = argparse.ArgumentParser(description='Python script to find jobs, builds matching certain criteria and delete the build of jobs if needed .')
parser.add_argument('--uncheck_keep_forever_build', action='store_true', help='Use this to disable keep forever builds')
parser.add_argument('--delete', action='store_true', help='Use this to delete the jobs/builds')
parser.add_argument('--backup', action='store_true', help='Use this to backup the job/builds')
parser.add_argument('--backup_delete', action='store_true', help='Use this to backup the job/builds')
args = parser.parse_args()

with open('keep_forever_builds.list', 'r') as file:
    line_count = sum(1 for line in file)
    print(f"Found out {line_count} builds.")

if line_count != 0:
    i = 0
    backup_directory_path = create_directory_in_current_path('backup_jenkins_items')

    error_file = open("jenkins_item_deletion_error.txt", "w")
    error_file.close()

    error_file = open("jenkins_item_backup_error.txt", "w")
    error_file.close()

    success_file = open("jenkins_item_deletion_success.txt", "a")
    success_file.close()

    success_file = open("jenkins_item_backup_success.txt", "a")
    success_file.close()


    with open('keep_forever_builds.list', 'r') as file:
        for each_item in file:
            
            print(f"\n\n\nProcessing item number {i}")

            item_url = each_item.strip()
            item_name = print_text_between_slashes(each_item)

            print(f"\nName: {item_name}\nURL: {item_url}")

            if args.uncheck_keep_forever_build == True:
                uncheck_keep_forever_build(item_url)

            if args.backup == True:
                backup(item_url, item_name, backup_directory_path)

            if args.delete == True:
                delete(item_url, args.backup)

            if args.backup_delete == True:
                backup_status = backup(item_url, item_name, backup_directory_path)
                if backup_status == "success":
                    delete(item_url)
            i = i+1

    print("\n\n")
    # Copy the error and success files to the backup directory
    copy_file_to_directory('jenkins_item_deletion_error.txt', backup_directory_path)
    copy_file_to_directory('jenkins_item_backup_error.txt', backup_directory_path)
    copy_file_to_directory('jenkins_item_deletion_success.txt', backup_directory_path)
    copy_file_to_directory('jenkins_item_backup_success.txt', backup_directory_path)

    # Zip the backup directory
    zip_directory(backup_directory_path, backup_directory_path)

else:
    print(" Nothing to process, exiting!")
    
print(f"\n\n--- Took {round(time.time() - start_time) // 60} minutes for processing" )
