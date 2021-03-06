""" submit_fish_sliced_job.py
    Write the file for and submit (qsub) a pbs job to process a whole fish
    using suite2p. Will launch s2p_fish.py. Note the output_directory is fish
    specific.
"""
from subprocess import call
import sys
import os
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('fish_abs_path', help="Absolute path to the directory with .tif files")
parser.add_argument('output_directory', help="Absolute path to this fish's individual output folder")
parser.add_argument('s2p_config_json', help="Path to a json file containing ops for suite2p")
parser.add_argument('planes_left_json', help='Path to json file with list of planes left to do')
args = parser.parse_args()

fish_folder = os.path.normpath(args.fish_abs_path)
fish_output_folder = os.path.normpath(args.output_directory)
fish_num = os.path.basename(fish_folder).split('fish')[1].split('_')[0]
job_name = args.s2p_config_json.split('_ops_1P_whole.json')[0].split('/')[-1]

with open(args.planes_left_json, 'r') as fp:
    planes_left = json.load(fp)
num_planes = len(planes_left)

## Define variables needed for file
users_school = os.getenv('UQSCHOOL')

# pbs will error if only 1 file in array, add fake job if needed
array_size = num_planes
if num_planes == 1:
    array_size = 2

## Build pbs script 
file_contents = f"""#!/bin/bash
#PBS -N {fish_num}_{job_name}
#PBS -A {users_school}
#PBS -l select=1:ncpus=4:mem=110GB:vmem=110GB
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -k doe
#PBS -J 1-{array_size}

# Deal with only 1 slice left to do case
if [ {num_planes} -eq 1 ]; then
    if [ {array_size} -eq ${{PBS_ARRAY_INDEX}} ]; then
        echo "This is the fake job to allow array, exiting."
        exit
    fi
fi

module load anaconda
source activate suite2p

for fish_tif in `ls {fish_folder}/*.tif`; do
    /usr/local/bin/recall_medici $fish_tif
done

export OMP_NUM_THREADS=4
export NUMBA_NUM_THREADS=4
export MKL_NUM_THREADS=4

python ~/hpc_pipeline/s2p_fish_sliced.py {fish_folder} {fish_output_folder} {args.s2p_config_json} {args.planes_left_json} ${{PBS_ARRAY_INDEX}}

cp ~/*.o* /QRISdata/Q4414/debug/
"""


## Write pbs script to disk
pbs_filename = 's2p_fish_sliced.pbs'
with open(pbs_filename, 'w') as fp:
    fp.write(file_contents)


## Launch the HPC job
job_string = f"qsub {pbs_filename}"
call([job_string],shell=True)