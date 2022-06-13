""" submit_single_vis_job.py
    Write the file for and submit (qsub) a pbs job to run matlab visualisations / analysis
    Will eventually launch create_single_fish_plots.m
"""
from subprocess import call
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('pipeline_output_directory', help="Absolute path to the directory with both s2p and ants output folders")
parser.add_argument('fish_num', help="zero-padded fish number to visualise")
args = parser.parse_args()

pipeline_output_directory = os.path.normpath(args.pipeline_output_directory)
fish_num = args.fish_num

## Define variables needed for file
users_school = os.getenv('UQSCHOOL')

## Build pbs script 
file_contents = f"""#!/bin/bash
#PBS -N {fish_num}_matlab
#PBS -A {users_school}
#PBS -l select=1:ncpus=12:mem=64GB:vmem=64GB
#PBS -l walltime=06:00:00
#PBS -j oe
#PBS -k doe

export MATLABPATH="$HOME/matlab_analysis"
module load matlab
matlab -nosplash -nodesktop -r "pipeline_core_analysis('{pipeline_output_directory}', '{fish_num}', [1200]); exit;"
"""


## Write pbs script to disk
pbs_filename = 'single_vis.pbs'
with open(pbs_filename, 'w') as fp:
    fp.write(file_contents)


## Launch the HPC job
job_string = f"qsub {pbs_filename}"
call([job_string],shell=True)