import sys
import requests
import time
import datetime
import time as mod_time

start_time = time.time()

# Define your Jenkins URL and credentials
jenkins_url = "https://own.hosted.site/jenkins/"
username = "the_username"
api_token = "the_password"

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

# Function to get jobs recursively
def get_jobs_recursively(api_url):
    jobs = []
    # response = requests.get(url, auth=auth)
    response = make_get_request_with_retries(api_url)
    # time.sleep(5)
    if response.status_code == 200:
        data = response.json()
        if data['_class'] == "hudson.model.Hudson":
            print("Processing: Jenkin's root directory")
        else:
            print(f"\nProcessing: {data['fullName']}")
        for job in data.get('jobs', []):
            try:
                if job['_class'] == 'com.cloudbees.hudson.plugins.folder.Folder':
                    jobs.append({'type': job['_class'], 'name': job['name'], 'url': job['url'], 'buildable': "N/A", 'lastBuild': "N/A"})
                    jobs.extend(get_jobs_recursively(job['url'] + 'api/json'))
                elif job['_class'] == 'org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject' or job['_class'] == 'jenkins.branch.OrganizationFolder' or job['_class'] == 'com.cloudbees.hudson.plugins.modeling.impl.jobTemplate.JobTemplate':
                    jobs.append({'type': job['_class'], 'name': job['name'], 'url': job['url'], 'buildable': "N/A", 'lastBuild': "N/A"})
                else:
                    job_api_url = f"{job['url']}api/json"
                    print(f" {job['url']}")
                    job_api_response = make_get_request_with_retries(job_api_url)
                    # time.sleep(5)
                    job_data = job_api_response.json()
                    
                    try:
                        if job_data['lastBuild'] == None:
                            lastBuild = "Not built once"
                        else:
                            build_api_url = f"{job_data['lastBuild']['url']}/api/json?tree=number,timestamp"
                            build_api_response = make_get_request_with_retries(build_api_url)
                            # time.sleep(5)
                            build_data = build_api_response.json()
                            
                            # Convert to seconds by dividing by 1000
                            epoch_time_s = build_data['timestamp'] / 1000

                            # Convert to datetime
                            date_time = datetime.datetime.fromtimestamp(epoch_time_s)

                            # Extract the date part
                            date_only = date_time.date()

                            lastBuild = str(date_only)
                    except:
                        lastBuild = "error"
                        
                    jobs.append({'type': job['_class'], 'name': job['name'], 'url': job['url'], 'buildable': job_data['buildable'], 'lastBuild': lastBuild})
            except:
                print("Some error has occurred but skipped without writing to the csv or temp file.")
    return jobs

# Main execution block

# API endpoint to get the list of all jobs
api_url = f"{jenkins_url}/api/json?tree=jobs[name,url,_class,fullName]"

# Get the list of jobs recursively
f = open("all_jobs_in_apic_jenkins.temp", "w")
f.close()
all_jobs = get_jobs_recursively(api_url)

# Output the results
f = open("all_jobs_in_apic_jenkins.temp", "w")
f.write(str(all_jobs))
f.close()

with open("all_jobs_in_apic_jenkins.csv","w") as f:
    f.write("Type,Job Name,URL,Buildable,Last build")
    for job in all_jobs:
        # print(f"Job Name: {job['name']}, URL: {job['url']}")
        f.write(f"\n{job['type']},{job['name']},{job['url']},{job['buildable']},{job['lastBuild']}")

if not all_jobs:
    print("No jobs found.")

print(f"\n\n--- Took {round(time.time() - start_time) // 60} minutes for processing" )