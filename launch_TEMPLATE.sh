#! /bin/bash

JOBNAME="test-hpc-pipeline"                             # Can be anything unique
INPUTFOLDER="/QRISdata/Q2396/SPIM_120170/Spontaneous"   # A folder containing individual folders for each fish
OUTPUTFOLDER="/QRISdata/Q4008/Q2396/Spontaneous"        # An output folder where the finish fish folders will go
JOBTYPE='fish-whole'                                    # The type of job, for now leave this as fish-whole
S2PCONFIG='ops_1P_whole.json'                           # Path to a json file containing the ops for suite2p

## COMMENTS
# You can add any comments about this job here. e.g. testing tau = 1.5.
# This comments will get saved in a .txt file with the same name as the log file.

## The below shouldn't need editing in normal use

echo "------------------------------------------" >>${JOBNAME}.txt
date >>${JOBNAME}.txt
cat ${0##*/} >>${JOBNAME}.txt  # copy this file into "jobname".txt
echo "s2p file:" >>${JOBNAME}.txt
cat $S2PCONFIG >>${JOBNAME}.txt

# Actually start monitoring
nohup python3 hpc_pipeline.py -j $JOBTYPE -i $INPUTFOLDER -o $OUTPUTFOLDER -s $S2PCONFIG  ${JOBNAME} >>${JOBNAME}.txt 2>&1 &
