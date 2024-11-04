import requests
import argparse
import time
import datetime
import time as mod_time
from datetime import datetime
from datetime import datetime, timedelta
from datetime import date, timedelta  

start_time = time.time()

# Define your Jenkins URL and credentials
jenkins_url = "https://own.hosted.site/jenkins/"
username = "the_username"
api_token = "the_password"

# Define the job name
job_name = "Pipelines/job/build/job/RunUnitTests"

# Function to send get request with retry mechanism
def make_get_request_with_retries(api_url, each_build, retries=3, backoff_factor=2):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(api_url, auth=(username, api_token))
            if response.status_code == 404:
                print(" - build got deleted before parsing its metadata,", end=" ")
            else:
                # print(",", end=" ")
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"\n Attempt {attempt + 1} failed: {e}")
            attempt += 1
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
    print(f"All {retries} attempts failed.")
    return None


def build_before_target_days(builds,days):
    with open("build_before_target_days.csv","w") as f:
        f.write(f"Build Number,URL\n")
        today = datetime.now()
        yesterday = datetime.now() - timedelta(days)
        today_time = int((mod_time.mktime(today.timetuple())))
        time_minus_target_days = int((mod_time.mktime(yesterday.timetuple())))
        today_unixtime = (today_time*1000)
        today_unixtime_minus_target_days = (time_minus_target_days*1000)

        print(f"\nFiltering out the builds that are before the target day {datetime.fromtimestamp(time_minus_target_days)}.")
        build_before_target_days = []
        i = 1
        for each_build in builds:   
            print(f" Processing item number {i} with build ID = {each_build}")
            api_url = f"{jenkins_url}/job/{job_name}/{each_build}/api/json?tree=number,timestamp"

            # Make a request to get the job details
            response = make_get_request_with_retries(api_url,each_build)
            if response.status_code == 200:
                job_data = response.json()
                if job_data['timestamp'] < today_unixtime_minus_target_days:
                    build_before_target_days.append(job_data['number'])
                elif job_data['timestamp'] > today_unixtime_minus_target_days:
                    break
            elif response.status_code != 404:
                print(f"Jenkins API response error")   
            # time.sleep(10)
            i = i+1
        
        # Output the results
        if not build_before_target_days:
            print("  No builds found.")
        else:
            print("\n")
            print(f" Found out {len(build_before_target_days)} builds matching the given criteria.")
            for each_build in build_before_target_days:
                f.write(f"{each_build},{jenkins_url}/job/{job_name}/{each_build}\n")
            print(" Wrote the filtered data into csv file.")
    return build_before_target_days
    
        
def keep_forever_build(builds):
    with open("keep_forever_builds.csv","w") as f:
        print("\nFiltering out the builds that are tagged as 'keep this build forever'.")
        f.write(f"Build Number,URL\n")
        keep_forever_builds = []
        i = 1
        for each_build in builds:   
            print(f" Processing item number {i} with build ID = {each_build}")
            api_url = f"{jenkins_url}/job/{job_name}/{each_build}/api/json?tree=number,keepLog"

            # Make a request to get the job details
            response = make_get_request_with_retries(api_url, each_build)
            if response.status_code == 200:
                job_data = response.json()
                if job_data['keepLog']:
                    keep_forever_builds.append(job_data['number'])
            elif response.status_code != 404:
                print(f"Jenkins API response error")   
            # time.sleep(10)
            i = i+1
        
        # Output the results
        if not keep_forever_builds:
            print("  No builds found.")
        else:
            print("\n")
            print(f" Found out {len(keep_forever_builds)} builds matching the given criteria.")
            for each_build in keep_forever_builds:
                f.write(f"{each_build},{jenkins_url}/job/{job_name}/{each_build}\n")
            print(" Wrote the filtered data into csv file.")

    return keep_forever_builds


# Function to retrieve all job builds
def get_all_builds(job_name):
    print(f"\nRetrieving all build ID's existing under job: \n {jenkins_url}/job/{job_name} \n")
    all_builds = []
    url = f"{jenkins_url}/job/{job_name}/api/json?tree=allBuilds[id]"
    response = requests.get(url, auth=(username, api_token))
    if response.status_code == 200:
        data = response.json()
        for key in data["allBuilds"]:
            all_builds.append(key['id'])
        all_builds.sort()
        print(f" Found out {len(all_builds)} builds.")
        f = open("all_builds_in_the_given_job.list", "w")
        f.write(str(all_builds))
        f.close()
        print(" Wrote the filtered data into list file.")
    else:
        print(f"Error: {response.status_code}")
    return all_builds

    
# Main code
parser = argparse.ArgumentParser(description='Python script to find jobs, builds matching certain criteria and delete the build of jobs if needed .')
parser.add_argument('--days', help='Filter builds before this day (default is 0 days)')
parser.add_argument('--builds_before', nargs='?', const=30, type=int, help='Filter builds before this day (default is 30 days)')
parser.add_argument('--builds_tagged_as_keep_forever', action='store_true', help='Filter builds tagged as keep forever')
args = parser.parse_args()

builds = get_all_builds(job_name)
if args.builds_before:
    days = int(args.builds_before)
    builds = build_before_target_days(builds, days)
if args.builds_tagged_as_keep_forever:
    builds = keep_forever_build(builds)

print(f"\n\n--- Took {round(time.time() - start_time) // 60} minutes for processing" )