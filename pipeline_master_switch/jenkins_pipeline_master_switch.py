import jenkins
import re
import sys
import os
#author: Vivin Neelankavil(vneelank)

#Parameter validator and injector
consolidated_filtered_jobs = []
if ("SWITCH" in os.environ) and ("PATTERNS" in os.environ):
    if ((os.environ["PATTERNS"] == "Custom") and ("CUSTOM_PATTERNS" in os.environ)):
        if ((os.environ["CUSTOM_PATTERNS"] is None) or (os.environ["CUSTOM_PATTERNS"] == "")): 
            print("You have chosen to run with custom patterns but did not provide any pattern to search and disable jobs, please check.")
            sys.exit(1)
elif ("SWITCH" not in os.environ) and ("PATTERNS" not in os.environ):
    print("Something is weird! \nthis should have not happened, please check whether SWITCH and PATTERNS variable are set.")
    sys.exit(1)

#Jenkins search and take action code
server = jenkins.Jenkins(os.environ["JENKINS"], username='the_user_name', password='the_password')
user = server.get_whoami()
version = server.get_version()
print(f"\n\nHello {user['fullName']}, I have connected to your Jenkins instance running with version {version}\n")

switch = os.environ["SWITCH"]
dry_run_switch = os.environ["DRY_RUN"]

if switch == "Enable":
    print("Entered in enable jobs mode\n")
    
    if os.environ["PATTERNS"] == "Custom_file":
        if(os.path.isfile("custom_file.txt")):
            print("Custom file found.")
            with open('custom_file.txt', 'r') as file:
                disabled_jobs = file.read().split('\n')
        else:
            print("Custom file is not uploaded or does not exists, please check.")
            sys.exit(1)
    # elif os.environ["PATTERNS"] == "Custom_patterns":
    #     disabled_jobs = os.environ["CUSTOM_PATTERNS"].split(',')
    else:
        print("Default_SCM or Custom_patterns is not supported in this mode.")

    for each_job in disabled_jobs:
        print(f"\nJob Name : {each_job}")
        if dry_run_switch == "false":
            try:
                server.enable_job(each_job)
                print("Status   : Successfully enabled.")
                open("enabled_jobs.txt", "a").write(f"{each_job}\n")
            except:
                print("Status   : Enablement failed.")
                open("error_jobs.txt", "a").write(f"{each_job}\n")
        else:
            print("Status   : Would be enabled.")
            open("enabled_jobs.txt", "a").write(f"{each_job}\n")
    
elif switch == "Disable":
    print("Entered in disable jobs mode\n")
    jobs = server.get_jobs(folder_depth=10000, folder_depth_per_request=10)
    # open("jenkins_jobs.list", "w").write(str(jobs))

    if os.environ["PATTERNS"] == "Custom_patterns":
        patterns = os.environ["CUSTOM_PATTERNS"].split(',')
    elif os.environ["PATTERNS"] == "Custom_file":
        with open('custom_file.txt', 'r') as file:
            patterns = file.read().split('\n')
    else:
        with open('patterns.txt', 'r') as file:
            patterns = file.read().split('\n')
    for each_job in patterns:
        jobs_fullname = [d['fullname'] for d in jobs]
        # print(jobs_fullname)
        # r = re.compile(".*_latest_036")
        # sys.exit(1)
        r = re.compile(f".*{each_job}")
        filtered_jobs = list(filter(r.match, jobs_fullname))
        for each_filtered_job in filtered_jobs:
            consolidated_filtered_jobs.append(each_filtered_job)
        # open("jenkins_jobs_filtered.list", "w").write(str(filtered_jobs))
    open("jenkins_jobs_consolidated_filtered.list", "w").write(str(consolidated_filtered_jobs))

    for each_consolidated_filtered_job in consolidated_filtered_jobs:
        # print(each)
        job_info = server.get_job_info(each_consolidated_filtered_job, fetch_all_builds=False)
        for key, value in job_info.items():
            # print(f"Key: {key}, Value: {value}")
            if key == "buildable":
                print(f"\nJob Name : {each_consolidated_filtered_job}")
                if value == True:
                    if dry_run_switch == "false":
                        try:
                            server.disable_job(each_consolidated_filtered_job)
                            print("Status   : Successfully disabled.")
                            open("disabled_jobs.txt", "a").write(f"{each_consolidated_filtered_job}\n")
                        except:
                            print("Status   : Disablement failed.")
                            open("error_jobs.txt", "a").write(f"{each_consolidated_filtered_job}\n")
                    else:
                        print("Status   : Would be disabled.")
                        open("disabled_jobs.txt", "a").write(f"{each_consolidated_filtered_job}\n")
                else:
                    print("Status   : Already in disabled state, skipped.")
                
else:
    print("Something is weird! \nthis should have not happened.")