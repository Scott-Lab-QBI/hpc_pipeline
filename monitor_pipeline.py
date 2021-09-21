""" stopjob.py
    Stop some controller jobs and associated awoonga jobs
"""

import paramiko
import argparse
import json
from subprocess import call
import os
from check_pipeline import *

# HPC ssh address to use
HPCHOSTNAME='awoonga.qriscloud.org.au'
# HPC user account to use, set as environment variable
USERNAME=os.getenv('UQUSERNAME')
PIDIDX=0
NAMEIDX=1

def main():
    
    ## Process input arguments
    parser = argparse.ArgumentParser(description="Monitor computational jobs on a remote server.")
    parser.add_argument('job_idx', help='The list index of the job to kill', type=str, nargs='?', default='')
    args = parser.parse_args()

    # TODO : Ensure try catch for no file
    #with open(f"/home/{os.getenv('UQUSERNAME')}/hpc_pipeline/controller_data.json", 'r') as fp:
    #    controller_data = json.load(fp)

    controller_data = print_status()

    if not args.job_idx:
        return

    if int(args.job_idx) >= len(controller_data):
        print('Invalid index:', args.job_idx)
        return

    kill_awoonga_jobs = True if input('Kill associated jobs on awoonga too (y/N)? ').lower() == 'y' else False

    data_to_kill = controller_data[int(args.job_idx)]
    # data to kill is a list with two items, the first has form <job name> and <pid>
    pid = data_to_kill[0][0]

    if kill_awoonga_jobs:
        # start ssh etc.
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HPCHOSTNAME, username=USERNAME)

        job_ids = [x.split(' ')[-1].strip() for x in data_to_kill[1]]
        job_ids_string = ' '.join(job_ids)
        awoonga_kill_string = f"qdel {job_ids_string}"
        print('Awoonga kill string:', awoonga_kill_string)

        # Do awoonga kill
        stdin, stdout, stderr = ssh.exec_command(awoonga_kill_string)
    
    ## Kill local job
    #print(f"kill -9 {pid}")
    call([f"kill -9 {pid}"], shell=True)

def print_status(do_print=True):
    try:
        output = str(subprocess.check_output("ps ux | grep hpc_pipeline.py | grep -v grep", shell=True), 'UTF-8')
    except subprocess.CalledProcessError:
        print('No running controllers.')
        return

    controllers = [] # list of tuples of controller pid's and name
    for line in output.split('\n'):
        if 'hpc_pipeline.py' in line:
            pid = line.split(' ')[1]
            job_name = line.split(' ')[-1]
            controllers.append((pid, job_name))

    controllers_dict = {}
    for i, controller in enumerate(controllers):
        if do_print:
            print('-' * 60)
            print(f'({i}) {controller[NAMEIDX]}, jobid: {controller[PIDIDX]}')
        
        controllers_dict[i] = (controller, [])
        fish_states = parse_logs(controller[NAMEIDX])
        for fish_string in fish_states.values():
            if do_print:
                print(f'    {fish_string}')
            controllers_dict[i][1].append(fish_string)
    if do_print:
        print('-' * 60)

    return controllers_dict

def parse_logs(job_name):
    """ Read a log file for a """
    uq_username = os.getenv('UQUSERNAME')
    log_name = f'/home/{uq_username}/hpc_pipeline/logs/{job_name}.log'
    with open(log_name, 'r') as fp:
        log_text = fp.readlines()
    
    fish_states = {} # list of fish number and string state (only keep last state)
    for line in log_text:
        if 'FISH_STATUS:' in line:
            fish_string = line.split('FISH_STATUS:')[1].strip()
            fish_num = fish_string.split('fish_')[1].split(' ')[0]
            fish_states[fish_num] = fish_string

    return fish_states


if __name__ == '__main__':
    main()