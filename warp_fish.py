""" warp_fish.py
Use ANTs to warp a fish to zbrains
"""

import nrrd
import glob
import numpy as np
import os
import argparse
import re
import warnings


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('fish_abs_path', help="Absolute path to the directory of s2p output")
    parser.add_argument('output_directory', help="Absolute path to an output folder")
    args = parser.parse_args()

    fish_num = os.path.basename(args.fish_abs_path).split('fish')[1].split('_')[0]

    ## Create fish's individual warp coords
    output_nrrd = os.path.join(args.output_directory, f'mean_stack_{fish_num}.nrrd')
    print(output_nrrd)
    make_single_stack(args.fish_abs_path, output_nrrd)
    return

    ## Create csv if not there
    output_csv = os.path.join(args.output_directory, f'ROIs_{fish_num}.csv')
    if not os.path.isfile(output_csv):
        write_csv(args.fish_abs_path, output_csv)

    ## Warp fish to template space


    ## Warp fish to zBrains space



def create_fish_warp():
    #test3='D:\Scn_synchotron\Test_3D_stacks'#'D:/Maya/Suite2p_output'
    temp=file_locations(test3)
    fishstack=make_3D_stack(temp)


def get_range(foldername):
    assert os.path.isdir(foldername)
    if 'step' not in foldername:
        nplanes=int(foldername.rsplit('SL')[-1].split('_')[0])
    else:
        slrange=int(foldername.rsplit('range')[-1].split('_')[0])
        slstep=int(foldername.rsplit('step')[-1].split('_')[0])
        nplanes=int((slrange/slstep)+1)
    return nplanes

def get_z_step(foldername):
    if 'step' in foldername:
        z_step=int(foldername.split('step')[-1].split('_')[0]) # Takes the second instance in ones where it's been inputted twice
    else:
        warning.warn('Step info not present in folder name, assuming range of 250 um')
        assert 'SL' in foldername, 'Number of slices not present in folder name'
        z_step=250/int(foldername.split('SL')[-1].split('_')[0])
    return z_step

def file_locations(basefolder):
    # Gets all of the file locations for one fish
    assert os.path.isdir(basefolder)
    suite2p_output_folder_list=glob.glob(basefolder+'/*/')
    fish_folders=list()
    slice_orders=list()
    regex=re.compile(".+_(\d+)_.+fish(\d+).+")
    fish_list=[''.join(regex.match(foldername).groups()) for foldername in suite2p_output_folder_list]
    fish_list=set(fish_list)
    #print(fish_list)
    #print(suite2p_output_folder_list)
    for fish in fish_list: #suite2p_output_folder in suite2p_output_folder_list:
        output_folders=[foldername for foldername in suite2p_output_folder_list if ''.join(regex.match(foldername).groups())==fish]
        #print(output_folders)
        nplanes=get_range(output_folders[0])
        fish_folder=list()
        slice_order=list()
        #assert os.path.isdir(suite2p_output_folder)
        #assert os.path.isdir(suite2p_output_folder+'/plane0')
        if 'Slice' in output_folders[0]:
            for folder in output_folders:
                assert 'Slice' in folder, 'All folders for this fish should have slice in their name'
                assert os.path.isdir(folder+'/plane0'), 'No suite2p output found in '+folder
                fish_folder.append(folder+'/plane0')
                slice_number=int(folder.split('Slice')[1].split('_')[0])-1
                slice_order.append(slice_number)
        else:
            fish_folder=glob.glob(output_folders[0]+'/*/')
            slice_order=[int(folder.split('plane')[1].split('\\')[0]) for folder in fish_folder]
        assert len(fish_folder)==nplanes, 'Number of folders does not match expected number of planes'
        fish_folders.append(fish_folder)
        slice_orders.append(slice_order)            
    fish_folders=zip(fish_folders, slice_orders)    
    return list(fish_folders) #Returns a list of fish with a sub-list for each containing all the folders in which to find the mean tiffs

def make_3D_stack(fish_folders):
    regex=re.compile(".+_(\d+)_.+fish(\d+).+")
    for folders in fish_folders:
        counter=0
        for i,slicefolder in enumerate(folders[0]):
            slice_number=folders[1][i]
            if os.path.isfile(slicefolder+'/ops.npy'):
                ops=np.load(slicefolder + '/ops.npy',allow_pickle=True).item()
                meanImg=ops['meanImg']
                #print(meanImg.shape)
                if counter==0: #Make empty stack to fill in
                    fish_stack=np.zeros((len(folders[0]),meanImg.shape[0],meanImg.shape[1]), dtype='uint16')
                    counter=1
                    #print(slicefolder)
                    fishid=''.join(regex.match(slicefolder).groups()) 
                    #print(fish_stack.shape)
                fish_stack[slice_number]=meanImg #Insert mean image from that slice to its rightful location 
                
            else:
                warnings.warn('No ops file found in '+slicefolder)
        # Now save it as an .nrrd file with the metadata embedded
        basefolder=Path(slicefolder).parents[1]
        filename=str(basefolder)+os.path.sep+fishid+'.nrrd'
        print(filename)
        z_step=get_z_step(slicefolder)
        header= {'kinds': ['domain', 'domain', 'domain'], 'units': ['micron'], 'spacings': [1.28, 1.28, z_step]} # Use hard-coded x and y pixel sizes (binning of 4)
        nrrd.write(filename,np.transpose(fish_stack,(2,1,0)),header)   
                
    return fish_stack

def make_single_stack(fish_abs_path, output_nrrd):
    """ Given the folder of fish s2p output make a single 3D stack of the
        meanImage from each plane.
    """
    all_folders = glob.glob(os.path.join(fish_abs_path, '*'))
    # Remove combined folder 
    for folder in all_folders:
        if 'combined' in folder:
            all_folders.remove(folder)
    # Sort folders based on digits after plane
    all_folders.sort(key=lambda x : int(x[-7:].split('plane')[1]))
    # TODO : Verify planes are in order else stack will not be aligned
    print(all_folders)
    initalised = False
    for plane_idx, plane_path in enumerate(all_folders):
        ops_path = os.path.join(plane_path, 'ops.npy')
        if not os.path.isfile(ops_path):
            continue
        ops = np.load(ops_path, allow_pickle=True).item()
        meanImg = ops.get('meanImg')
        if not initalised:
            fish_stack = np.zeros((len(all_folders),meanImg.shape[0],meanImg.shape[1]), dtype='uint16')
            initalised = True
        fish_stack[plane_idx]=meanImg

    # Now save it as an .nrrd file with the metadata embedded
    z_step=get_z_step(fish_abs_path)
    header= {'kinds': ['domain', 'domain', 'domain'], 'units': ['micron'], 'spacings': [1.28, 1.28, z_step]} # Use hard-coded x and y pixel sizes (binning of 4)
    nrrd.write(output_nrrd, np.transpose(fish_stack,(2,1,0)), header) 

def write_csv(fish_abs_path, output_file):
    """ Create a csv file will all ROIs for the fish
    """
    planes = glob.glob(os.path.join(fish_abs_path, '*'))
    #print('all planes:', planes)

    all_cells = np.zeros((0, 3))  # will be y, x, plane co-ordinates 
    for i, plane in enumerate(planes):
        
        if not os.path.exists(os.path.join(plane, 'iscell.npy')):
            raise Exception(f'Plane {i} doesn\'t have iscell.npy, cannot continue')
        
        # load fish
        iscell = np.load(os.path.join(plane, 'iscell.npy'), allow_pickle=True)
        stat = np.load(os.path.join(plane, 'stat.npy'), allow_pickle=True)
        ncells = iscell.shape[0]
        
        # Get all cells in this plane
        plane_cells = []
        for n in range(ncells):
            if iscell[n, 0]:
                # TODO : what is med? are we sure this is x and y? this needs revising
                x = stat[n]['med'][1]  # For some reason 'med' is in (y,x)
                y = stat[n]['med'][0]
                cell_coords = np.array([x, y, i])
                plane_cells.append(cell_coords)
        all_cells = np.concatenate((all_cells, np.array(plane_cells)))

    ## Combine and then write output
    extra = np.zeros((all_cells.shape[0], 3))  # ANTs wants time, label, and comment, zero for all
    ants_all_cells = np.concatenate((all_cells, extra), axis=1)
    # TO csv, slow but i dont want to have to import pandas and other methods were a pain
    csv_rows = [ ','.join([str(num) for num in x]) for x in ants_all_cells]
    csv_text = "\n".join(csv_rows)

    with open(output_file, 'w') as f:
        f.write("x,y,z,t,l,c\n")
        f.write(csv_text)


if __name__ == '__main__':
    main()