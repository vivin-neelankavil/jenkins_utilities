import requests
import time
#author: Vivin Neelankavil(vneelank)

start_time = time.time()

# Define your Jenkins URL and credentials
jenkins_url = "https://own.hosted.site/jenkins"
username = "the_username"
api_token = "the_password"

with open('keep_forever_builds.list', 'r') as file:
    line_count = sum(1 for line in file)
    print(f" Found out {line_count} builds.")
    # time.sleep(100)

with open('keep_forever_builds.list', 'r') as file:
    for each_build in file:
        # Remove the newline character 
        cleaned_line = each_build.strip()
        print(f"\n{cleaned_line}")
        
        doNotKeepBuildForever_api_url = f"{cleaned_line}/toggleLogKeep"
        response = requests.post(doNotKeepBuildForever_api_url, auth=(username, api_token))
        
        # Check the unchecked response status 
        if response.status_code == 200: 
            print(f" Build was successfully unchecked.")
            # time.sleep(3)
            # delete_api_url = f"{cleaned_line}/doDelete"
            # response = requests.post(delete_api_url, auth=(username, api_token))
            
            # # Check the delete response status 
            # if response.status_code == 200: 
            #     print(f" Build was successfully deleted.")
            #     time.sleep(30)
            # else: 
            #     print(f" Failed to delete build with status code: {response.status_code}") 
        else: 
            print(f" Failed to uncheck build with status code: {response.status_code}") 
        
        

print(f"\n\n--- Took {round(time.time() - start_time) // 60} minutes for processing" )