""" submit_run_warp_job.py
    Write the file for and submit (qsub) a pbs job to process warp a fish
    using ants. Will launch warp_fish.py. Note the output_directory is fish
    specific.
"""
from subprocess import call
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('s2p_output_path', help="Absolute path to the directory with s2p plane folders")
parser.add_argument('output_directory', help="Absolute path where this individual output folder should be made")
args = parser.parse_args()

s2p_output_path = os.path.normpath(args.s2p_output_path)
ants_output_path = os.path.normpath(args.output_directory)
fish_num = os.path.basename(s2p_output_path).split('fish')[1].split('_')[0]

## Define variables needed for file
users_school = os.getenv('UQSCHOOL')

## Build pbs script 
file_contents = f"""#!/bin/bash
#PBS -N {fish_num}_ANTs
#PBS -A {users_school}
#PBS -l select=1:ncpus=6:mem=110GB:vmem=110GB
#PBS -l walltime=06:00:00
#PBS -j oe
#PBS -k doe

## Needed because packages like nrrd are in suite2p env
module load anaconda
source activate suite2p

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=6
python ~/hpc_pipeline/warp_fish.py {s2p_output_path} {ants_output_path}

cp ~/*.o* /QRISdata/Q4414/debug/
"""


## Write pbs script to disk
pbs_filename = 'ants_warp_fish.pbs'
with open(pbs_filename, 'w') as fp:
    fp.write(file_contents)


## Launch the HPC job
job_string = f"qsub {pbs_filename}"
call([job_string],shell=True)