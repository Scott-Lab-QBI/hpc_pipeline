# hpc_pipeline
This repository contains tools for automating as many steps as possible in processing calcium imaging data. It provides tools to launch and then manage jobs on the Awoonga compute cluster. A key feature of the hpc_pipeline is the ability to restart jobs that have failed for spurious reasons such as the data storage temporarily dropping out. In particular, the hpc_pipeline processes raw calcium imaging data and provides biologically relevant signals and analyses. 

# How do I process my data?


## Get Josh to add you the command server (Zfish)
The hpc_pipeline is controlled by an external server (the command server) which launches jobs on Awoonga and periodically checks on them. To access the server you will need to be added, give your uq staff id (or student number) to Josh who will add you.

## Get an Awoonga account
Follow instructions here [https://rcc.uq.edu.au/awoonga](https://rcc.uq.edu.au/awoonga). You may be required to undergo HPC training run by RCC, see [https://rcc.uq.edu.au/training](https://rcc.uq.edu.au/training). (May take a few days for your account to be approved). As description for the project add: "HPC required to analyse calcium imaging data from zebrafish, will need to launch multiple array jobs with 25-50 subjobs, each requesting ~4-6 cores and ~110GB of RAM."

## Install VS code
Visual Studio code (VS code) is an integrated development environment built by Microsoft. It allows us to edit code/files on a remote server (like the HPC computers) as if the files were locally stored on our computer. Additionally, it has an integrated terminal which will allow us to execute commands on the HPC, like running the pipeline. 

Steps:
- To install VS code follow the instructions on the VS code website [https://code.visualstudio.com/docs/setup/windows](https://code.visualstudio.com/docs/setup/windows).
- Once VS code is installed we will also need to install the remote development extension, you can install it using the install button on this [website](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack).


## Set up the hpc_pipeline on Awoonga
Now we will need to set up the hpc_pipeline on Awoonga.

Initially connect VS code to Awoonga:
- Open VS code
- Press `ctrl` + `shift` + `p` to open the VS code command palette
- type in "Remote-SSH: Connect to Host" and press enter 
- click on "Add New SSH Host..."
- type in `ssh your-user-name@awoonga.qriscloud.org.au`, replacing "your-user-name" with your own uq username (e.g. uqjsmith or s444444)
- Select the top SSH configuration file
- Press `ctrl` + `shift` + `p` to open the VS code command palette again
- type in "Remote-SSH: Connect to Host" again and select awoonga.qriscloud.org.au from the list, a new VS code window will appear, we can close the old one now
- In the new window select Linux
- Select Continue
- Enter your password
- Wait a few minutes for VS code to install on Awoonga, you may be prompted for your password again
- Once installation is done, press `ctrl` + `shift` + `` ` `` to open a terminal on Awoonga

You will only need to complete the above step once, in the future to log into Awoonga or Zfish you will only need to follow the steps in 'logging in' in the section on launching a job below.

Throughout the rest of this document you will need to type commands into this terminal, you can manually retype the commands or you can copy the commands from this page and then Right-click on the terminal to paste. Copy this command into the terminal window and replace "your-user-name" with your UQ user name.
```
echo "export UQUSERNAME=your-user-name" >> ~/.bashrc
```
For example, you might type `echo "export UQUSERNAME=uqjsmith" >> ~/.bashrc`.
QRIS also requires we tell them which school we belong to at UQ, this varies between different lab members but is likely going to be `UQ-QBI`, `UQ-SCI-SBMS` or `UQ-EAIT-ITEE`. Replace "your-uq-school" with whichever is appropriate for you. If you are unsure which account is correct for you type the command `groups` into the terminal, see which of the above appears.
```
echo "export UQSCHOOL=your-uq-school" >> ~/.bashrc
```
And now lets make sure those are working correctly, again copying this line into the terminal window, maybe take 30 seconds to refresh the terminal
```
source ~/.bashrc
```
Now copy the following into the terminal window
```
echo $UQUSERNAME
echo $UQSCHOOL
```
These should print your username and school string.

### Install anaconda on Awoonga
Before we can install Suite2p we will need to install anaconda, agree to the licence (press and hold enter to scroll to bottom of the licence and type yes), use default install locations (just press enter when asked about install locations) and then type yes to initialise miniconda.
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```
Now we can remove anaconda's install file and refresh the terminal 
```
rm Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

### Install Suite2p
We will need to download the code for [Suite2p](https://github.com/Scott-Lab-QBI/suite2p.git) by entering the commands below, first we will make sure we are in the home directory, enter the following commands into the terminal window
```
cd ~/
git clone https://github.com/Scott-Lab-QBI/suite2p.git
```
Now lets go into the Suite2p folder and set up the an Anaconda environment, copy the following commands, agree to the installation instructions and default locations
```
cd suite2p
conda env create -f environment.yml
```
To Activate and use the suite2p environment you can use the command
```
conda activate suite2p
```
Finally we need to install nrrd for warping images later in ANTs, run:
```
conda install -c conda-forge pynrrd
```

### Download the hpc_pipeline
To install the hpc_pipeline on Awoonga we will first need to go back to the home directory and then download the code

```
cd ~/
git clone https://github.com/Scott-Lab-QBI/hpc_pipeline.git
```

## Set up the hpc_pipeline on the command server (Zfish)
Now that the hpc_pipeline is installed on Awoonga we will also need to also install it on the command server. The command server takes the place of a human checking on the HPC, it will check on the state of the jobs on the HPC and restart jobs when they fail. We will be using the Zfish computer from EAIT. The next few steps will create a second VS code window, one logged into Awoonga and a new window which will be logged into Zfish. You can tell which computer each window is logged into by checking the little green box in the bottom left of the VS code window. The rest of these instructions should be run in the Zfish VS code window, you can close the Awoonga window if you want. 

Repeat the steps listed under the heading "Initially connect VS code to Awoonga" but using the remote server address `uqjarno4-zfish.zones.eait.uq.edu.au` instead of Awoonga's address.

Now, run the following commands in the terminal to install a copy of the hpc_pipeline on Zfish.
```
cd ~/
git clone https://github.com/Scott-Lab-QBI/hpc_pipeline.git
```

Now we need to make sure the hpc_pipeline knows which user account to use when it tries to connect to awoonga, in the following command replace "your-user-name" with your UQ user name
```
echo "export UQUSERNAME=your-user-name" >> ~/.bashrc
echo "alias pstat='python3 ~/hpc_pipeline/monitor_pipeline.py'" >> ~/.bashrc
source ~/.bashrc
```

### Install anaconda on Zfish
As before when installing Anaconda, agree to the licence (press and hold enter to scroll to bottom of the licence and type yes), use default install locations (just press enter when asked about install locations) and then type yes to initialise miniconda.
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```
Now we can remove anaconda's install file and refresh the terminal 
```
rm Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

### Install hpc_pipeline dependencies
The hpc_pipeline communicates with the HPC over SSH using paramiko, to install paramiko execute the following commands
```
pip install --upgrade pip
pip install setuptools-rust
pip install paramiko
```

### Set up SSH keys between Zfish and Awoonga
To allow the command server (Zfish) to access Awoonga without you there to enter your password we need to set up a pair of keys ([more info on keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2)). First we will need to generate some keys for your account on Zfish, use the default install location with no pass phrase after entering these commands in the terminal on Zfish. 
```
ssh-keygen -t ed25519
```
And now copy the new key onto Awoonga
```
ssh-copy-id ${UQUSERNAME}@awoonga.qriscloud.org.au
```

## Launch a job
The previous steps only need to be completed once to initially set up the hpc_pipeline. To use the pipeline, we just need to specify the details of the job to be run and then to start the job using a launch file. To do this log into the command server (Zfish) 

### Logging in to remote computers
- Open VS code
- Press `ctrl` + `shift` + `p` to open the VS code command palette
- type in "Remote-SSH: Connect to Host" and press enter 
- select awoonga.qriscloud.org.au or uqjarno4-zfish.zones.labs.eait.uq.edu.au from the list
- press `ctrl` + `shift` + `\`` to open a terminal

### Open your home directory
To edit files on a remote server:
- press `ctrl` + `shift` + `e` and click open folder.
- select the folder `/home/your-user-name` where "your-user-name" is your uq user name
- if prompted, click yes you trust the authors
- The files in this folder should now appear in the left hand menu

### launch files
The pipeline is controlled using launch files, in the hpc_pipeline folder on the remote server open the launch_TEMPLATE.sh file by double clicking in it from the left hand menu.
You will need to edit a few bits of information before you can run the hpc_pipeline: 
- `JOBNAME="descriptive-name"` - A short descriptive name for the job, can be anything without spaces but its important it is unique to any other running jobs e.g. `fish8-11Spont`
- `INPUTFOLDER="/path/to/folder/with/multiple/fish/folders"` - The folder in which the fish folders to process are
- `OUTPUTFOLDER="/path/where/s2p/output/should/save"` - The folder in which the finished fish will be saved
- `JOBTYPE="full-pipeline"` - The type of job, for now leave this as full-pipeline which will run everything
- `S2P_CONFIG="ops_1P_whole.json"` - A JSON file containing suite2p ops

You may want to make copies of this file for individual processing jobs or just edit the values in the original as necessary. Once you are sure the details are correct you can launch the job by typing the following into the terminal window.
```
cd ~/hpc_pipeline
./launch_TEMPLATE.sh
```
If you get a permissoion denied error message see the additional information below. The pipeline will start running in the background, if you check the `qstat` command on Awoonga you will soon see jobs starting. 


## Checking on a job or debugging
To check if the hpc_pipeline is running in a terminal on Zfish type the command
```
pstat
```
which will produce output like the below:
```
------------------------------------------------------------
(0) v1-tests, jobid: 224523
    fish_06, 0/50 planes, 0% done, Latest HPC id: 210917[]
    fish_07, 0/50 planes, 0% done, Latest HPC id: 210918[]
------------------------------------------------------------
(1) pipe2ants, jobid: 151458
    fish_05, Running ANTs, Latest HPC id: 210914
    fish_06, Running ANTs, Latest HPC id: 210915
------------------------------------------------------------
```
In this case there are two jobs running with job names v1-tests and pipe2ants, each with two fish. The initial number in backets is the the jobs pipeline number, to stop a job you can type the command `pstat` then the pipeline job number, e.g. to stop the v1-tests which has a pipeline job number of 0 you could type
```
pstat 0
```
You will be asked if you also want to stop the associated jobs on the HPC cluser (Awoonga). This doesn't always work perfectly, so if you want to make sure the HPC jobs have stopped you will need to log into Awoonga and do that manually. 

To check the logs (which tell us what the program is doing / did) we need to know the jobname specified for the job. We can then view the logs using
```
cd ~/hpc_pipeline
cat logs/descriptive-name.log
``` 
which will just paste the whole log to the terminal, alternatively you could just open the file in VS code to view it. Similarly, for each job launched a `descriptive-name.txt` file is also created which has a record the information used to launch the job (the input folder, fps, nplanes, etc.). 

To stop a job from running 


## Additional information about the hpc_pipeline

### Set up ssh keys from your Windows computer to Awoonga or Zfish
- Open powershell
- type `C:` into powershell
- Change to your home directory `cd Users/your-uq-username`, swap `your-uq-username` with your uq username
- Check if you already have an SSH key `ls .ssh`, check for a file called `id_rsa.pub`
- if no file, type `ssh-keygen`, follow prompts
- Copy key to remote server `type $env:USERPROFILE\.ssh\id_rsa.pub | ssh uqjsmith@uqjarno4-zfish.zones.eait.uq.edu.au "cat >> .ssh/authorized_keys"`, change uqjsmith to your username
- enter password
- [Optional] Repeat the above and change Zfish link to `awoonga.qriscloud.org.au` to use ssh keys with Awoonga also


### Joining data from two experiments on the same fish (Using symlinks)
Often a single fish is used in two or more sets of data collections e.g. spontaneous for several minutes as well as an assay of stimuli. In these cases the two data sets can be combined to allow suite2p to join the ROIs between both sets. The script `symlink_data.py` implements this functionality by creating symbolic links (like shortcuts on windows) in a new folder that points to both datasets, suite2p can then be run on this folder of symlinks as if it was one big data collection. 

The script shold be run on Awoonga or Flashlite (not Zfish):
```
cd hpc_pipeline
python symlink_data.py /path/to/sponaneous/data /path/to/stimuli/assay /new/output/folder/for/symlinks
```
Where `/path/to/spontaneous/data` and `/path/to/stimuli/assay` are folders containing equal numbers of fish folders with tifs inside. `/new/output/folder/for/symlinks` is the folder in which a set of new fish folders will be created with the symlinks to the original data.


### Permission denied when launching a job
If you tried to run a launch file (e.g. `./launch_TEMPLATE.sh`) and got a permission denied error, you may need to make the file executable, try the following (substituting the filename for whatever file you were trying to run
```
chmod a+x launch_TEMPLATE.sh
```
You should now be able to execute the file.

### Adding new users to Zfish
On Zfish run `uq-add-user username`

### Install magic wormhole to make debugging easier
conda install -c conda-forge magic-wormhole

### Install ANTs
The Advanced Normalisation Tools (ANTs) allow us to warp images so they can be compared within a common space. To install ANTs 
- Log into Awoonga 
- Enter command `module load CMake/3.15.0-gnu-7.2.0`
- The next two steps refer to specific sections of the final step (following the normal ANTs instructions)
- Make sure to change the install location from `/opt/ANTs` to `/home/your-username/ANTs`, replaceing `your-username` with your uq username
- In the final, "Post installation" step replace `export ANTSPATH=/opt/ANTs/bin/` with the path from the last step.
- Follow instructions here [https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS)



### External server
The restarting functionality of the hpc_pipeline is provided by the hpc_pipeline.py file which should be run on a server seperate to the computing cluster. For this server we have chosen to use the Zfish computer hosted by EAIT. Each time a job is started it moves into the background on the control server (Zfish), it will check on the computing cluster every few hours and restart any jobs that have failed. The server communicates with the HPC cluster by setting up an SSH connection using paramiko, it then executes varios bash commands on the cluster to launch and monitor the state of jobs. 

