#! /bin/bash

JOBNAME="test-hpc-pipeline"                             # Can be anything unique
INPUTFOLDER="/QRISdata/Q2396/SPIM_120170/Spontaneous"   # A folder containing individual folders for each fish
OUTPUTFOLDER="/QRISdata/Q4008/Q2396/Spontaneous"        # An output folder where the finish fish folders will go
JOBTYPE='full-pipeline'                                    # The type of job, for now leave this as full-pipeline
S2PCONFIG='ops_1P_whole.json'                           # Path to a json file containing the ops for suite2p
TEMPLATEPREFIX='MW_To_Zbrain'                           # Prefix of template on Q4414 to use (default is MW_To_Zbrain)

## COMMENTS
# You can add any comments about this job here. e.g. testing tau = 1.5.
# This comments will get saved in a .txt file with the same name as the log file.

## The below shouldn't need editing in normal use
export HPCHOSTNAME='awoonga.qriscloud.org.au'         # Either 'awoonga.qriscloud.org.au' or 'flashlite.rcc.uq.edu.au'
LOGDIR="logs"
if [[ ! -d $LOGDIR ]]; then 
    echo "Log diretory $LOGDIR, doesn't exist, creating..."
    mkdir $LOGDIR
fi
LOGFILE="${LOGDIR}/${JOBNAME}.txt"
echo "------------------------------------------" >>$LOGFILE
date >>$LOGFILE
cat ${0##*/} >>$LOGFILE  # copy this file into "logs/jobname".txt
echo "s2p file:" >>$LOGFILE
cat $S2PCONFIG >>$LOGFILE

# Actually start monitoring
nohup python3 hpc_pipeline.py -j $JOBTYPE -i $INPUTFOLDER -o $OUTPUTFOLDER -s $S2PCONFIG -p $TEMPLATEPREFIX  ${JOBNAME} >>$LOGFILE 2>&1 &
