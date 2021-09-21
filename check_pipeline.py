""" check_pipeline.py
    Print status of all pipelines currently running
"""
import subprocess
import os

PIDIDX=0
NAMEIDX=1


def main():
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

    for controller in controllers:
        print('-' * 60)
        print(f'{controller[NAMEIDX]}, jobid: {controller[PIDIDX]}')
        
        fish_states = parse_logs(controller[NAMEIDX])
        for fish_string in fish_states.values():
            print(f'    {fish_string}')
    print('-' * 60)


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