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
from subprocess import call


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('fish_abs_path', help="Absolute path to the directory of s2p output")
    parser.add_argument('output_directory', help="Absolute path to an output folder")
    args = parser.parse_args()

    fish_num = os.path.basename(args.fish_abs_path).split('fish')[1].split('_')[0]

    ## Create fish's individual meanImg of suite2p activity (as nrrd)
    output_nrrd = os.path.join(args.output_directory, f'mean_stack_{fish_num}.nrrd')
    if not os.path.isfile(output_nrrd):
        print('make suite2p mean image stack', output_nrrd)
        make_meanImg_stack(args.fish_abs_path, output_nrrd)
    else:
        print(f"Fish meanImg stack existed, skipping. output name: {output_nrrd}")


    ## Warp fish meanImg to template space to get warp matrices
    # Following process in 'register_brains_to_template.ipynb'
    fixed_image = '/QRISdata/Q2396/ForANTs/MW_Synchotrontemplate.nrrd' # the template
    moved_image = output_nrrd  # The fish 
    output_name = os.path.join(args.output_directory, f'antReg_{fish_num}')
    affine_matrix = f'{output_name}0GenericAffine.mat'

    if not os.path.isfile(affine_matrix):
        job_string = """antsRegistration -d 3 --float 1 -o ["""+output_name+""", """+output_name+""".nii] -n WelchWindowedSinc --winsorize-image-intensities [0.01,0.99] --use-histogram-matching 1 -r ["""+fixed_image+""","""+moved_image+""", 1] -t rigid[0.1] -m MI["""+fixed_image+""","""+moved_image+""",1,32, Regular,0.5] -c [1000x500x500x500,1e-8,10] --shrink-factors 8x4x2x1 --smoothing-sigmas 2x1x1x0vox -t Affine[0.1] -m MI["""+fixed_image+""","""+moved_image+""",1,32, Regular,0.5] -c [1000x500x500x500,1e-8,10] --shrink-factors 8x4x2x1 --smoothing-sigmas 2x1x1x0vox -t SyN[0.05,6,0.5] -m CC["""+fixed_image+""","""+moved_image+""",1,2] -c [1000x500x500x500x500,1e-7,10] --shrink-factors 12x8x4x2x1 --smoothing-sigmas 4x3x2x1x0vox -v 1"""
        print("Job string: ", job_string)
        call([job_string],shell=True)
    else:
        print(f"Warp coords existed, skipping. output name: {output_nrrd}")


    ## Create csv of ROIs to be warped (in real space)
    output_csv = os.path.join(args.output_directory, f'ROIs_worldCoords_{fish_num}.csv')
    if not os.path.isfile(output_csv):
        write_csv(args.fish_abs_path, output_csv)
    else:
        print(f"ROIs csv existed, skipping. output name: {output_nrrd}")


    ## Warp ROIs to template space
    warp_image=affine_matrix.replace('0GenericAffine.mat','1InverseWarp.nii.gz')
    warped_rois_output_name = os.path.join(args.output_directory, f'ROIs_templatespace_{fish_num}.csv')
    job_string = """antsApplyTransformsToPoints -d 3 -i %s -o %s -t [%s, 1] -t %s""" % (output_csv, warped_rois_output_name, affine_matrix, warp_image)
    print('Warp to template string: ', job_string)
    if not os.path.isfile(warped_rois_output_name):
        call([job_string],shell=True)
    else:
        print(f'ROIs warped to template space exist, skipping.')


    ## Warp ROIs to zbrains space
    affine_matrix = '/QRISdata/Q2396/ForANTs/Mask_nosedown/MW_To_Zbrain0GenericAffine.mat'
    warp_image = affine_matrix.replace('0GenericAffine.mat','1InverseWarp.nii.gz')
    input_coords = warped_rois_output_name
    output_name = os.path.join(args.output_directory, f'ROIs_zbrainspace_{fish_num}.csv')
    job_string = """antsApplyTransformsToPoints -d 3 -i %s -o %s -t [%s, 1] -t %s""" % (input_coords, output_name, affine_matrix, warp_image)
    print('Warp to zbrains string: ', job_string)
    if not os.path.isfile(output_name):
        call([job_string],shell=True)  
    else:
        print(f'ROIs warped to zbrains space exist, skipping.')


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

def make_meanImg_stack(fish_abs_path, output_nrrd):
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
    pix_dim = 1.28
    header= {'encoding': 'raw', 'endian':'big','space dimension':3,'space directions': ([[  pix_dim,   0. ,   0. ],[  0. ,   pix_dim,   0. ],[  0. ,   0. ,  z_step]]),'space units': ['microns', 'microns', 'microns']}

    #header= {'kinds': ['domain', 'domain', 'domain'], 'units': ['micron'], 'spacings': [1.28, 1.28, z_step]} # Use hard-coded x and y pixel sizes (binning of 4)
    nrrd.write(output_nrrd, np.transpose(fish_stack,(2,1,0)), header) 

def write_csv(fish_abs_path, output_file, pix_dims=[1.28, 1.28, 5]):
    """ Create a csv file will all ROIs for the fish
    """
    planes = glob.glob(os.path.join(fish_abs_path, '*'))
    # Sort folders based on digits after plane
    planes.sort(key=lambda x : int(x[-7:].split('plane')[1]))

    all_cells = np.zeros((0, 3))  # will be y, x, plane co-ordinates 
    for i, plane in enumerate(planes):
        
        if not os.path.exists(os.path.join(plane, 'iscell.npy')):
            print(os.path.join(plane, 'iscell.npy'))
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
                cell_coords = np.array([x, y, i]) * np.array(pix_dims)
                plane_cells.append(cell_coords)
        all_cells = np.concatenate((all_cells, np.array(plane_cells)))

    ## Combine and then write output
    extra = np.zeros((all_cells.shape[0], 3))  # ANTs wants time, label, and comment, zero for all
    ants_all_cells = np.concatenate((all_cells, extra), axis=1)
    # TO csv, slow but i dont want to have to import pandas and other methods were a pain
    csv_rows = [ ','.join([f'{num:.2f}' for num in x]) for x in ants_all_cells]
    csv_text = "\n".join(csv_rows)

    with open(output_file, 'w') as f:
        f.write("x,y,z,t,l,c\n")
        f.write(csv_text)


if __name__ == '__main__':
    main()