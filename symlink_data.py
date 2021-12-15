""" symlink_data.py
    Given two folders of calcium imaging data recorded from the same fish
    on two tasks, create a new folder with symbolic links joining the two
    datasets as if they were one continuous dataset.
"""

import argparse
import os
import glob

def main():

    parser = argparse.ArgumentParser(description="Symlink two datasets together.")
    parser.add_argument('exp_folders', nargs='+', default=[], help='Experiment folder in order they should be linked')
    parser.add_argument('symlinked_folder', help='New folder where sym links should go')
    args = parser.parse_args()

    ## If output folder doesn't exist, create
    if not os.path.isdir(args.symlinked_folder):
        os.makedirs(args.symlinked_folder)


    ## Create a list of fish_nums that we will expect to remain constant
    #   sample from first folder
    fish_folders = glob.glob(os.path.join(args.exp_folders[0], '*fish*'))
    get_fish_num = lambda path : os.path.basename(path).split('fish')[1].split('_')[0]
    fish_nums = [get_fish_num(fish_path) for fish_path in fish_folders]


    for i, fish_num in enumerate(fish_nums):
        sym_link_index = 0
        mappings = []
        print(f'For fish: {fish_num}')

        ## Make a directory in output folder for this fish
        folder_details = f"{fish_folders[i].split('/')[-1].strip('.ome.tif')}_stitched" # This will be the experiments details e.g. MW_synchaud_20210304_scn1lab_fish03_2Hz_range250_step5_exposure10_power20_range245_step5_exposure10_power20
        ## Hack of converting spon, spont, spontaneous, Spontaneous, Spon, Spont, aud, Aud, etc. -> symlinked
        #exp_names = ['spontaneous','Spontaneous', 'spont','Spont', 'spon', 'Spon','auditory','Auditory','aud','Aud']
        #for name in exp_names:
        #    folder_details = folder_details.replace(name, 'symlinked') 
        fish_output_dir = os.path.join(args.symlinked_folder, folder_details)
        if not os.path.isdir(fish_output_dir):
            os.makedirs(fish_output_dir)

        for exp_folder in args.exp_folders:
            
            print(f'  For exp_folder: {os.path.basename(exp_folder)}')

            # Need to get the fish_dir name here since this changes between exps
            # Use fish_idx to keep fish in order
            fish_dir = glob.glob(os.path.join(exp_folder, f'*fish{int(fish_num):02}*'))[0]

            ## Go through all tifs for this fish and experiment making links
            all_tifs = glob.glob(os.path.join(fish_dir, '*.tif'))
            all_tifs.sort(key=lambda path : get_tif_index(path))

            for tif in all_tifs:
                symlink_tiff_name = f'MMStack_Pos0_{sym_link_index}.ome.tif'
                if sym_link_index == 0:
                    symlink_tiff_name = f'MMStack_Pos0.ome.tif'

                symlink_full_path = os.path.join(fish_output_dir, symlink_tiff_name)
                os.symlink(tif, symlink_full_path)
                print(f'    {tif} -> {symlink_full_path}')
                mappings.append(f'{tif} -> {symlink_full_path}')
                sym_link_index += 1
        
        ## make record of what was mapped where
        with open(os.path.join(fish_output_dir, 'symlinked_files.txt'), 'w') as fp:
            fp.write('This file lists which original tif files got mapped to which symlinks.\n')
            for link in mappings:
                fp.write(link + '\n')


def get_tif_index(path):
    if 'MMStack_Pos0.ome' in path:
        return 0
    return int(path.split('MMStack_Pos0_')[1].split('.ome')[0])


if __name__ == '__main__':
    main()