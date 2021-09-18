""" This tool allows jobs to automatically be relaunched on a remote server 
    until some completion criteria are met. The main function loops over a list
    of jobs until each meets its stopping criteria, relaunching and monitoring
    them as necessary. Jobs in the list should inherit from the HPCJob class.
"""
import paramiko
import os
import time
import datetime
import logging
import argparse
import json
import shutil
import datetime

# How long to wait before checking on running jobs
WAITTIME = 6 * 60 * 60
# HPC ssh address to use
HPCHOSTNAME='awoonga.qriscloud.org.au'
# HPC user account to use, set as environment variable
USERNAME=os.getenv('UQUSERNAME')



def main():

    ## Process input arguments
    parser = argparse.ArgumentParser(description="Launch and monitor computational jobs on a remote server.")
    parser.add_argument('-j', '--job-type', help='The type of HPC job to run', type=str, choices=['fish-whole', 'fish-slices', 'slice-whole', 'fish-parallel'], default='fish-whole')
    parser.add_argument('-s', '--s2p-config-json', help='Suite2p json config file', type=str)
    parser.add_argument('-i', '--input-folder', help='Folder containing input data', type=str)
    parser.add_argument('-o', '--output-folder', help='Folder where output should be saved', type=str)
    parser.add_argument('-a', '--array-id', help='Job ID of a currently running array to watch - for slice arrays only', type=str)
    parser.add_argument('name', help='A unique name identifying this set of jobs.', type=str)
    args = parser.parse_args()

    ## Initialise logging
    logging.basicConfig(filename=f'{args.name}.log', level=logging.INFO)
    logging.info('-' * 60)
    logging.info(f'{datetime.datetime.now()}                   Launch pipeline')
    logging.info('-' * 60)

    ## Set up SSH connection
    ssh = get_ssh_connection()

    ## Create job objects based on input arguments
    incomplete_jobs = []
    if args.job_type == 'fish-whole':
        print('Doing fish whole job')
        # Send s2p args to server and get the filename used
        exp_s2p_filename = transfer_s2p_args(ssh, args.name, args.s2p_config_json)

        ## Create all jobs
        incomplete_jobs = create_whole_fish_s2p_jobs(ssh, args.input_folder, args.output_folder, exp_s2p_filename, FullFishs2p)
        
    elif args.job_type == 'fish-slices':
        # Send s2p args to server and get the filename used
        logging.info('Starting a fish-slices job')
        exp_s2p_filename = transfer_s2p_args(ssh, args.name, args.s2p_config_json)
        incomplete_jobs = [SlicedFishs2p(ssh, args.input_folder, args.output_folder, exp_s2p_filename, args.name)]
        if args.array_id:
            logging.info(f'Using passed in job_id: {args.array_id}')
            incomplete_jobs[0].job_ids.append(args.array_id)
    
    elif args.job_type == 'fish-parallel':
        print('doing parallel_fish')
        # Send s2p args to server and get the filename used
        exp_s2p_filename = transfer_s2p_args(ssh, args.name, args.s2p_config_json)

        ## Create all jobs
        incomplete_jobs = create_whole_fish_s2p_jobs(ssh, args.input_folder, args.output_folder, exp_s2p_filename, ParallelFishs2p)
    
    elif args.job_type == 'slice-whole':
        print('Doing slice-whole (will reslice fish then process)')
        raise NotImplementedError()

    else:
        print('Job type not recognised.')
        raise Exception()

    ## Main loop
    while incomplete_jobs:

        ## Get a list of currently running jobs
        running_jobs = get_current_jobs(ssh)
        logging.info(f'Check on job states: {datetime.datetime.now()}')

        finished_jobs = []
        ## for each incomplete job
        for job in incomplete_jobs:

            ## if job is still running, skip for now
            if job.get_latest_job_id() in running_jobs:
                logging.info(f'Still running, skip {job}')
                continue

            # if not running and meets finished criteria, prepare to remove          
            if job.is_finished():
                finished_jobs.append(job)
                logging.info(f'Job finished: {job}')
                continue

            # else, not running and not finished, so restart
            job.start_job()

        ## remove finished jobs from incomplete jobs
        [incomplete_jobs.remove(job) for job in finished_jobs]
        finished_jobs = []

        ## Wait some time before checking again
        time.sleep(WAITTIME)    


def transfer_s2p_args(ssh, exp_name, s2p_config_json):
    ## Create an experiment specific copy of s2p_ops 
    exp_s2p_filename = f'{exp_name}_{os.path.basename(s2p_config_json)}'
    shutil.copy2(s2p_config_json, exp_s2p_filename)

    ## move to server
    ftp_client = ssh.open_sftp()
    ftp_client.put(exp_s2p_filename, exp_s2p_filename)
    logging.info(f"Sent {exp_s2p_filename} to server.")
    return exp_s2p_filename

def create_whole_fish_s2p_jobs(ssh, input_folder, output_folder, s2p_config_json, job_class):
    """ Create suite2p whole fish jobs for the cluster given the ssh connection
        and the command line arguments

    Arguments:
        ssh: The ssh connection to the server for jobs to run on
        input_folder: Path to folder containing folders of fish
        output_folder: Path to save folders of finished fish
        s2p_config_json: Path to json file containing s2p attributes to use

    Returns:
        List of job_class jobs to be run on the server.
    """
    ## Get a list of all fish
    ls_fish = f'ls {input_folder}'
    all_fish = run_command(ssh, ls_fish)
    # ls results end in \n, need to strip away
    all_fish = [filename.strip() for filename in all_fish]
    input_folder = os.path.normpath(input_folder)

    # TODO : hack to only process some of q2396 fish (just grab some)
    # all_fish = all_fish[18:25]

    fish_jobs = []
    for fish_base_name in all_fish:
        fish_abs_path = os.path.join(input_folder, fish_base_name)
        fish_job = job_class(ssh, fish_abs_path, output_folder, s2p_config_json)
        fish_jobs.append(fish_job)
    
    logging.info(f'Created several fish jobs: {fish_jobs}')
    return fish_jobs


def create_slice_whole_jobs(ssh, base_input_folder, output_folder):
    """ Given a folder with multiple fish create a list of SliceFish objects to
        slice the fish ready for s2p.

    Arguments:
        ssh: The ssh connection to the server for jobs to run on
        input_folder: Path to folder containing folders of fish
        output_folder: Path to save folders of sliced fish

    Returns:
        List of SliceFish jobs to be run on the server.
    """
    ## Get a list of all fish
    ls_fish = f'ls {base_input_folder}'
    all_fish = run_command(ssh, ls_fish)
    # ls results end in \n, need to strip away
    all_fish = [filename.strip() for filename in all_fish]
    input_folder = os.path.normpath(base_input_folder)

    slice_jobs = []
    for slice_base_name in all_fish:
        slice_abs_path = os.path.join(base_input_folder, slice_base_name)
        #fish_job = FullFishs2p(ssh, slice_abs_path, output_folder, s2p_config_json)
        slice_job = SliceFish(ssh, slice_abs_path, output_folder)
        slice_jobs.append(slice_job)
    
    logging.info(f'Created several SliceFish jobs: {slice_jobs}')
    return slice_jobs

def run_command(ssh, command):
    """ Execute a given command on the remote server and return a list of lines

    Arguments:
        ssh: The ssh connection to the server for jobs to run on
        command: the command to execute on the remote server

    Returns:
        List of strings of the output resulting from running the command
    """
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.readlines()    

def get_current_jobs(ssh):
    """ Given the ssh object return a list of all current jobs running 

    Arguments:
        ssh: The ssh connection to the server for jobs to run on

    returns:
        list of strings with the job id of all running jobs. Array jobs have 
          the [] removed. 
    """
    stdin, stdout, stderr = ssh.exec_command('qstat')

    running_jobs = []
    for line in stdout.readlines():
        job_id = parse_job_id(line)
        if job_id:
            running_jobs.append(job_id)
    
    return running_jobs

def parse_job_id(line):
    """ Parse a string returning job id or None if one cannot be found

    Argument:
        line: the string to parse

    Returns:
        A string of number representing a job id or None
    """
    if '.awon' in line:
        return line.split('.awon')[0].strip('[]')
    return None


def get_ssh_connection():
    """ Start a connection to HPC
    
    Returns:
        SSH client to HPC cluster where jobs should be launched
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HPCHOSTNAME, username=USERNAME)
    return ssh



class HPCJob:
    """ An abstract class representing some computation to be run on a ssh
        connection

    Attributes:
      job_ids: List of job ids that have been used
      ssh: The ssh connection where jobs are being run
    """
    def __init__(self, ssh):
        self.job_ids = []
        self.ssh = ssh

    def get_latest_job_id(self):
        """ Return the job id of the latest job that was sent to the HPC
        """
        return self.job_ids[-1] if len(self.job_ids) else None

    def start_job(self):
        """ Launch a job through the ssh connection attribute
        """
        raise NotImplementedError

    def do_qsub_check_errors(self, launch_cmd):
        logging.info(f'ssh exec: {launch_cmd}')
        # Actually send job to awoonga
        stdin, stdout, stderr = self.ssh.exec_command(launch_cmd)

        # Did launching the job cause error output
        any_errors = stderr.readlines()
        if any_errors:
            logging.warning(f'Error when starting fish: {any_errors}')
            return None

        # Try to parse job id
        output = stdout.readlines()[0]
        job_id = parse_job_id(output)

        self.job_ids.append(job_id)
        logging.info(f'Successfully launched: {self}')
        return job_id

    def is_finished(self):
        """ Returns True iff the stopping criteria for this job are met
        """
        raise NotImplementedError
    
    def __str__(self):
        return f'HPCJob({self.job_ids})'

    def __repr__(self):
        return str(self)


class Warp2Zbrains(HPCJob):
    """ Warp a completed suite2p fish to Zbrain coordinates
    
        Rough actions:
            - Warp suite2p motion corrected meanImg to template
            - Convert suite2p output to csv list
            - Warp csv list to template
            - warp points again to zbrain
    """

    def __init__(self, ssh, fish_abs_path, base_output_folder):
        """ 
        Args:
            ssh: An open ssh connection
            fish_abs_path: Absolute path to folder containing one or more .tif 
              files
            base_output_folder: Absolute path where results from ANTs should be
              saved.
        """
        super().__init__(ssh)
        self.fish_abs_path = fish_abs_path
        self.base_output_folder = base_output_folder

    def start_job(self):
        ## Warp suite2p motion corrected meanImg to template

        ## Convert suite2p output to csv list
        self._write_csv()



        ## Warp original csv list to template space

        ## Warp points in csv space to zbrains space





    def is_finished(self):
        """ Will check if final zbrains files exist
        """
        pass



class FullFishs2p(HPCJob):
    """ Run a full fish through suite2p using arguments from specified config 
        file 
    """

    ## Each fish should produce 7 output files + a plane folder per plane
    ## F.npy, iscell.npy, Fneu.npy, spks.npy, ops.npy, stat.npy, Fall.npy, plane0
    ## so number planes * 8 is how big this should be per fish.
    FILESPERFISH = 8

    def __init__(self, ssh, fish_abs_path, base_output_folder, s2p_config_json):
        """ 
        Args:
            ssh: An open ssh connection
            fish_abs_path: Absolute path to folder containing one or more .tif 
              files
            base_output_folder: Absolute path where results from suite2p should be
              saved. Each fish will create its own directory at this path.
            s2p_config_json: A json config file containing suite2p options
        """
        super().__init__(ssh)
        self.fish_abs_path = fish_abs_path
        self.base_output_folder = base_output_folder
        self.fish_output_folder = os.path.join(base_output_folder, 'suite2p_' + os.path.basename(fish_abs_path))
        self.s2p_config_json = s2p_config_json

        # Load data from s2p_config_json for use (e.g. nplanes to calc num files)
        with open(self.s2p_config_json, 'r') as fp:
            try:
                self.s2p_ops = json.loads(fp.read())
            except:
                logging.warning(f'Failed to read s2p config file: {self.s2p_config_json}')

    def start_job(self):
        launch_job = f'python ~/hpc_pipeline/submit_fish_job.py {self.fish_abs_path} {self.fish_output_folder} {self.s2p_config_json}'

        self.do_qsub_check_errors(self, launch_job)

    def is_finished(self):
        """ Check if a fish has finished all processing

        Checking if a fish has finished all processing will just entail
        checking if the correct number of files exist in the output folder this
        could be augmented with additional file size checks or Num of ROIs 
        later.

        Returns:
            Whether the fish is finished or not.
        """
        find_command = f'find {self.fish_output_folder}'
        logging.info(f'ssh exec: {find_command}')

        stdin, stdout, stderr = self.ssh.exec_command(find_command)
        find_result = stdout.readlines()

        num_files_found = len(find_result)

        nplanes = self.s2p_ops.get('nplanes')
        assert nplanes is not None, f"nplanes not found in config file: {self.s2p_config_json}"
        # 8 files per plane (inc. planex dir) +8 for combined plane, +1 for the original directory
        total_files_expected = (nplanes * self.FILESPERFISH) + self.FILESPERFISH + 1

        logging.info(f'For fish found: {num_files_found} files, Of {total_files_expected} expected')
        assert num_files_found < total_files_expected, f"Found more files ({num_files_found}) than expected ({total_files_expected}), unclear what to do, exiting."
        return total_files_expected == num_files_found

    def __repr__(self):
        return f'FullFishs2p({self.fish_abs_path}, {self.fish_output_folder}, {self.s2p_config_json})'


class ParallelFishs2p(FullFishs2p):
    """ This will be for running a whole fish but as individual planes
    """

    def start_job(self):
        ## Collect a list of planes that still need to be done
        find_iscells = f'find {self.fish_output_folder} | grep iscell.npy'
        found_files = run_command(self.ssh, find_iscells)
        logging.info(f'found_files: {found_files}')

        # Check which planes don't have an iscell.npy
        self.planes_left = [str(x) for x in range(self.s2p_ops.get('nplanes'))]
        for plane in found_files:
            plane_num = plane.split('/plane')[1].split('/')[0]
            self.planes_left.remove(plane_num)
        logging.info(f'Planes left: {self.planes_left}')

        ## Create json file of planes left to do
        contents = json.dumps(self.planes_left)
        # TODO : pass exp_name explicitly shouldn't be splitting from filename like this
        exp_name = self.s2p_config_json.split('_ops_1P_whole.json')[0]
        planes_left_json = f'planes_left_{exp_name}.json'
        with open(planes_left_json, 'w') as fp:
            fp.write(contents)

        ## Send over to cluster
        ftp_client = self.ssh.open_sftp()
        ftp_client.put(planes_left_json, planes_left_json)
        
        ## Launch and check array
        launch_job = f'python ~/hpc_pipeline/submit_fish_sliced_job.py {self.fish_abs_path} {self.fish_output_folder} {self.s2p_config_json} {planes_left_json}'

        logging.log('Would do qsub here but just testing.')
        #self.do_qsub_check_errors(self, launch_job)

class SlicedFishs2p(HPCJob):
    """ Run a sliced fish through suite2p using arguments from specified config
        file 
    """
    FILESPERSLICE = 9
    def __init__(self, ssh, slice_folder, base_output_folder, s2p_config_json, exp_name):
        """ 
        Args:
            ssh: An open ssh connection
            slice_folder: Absolute path to folder containing folders of sliced
              fish
            output_folder: Absolute path where results from suite2p should be
              saved. Each slice will create its own directory at this path.
            s2p_config_json: A json config json containing suite2p options
        """
        super().__init__(ssh)
        self.slice_folder = slice_folder
        self.base_output_folder = base_output_folder
        self.s2p_config_json = s2p_config_json
        self.exp_name = exp_name

        ## Set up a list of slices to do
        ## Get a list of all slices
        ls_slice = f'ls {self.slice_folder}'
        logging.info(f'ssh exec: {ls_slice}')
        self.all_slices = run_command(ssh, ls_slice)
        # ls results end in \n, need to strip away
        self.all_slices = [filename.strip() for filename in self.all_slices]
        # Make paths absolute
        self.all_slices = [os.path.join(self.slice_folder, slice_name) for slice_name in self.all_slices]
        # Incomplete slices is a list of absolute paths to the tif files
        # and ends in .tif
        self.incomplete_slices = self.all_slices.copy()

        self.remove_finished_slices()

    def remove_finished_slices(self):
        logging.info('remove_finished_slices')
        # use the find command to get all folders in base_output_folder
        find_command = f'find {self.base_output_folder}'
        logging.info(f'ssh exec: {find_command}')
        stdin, stdout, stderr = self.ssh.exec_command(find_command)
        find_result = stdout.readlines()
        #logging.info(f'find_result: {find_result}')

        ## Count how many files exist for each slice
        counts = [0 for _ in range(len(self.incomplete_slices))]
        for filename in find_result:
            #logging.info(f'filename: {filename}')
            for i, slice in enumerate(self.incomplete_slices):
                #logging.info(f'      slice: {slice}')
                if os.path.basename(slice) in filename:
                    counts[i] += 1
                    break

        logging.info(f'counts result: {counts}')
            
        # Any incomplete slices with the expected number of files are now complete
        finished_slices = []
        for i, count in enumerate(counts):
            if count == self.FILESPERSLICE:
                finished_slices.append(self.incomplete_slices[i])

        # Now actually remove finished slices from incomplete list
        for slice in finished_slices:
            self.incomplete_slices.remove(slice)
            logging.info(f'Finished and removing slice: {slice}')
        
        logging.info(f'Finished slices removed, {len(self.incomplete_slices)} left.')


    def start_job(self):
        ## Create a list of slices to do
        contents = '\n'.join(self.incomplete_slices)
        incomplete_slices_filename = f'incomplete_slices_{self.exp_name}.txt'
        with open(incomplete_slices_filename, 'w') as f:
            f.write(contents)

        ## Send over to cluster
        ftp_client = self.ssh.open_sftp()
        ftp_client.put(incomplete_slices_filename, incomplete_slices_filename)

        ## Launch and check array
        raise NotImplementedError('Only whole fish supported currently.')
        launch_job = f'python ~/hpc_pipeline/pipelina_HPC_run_slice.py {incomplete_slices_filename} {self.base_output_folder} {self.s2p_config_json}'
        logging.info(f'ssh exec: {launch_job}')
        # Actually send job to awoonga
        stdin, stdout, stderr = self.ssh.exec_command(launch_job)

        # Did launching the job cause error output
        any_errors = stderr.readlines()
        if any_errors:
            logging.warning(f'Error when starting fish: {any_errors}')
            return None
        
        # Try to parse job id
        output = stdout.readlines()[0]
        job_id = parse_job_id(output)

        ## Failed parse job id
        if not job_id:
            logging.warning(f'Failed to get job id.')
            return None

        self.job_ids.append(job_id)
        logging.info(f'Successfully launched: {self}')
        return job_id

    def is_finished(self):
        self.remove_finished_slices()
        return len(self.incomplete_slices) == 0


class SliceFish(HPCJob):
    def __init__(self, ssh, slice_input_folder, base_output_folder, exp_name):
        raise NotImplementedError('Lots more work needed.')
        super().__init__(ssh)
        self.slice_input_folder = slice_input_folder
        self.base_output_folder = base_output_folder
        self.exp_name = exp_name

    def start_job(self):
        # TODO : adjust below line with new name of launch script + other spots
        launch_job = f'python ~/hpc_pipeline/pipelina_HPC_run_slice_fish.py {self.slice_input_folder} {self.base_output_folder}'
        logging.info(f'ssh exec: {launch_job}')

        # actually launch job
        stdin, stdout, stderr = self.ssh.exec_command(launch_job)

        # Did launching the job cause error output
        any_errors = stderr.readlines()
        if any_errors:
            logging.warning(f'Error when starting SliceFish: {any_errors}')
            return None
        
        # Try to parse job id
        output = stdout.readlines()[0]
        job_id = parse_job_id(output)

        ## Failed parse job id
        if not job_id:
            logging.warning(f'Failed to get job id.')
            return None

        self.job_ids.append(job_id)
        logging.info(f'Successfully launched: {self}')
        return job_id

    def is_finished(self):
        raise NotImplementedError()


if __name__ == '__main__':
    main()