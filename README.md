# hpc_pipeline
This repository contains tools for automating as many steps as possible in processing calcium imaging data. It provides tools to launch and then manage jobs on the Awoonga compute cluster. A key feature of the hpc_pipeline is the ability to restart jobs that have failed due to spurious reasons such as the data storage temporarily dropping out. In particular the hpc_pipeline processes raw calcium imaging data and provides biologically relevant signals and analyses. 

# How do I process my data?

## Get Josh to add you the command server
The hpc_pipeline is controlled by an external server (the command server) which launches jobs on Awoonga and periodically checks on them. To access the server you will need to be added, give your uq staff id (or student number) to Josh who will add you.

## Get an Awoonga account
Follow instructions here [https://rcc.uq.edu.au/awoonga](https://rcc.uq.edu.au/awoonga). You may be required to undergo HPC training run by RCC, see [https://rcc.uq.edu.au/training](https://rcc.uq.edu.au/training).

## Set up the hpc_pipeline on Awoonga
Now we will need to set up the hpc_pipeline on Awoonga. First log into Awoonga using PuTTY. If you do not have PuTTY installed you can download it [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html). You probably want the '64-bit x86' version.

Once installed, open PuTTY, into the field asking for Host name type the address:
```
awoonga.qriscloud.org.au
```
Log in using the **same** UQ user account that you will use for the command server (that is, don't mix your staff and student accounts if you have both). Now we will need to make sure the hpc_pipeline knows who you are.
Throughout this document you will need to type commands into PuTTY, you can manually retype the commands or you can copy the command from this page and then Right-click on the PuTTY window. Copy this command into the PuTTY window and replace "your-user-name" with your UQ user name.
```
echo "export UQUSERNAME=your-user-name" >> ~/.bashrc
```
For example, I would type `echo "export UQUSERNAME=uqjarno4" >> ~/.bashrc`.
QRIS also requires we tell them which school we belong to at UQ, this varies between different lab members but is likely going to be `UQ-EAIT-ITEE`, `UQ-QBI` or `UQ-SCI-SBMS`. Replace "your-uq-school" with whichever is appropriate for you. If you are unsure which account is correct for you ask Josh.
```
echo "export UQSCHOOL=your-uq-school" >> ~/.bashrc
```
And now lets make sure those are used correctly, again copying this line into the PuTTY window
```
source ~/.bashrc
```
To check these are correct copy the following into the PuTTY window.
```
echo $UQUSERNAME
echo $UQSCHOOL
```
These should print your username and school string.


### Install Suite2p
We will need to download the code for [Suite2p](https://github.com/Scott-Lab-QBI/suite2p.git), but first we will make sure we are in the home directory, enter the following commands into the PuTTY window
```
cd ~/
git clone https://github.com/Scott-Lab-QBI/suite2p.git
```
Now lets go into the Suite2p folder and set up the an Anaconda environment, copy the following commands, agree to the installation instructions and default locations
```
cd suite2p
module load anaconda
conda env create -f environment.yml
```
To Activate and use the suite2p environment you can use the command
```
conda activate suite2p
```

### Download the hpc_pipeline
To install the hpc_pipeline on Awoonga we will first need to go back to the home directory and then download the code

```
cd ~/
git clone https://github.com/Scott-Lab-QBI/hpc_pipeline.git
```

## Set up the hpc_pipeline on command server
Now that the hpc_pipeline is installed on Awoonga we will also need to install it on the command server. Start a new PuTTY window to connect to the command server. Once Josh has added you you will be able to log into the server using ssh (through PuTTY) as you would normally access Awoonga. The servers host name is:
```
uqjarno4-zfish.zones.eait.uq.edu.au
```

If this is your first time logging into the command server you will need to set up the hpc_pipeline, run the following command
```
git clone git@github.com:Scott-Lab-QBI/hpc_pipeline.git
```

Now make sure the hpc_pipeline knows which user account to use when it tries to connect to awoonga, in the following command replace "your-user-name" with your UQ user name
```
echo "export UQUSERNAME=your-user-name" >> ~/.bashrc
source ~/.bashrc
```

### Set up SSH keys between command server and Awoonga
To allow the command server to access Awoonga without you there to enter your password we need to set up a pair of keys ([more info](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2)). First we will need to generate some keys for your account on the command server, use the default install location with no pass phrase.
```
ssh-keygen -t ed25519
ssh-copy-id ${UQUSERNAME}@awoonga.qriscloud.org.au
```

## Launch a job
The previous steps only need to be completed once to initially set up the hpc_pipeline. To use the pipeline, we just need to specify the details of the job to be run and then to start the job using a launch file. To do this log into the command server through ssh (using PuTTY), the hostname is (`uqjarno4-zfish.zones.eait.uq.edu.au`) 

Change into the pipeline directory 
```
cd hpc_pipeline
```

You will need a few bits of information before you can run the hpc_pipeline: 
- `JOBNAME="descriptive-name"` - A short descriptive name for the job, can be anything but its important it is unique to any other running jobs e.g. `fish8-11Spont`
- `INPUTFOLDER="/path/to/folder/with/multiple/fish/folders"` - The folder in which the fish folders to process are
- `OUTPUTFOLDER="/path/where/s2p/output/should/save"` - The folder in which the finished fish will be saved
- `S2P_CONFIG="ops_1P_whole.json"` - A JSON file containing suite2p ops

You can set all of these values in the file called `launch_TEMPLATE.sh`. You may want to make copies of this file for individual processing jobs or just edit the values in the original as necessary. To open the file we can use the nano text editor, when you are done you can save by pressng `Ctrl`+`o` and then enter. To exit press `Ctrl`+`x`. For an alternative method to using nano, see the additional information. 
```
nano launch_TEMPLATE.sh
```
Once you are sure the details are correct you can launch the job by typing
```
./launch_TEMPLATE.sh
```
The program will start running in the background, if you check the `qstat` command on Awoonga you will soon see jobs starting.


## Checking on a job or debugging
To check if the hpc_pipeline is running you can use the command 
```
ps ux | grep hpc_pipeline
```
To check the logs (which tell us what the program is doing / did) we need to know the jobname specified for the job. We can then view the logs using
```
cat descriptive-name.log
``` 
which will just paste the whole log to the screen, alternatively you could use `nano` to open the file directly or filezilla to copy the log onto your own local computer and then open it with any text editor. Similarly, for each job launched a `descriptive-name.txt` file is also created which has a record the information used to launch the job (the input folder, fps, nplanes, etc.). 



## Additional information about the hpc_pipeline

# Avoiding nano
If you prefer not to use nano you can instead copy the file to your local computer, edit it in whatever program you prefer, and then transfer the editted file back to the server.
To do this you will need to use FileZilla, if you don't have it installed you can download it [here](https://filezilla-project.org/).
Open FileZilla, click on 'File' > 'Site Manager ...', a window will pop up.
Change the Protocol to 'SFTP - SSH File Transfer Protocol' and for the hostname enter the server you want to retrieve a file from (`awoonga.qriscloud.org.au` or `uqjarno4-zfish.zones.eait.uq.edu.au`). Set the Logon Type to 'Ask for Password', Enter your UQ user name in the username field and click connect. 

Once connected the left panel shows the files on your local computer and the right panel shows the files on the server, to copy files from one computer to the other just double click on the file or click and drag from one side to the other. 

# External server
The restarting functionality of the hpc_pipeline is provided by the hpc_pipeline.py file which should be run on a server seperate to the computing cluster. Originally this server was the a zone provided by the Faculty of EAIT, see [https://help.eait.uq.edu.au/smartos/](https://help.eait.uq.edu.au/smartos/). Each time a job is started it moves into the background on the control server, it will check on the computing cluster every 6 hours and restart any jobs that have failed. 
The server communicates with the HPC cluster by setting up an SSH connection using paramiko, it then executes varios bash commands on the cluster to launch jobs and monitor the state of jobs. 

