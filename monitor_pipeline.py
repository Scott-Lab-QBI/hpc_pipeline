""" stopjob.py
    Stop some controller jobs and associated awoonga jobs
"""

import paramiko
import argparse
import json
import subprocess
import os

# HPC ssh address to use
AWOOHPCHOSTNAME='awoonga.qriscloud.org.au'
FLASHHPCHOSTNAME='flashlite.rcc.uq.edu.au'
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

    kill_hpc_jobs = False if input('Kill associated jobs on HPC also (Y/n)? ').lower() == 'n' else True

    data_to_kill = controller_data[int(args.job_idx)]
    # data to kill is a list with two items, the first has form <job name> and <pid>
    pid = data_to_kill[0][0]

    if kill_hpc_jobs:
        
        ## which cluster
        hpc_hostname = FLASHHPCHOSTNAME if input('Jobs on Awoonga(A)[default] or Flashlite(F)? (A/f)').lower() == 'f' else AWOOHPCHOSTNAME

        # start ssh etc.
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hpc_hostname, username=USERNAME)

        job_ids = [x.split(' ')[-1].strip() for x in data_to_kill[1] if 'None' not in x]
        job_ids_string = ' '.join(job_ids)
        awoonga_kill_string = f"qdel {job_ids_string}"
        print('HPC kill string:', awoonga_kill_string)

        # Do awoonga kill
        stdin, stdout, stderr = ssh.exec_command(awoonga_kill_string)
    
    ## Kill local job
    #print(f"kill -9 {pid}")
    subprocess.call([f"kill -9 {pid}"], shell=True)

def print_status(do_print=True):
    try:
        output = str(subprocess.check_output("ps ux | grep hpc_pipeline.py | grep -v grep", shell=True), 'UTF-8')
    except subprocess.CalledProcessError:
        print('No running controllers.')
        return

    controllers = [] # list of tuples of controller pid's and name
    for line in output.split('\n'):
        if 'hpc_pipeline.py' in line:
            split = line.split(' ')
            split.remove('')
            pid = split[1]
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
    log_name = os.path.join(os.path.expanduser('~'), f'hpc_pipeline/logs/{job_name}.log')
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