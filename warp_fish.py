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
    parser.add_argument('s2p_output_path', help="Absolute path to the directory of s2p output")
    parser.add_argument('output_directory', help="Absolute path to a folder that ants output will be written to.")
    parser.add_argument('template_prefix', help="Prefix of the template to use stored in root directory of Q4414 RDM")
    args = parser.parse_args()

    fish_num = os.path.basename(args.s2p_output_path).split('fish')[1].split('_')[0]
    template_prefix = args.template_prefix

    ## if folder doesn't exist, create it
    ants_output_path = args.output_directory
    if not os.path.isdir(ants_output_path):
        print(f'Directory didnt exist, creating: {ants_output_path}')
        os.mkdir(ants_output_path)

    ## Create fish's individual meanImg of suite2p activity (as nrrd)
    meanImg_stack_nrrd_path = os.path.join(ants_output_path, f'mean_stack_{fish_num}.nrrd')
    if not os.path.isfile(meanImg_stack_nrrd_path):
        print('make suite2p mean image stack', meanImg_stack_nrrd_path)
        make_meanImg_stack(args.s2p_output_path, meanImg_stack_nrrd_path)
    else:
        print(f">>>> Fish meanImg stack existed, skipping. Filename: {meanImg_stack_nrrd_path}")


    ## Warp fish meanImg to template space to get warp matrices
    # Following process in 'register_brains_to_template.ipynb'
    #fixed_image = '/QRISdata/Q2396/ForANTs/MW_Synchotrontemplate.nrrd' # the template
    #fixed_image = '/QRISdata/Q4414/MW_Synchotrontemplate.nrrd'
    fixed_image = f'/QRISdata/Q4414/{template_prefix}template0.nrrd'
    moved_image = meanImg_stack_nrrd_path
    registration_output_name = os.path.join(ants_output_path, f'antReg_{fish_num}')
    to_template_affine_matrix = f'{registration_output_name}0GenericAffine.mat'
    num_cores = os.getenv('ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS')
    slow_registration = f"antsRegistration -d 3 --float 1 -o [{registration_output_name}, {registration_output_name}.nii] -n WelchWindowedSinc --winsorize-image-intensities [0.01,0.99] --use-histogram-matching 1 -r [{fixed_image}, {moved_image}, 1] -t rigid[0.1] -m MI[{fixed_image}, {moved_image},1,32, Regular,0.5] -c [1000x500x500x500,1e-8,10] --shrink-factors 8x4x2x1 --smoothing-sigmas 2x1x1x0vox -t Affine[0.1] -m MI[{fixed_image}, {moved_image},1,32, Regular,0.5] -c [1000x500x500x500,1e-8,10] --shrink-factors 8x4x2x1 --smoothing-sigmas 2x1x1x0vox -t SyN[0.05,6,0.5] -m CC[{fixed_image}, {moved_image},1,2] -c [1000x500x500x500x500,1e-7,10] --shrink-factors 12x8x4x2x1 --smoothing-sigmas 4x3x2x1x0vox -v 1"
    fast_registration = f"antsRegistrationSyNQuick.sh -d 3 -f {fixed_image} -m {moved_image}  -o {registration_output_name} -n {num_cores} -p f -j 1"
    job_string = slow_registration
    do_fast_registration = True
    if do_fast_registration:
        job_string = fast_registration
    print("Warp fish job string: ", job_string)
    if not os.path.isfile(to_template_affine_matrix):
        call([job_string],shell=True)
    else:
        print(f">>>> Fish already registered, skipping. output name: {to_template_affine_matrix}")


    ## Create csv of ROIs to be warped (in real space)
    output_csv = os.path.join(ants_output_path, f'ROIs_worldCoords_{fish_num}.csv')
    if not os.path.isfile(output_csv):
        z_step = get_z_step(args.s2p_output_path)
        write_csv(args.s2p_output_path, output_csv, [1.28, 1.28, z_step])
    else:
        print(f">>>> ROIs csv existed, skipping. output name: {output_csv}")


    ## Warp ROIs to template space
    templatespace_warp_image = to_template_affine_matrix.replace('0GenericAffine.mat','1InverseWarp.nii.gz')
    templatespace_rois_output_name = os.path.join(ants_output_path, f'ROIs_templatespace_{fish_num}.csv')
    template_warp_job_string = f"antsApplyTransformsToPoints -d 3 -i {output_csv} -o {templatespace_rois_output_name} -t [{to_template_affine_matrix}, 1] -t {templatespace_warp_image}"
    print('Warp to template string: ', template_warp_job_string)
    if not os.path.isfile(templatespace_rois_output_name):
        call([template_warp_job_string],shell=True)
    else:
        print(f'>>>> ROIs warped to template space exist, skipping.')


    ## Warp ROIs to zbrains space
    #to_zbrains_affine_matrix = '/QRISdata/Q2396/ForANTs/Mask_nosedown/MW_To_Zbrain0GenericAffine.mat'
    #to_zbrains_affine_matrix = '/QRISdata/Q4414/MW_To_Zbrain0GenericAffine.mat'
    to_zbrains_affine_matrix = f'/QRISdata/Q4414/{template_prefix}0GenericAffine.mat'
    warp_image = to_zbrains_affine_matrix.replace('0GenericAffine.mat','1InverseWarp.nii.gz')
    input_coords = templatespace_rois_output_name
    zbrainspace_rois_output_name = os.path.join(ants_output_path, f'ROIs_zbrainspace_{fish_num}.csv')
    job_string = f"antsApplyTransformsToPoints -d 3 -i {input_coords} -o {zbrainspace_rois_output_name} -t [{to_zbrains_affine_matrix}, 1] -t {warp_image}"
    print('Warp to zbrains string: ', job_string)
    if not os.path.isfile(zbrainspace_rois_output_name):
        call([job_string],shell=True)  
    else:
        print(f'>>>> ROIs warped to zbrains space exist, skipping.')


def get_z_step(foldername):
    ## Specific work around to keep mecp2 running, 
    ## new requirement will be to keep filenames similar to original recording folders
    ## Delete after mecp2's done processing.
    if 'symlinked' in foldername:
        print(">>>>>   HACK for original MECP2's which don't have step in filename   <<<<<<")
        mecp2_step_size = 5
        return mecp2_step_size

    if 'step' in foldername:
        z_step=int(foldername.split('step')[-1].split('_')[0]) # Takes the second instance in ones where it's been inputted twice
    else:
        #warnings.warn('Step info not present in folder name, assuming range of 250 um')
        print('>>> Step info not present in folder name, assuming range of 250 um <<<')
        assert 'SL' in foldername, 'Number of slices not present in folder name'
        z_step=250/int(foldername.split('SL')[-1].split('_')[0])
    return z_step

def make_meanImg_stack(s2p_output_path, output_nrrd):
    """ Given the folder of fish s2p output make a single 3D stack of the
        meanImage from each plane.
    """
    all_folders = glob.glob(os.path.join(s2p_output_path, 'plane*'))
    # Remove combined folder 
    for folder in all_folders:
        if 'combined' in folder:
            all_folders.remove(folder)
    # Sort folders based on digits after plane
    all_folders.sort(key=lambda x : int(x[-7:].split('plane')[1]))

    # Exclude bottom plane, due to imaging that plane is a mash of 
    # top and bottom. 
    all_folders = all_folders[1:]

    print(all_folders)
    initalised = False
    for plane_idx, plane_path in enumerate(all_folders):
        ops_path = os.path.join(plane_path, 'ops.npy')
        if not os.path.isfile(ops_path):
            continue
        ops = np.load(ops_path, allow_pickle=True).item()
        meanImg = ops.get('meanImg')
        assert meanImg is not None, f'suite2p meanImg is missing from plane {plane_idx}, cannot build meanImg stack.'
        if not initalised:
            fish_stack = np.zeros((len(all_folders),meanImg.shape[0],meanImg.shape[1]), dtype=np.float32)
            initalised = True
        fish_stack[plane_idx]=meanImg

    # Now save it as an .nrrd file with the metadata embedded
    z_step=get_z_step(s2p_output_path)
    pix_dim = 1.28
    header= {'encoding': 'raw', 'endian':'big','space dimension':3,'space directions': ([[  pix_dim,   0. ,   0. ],[  0. ,   pix_dim,   0. ],[  0. ,   0. ,  z_step]]),'space units': ['microns', 'microns', 'microns']}

    #header= {'kinds': ['domain', 'domain', 'domain'], 'units': ['micron'], 'spacings': [1.28, 1.28, z_step]} # Use hard-coded x and y pixel sizes (binning of 4)
    nrrd.write(output_nrrd, np.transpose(fish_stack,(2,1,0)), header) 

def write_csv(s2p_output_path, output_file, pix_dims=[1.28, 1.28, 5]):
    """ Create a csv file will all ROIs for the fish
    """
    planes = glob.glob(os.path.join(s2p_output_path, 'plane*'))
    # Sort folders based on digits after plane
    planes.sort(key=lambda x : int(x[-7:].split('plane')[1]))

    # Exclude bottom plane, due to imaging that plane is a mash of 
    # top and bottom. 
    planes = planes[1:]

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
        plane_cells = [] #np.empty((0, 3))
        for n in range(ncells):
            if iscell[n, 0]:
                x = stat[n]['med'][1]  # For some reason 'med' is in (y,x)
                y = stat[n]['med'][0]
                cell_coords = np.array([x, y, i]) * np.array(pix_dims)
                plane_cells.append(cell_coords)
                #plane_cells = np.concatenate((plane_cells, cell_coords))
        all_cells = np.concatenate((all_cells, np.reshape(np.array(plane_cells), (-1, 3))))

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