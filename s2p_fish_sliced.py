""" s2p_fish_sliced.py
    Actually execute s2p on the the supplied fish
"""
import suite2p
import sys
import os
import datetime
import argparse
import json
from subprocess import call
import time


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('fish_abs_path', help="Absolute path to the directory with .tif files")
    parser.add_argument('output_directory', help="Absolute path to this fish's individual output folder")
    parser.add_argument('s2p_config_json', help="Path to a json file containing ops for suite2p")
    parser.add_argument('planes_left_json', help='Path to json file with a list of planes left to do')
    parser.add_argument('array_num', help="The array_number of this job")
    args = parser.parse_args()

    print(args.fish_abs_path, args.output_directory, args.s2p_config_json, args.planes_left_json, args.array_num)

    ## Load s2p file
    with open(args.s2p_config_json, 'r') as fp:
        input_ops = json.loads(fp.read())

    with open(args.planes_left_json, 'r') as fp:
        planes_left = json.loads(fp.read())

    input_fish_folder = os.path.normpath(args.fish_abs_path)
    fish_output_path = os.path.normpath(args.output_directory)
    array_num = int(args.array_num) 
    plane_num = planes_left[array_num - 1] # offset for hpc array jobs starting at 1
    print(f'planes left: {planes_left}')

    ## Define 1P ops for full fish
    ops = suite2p.default_ops()
    ops.update(input_ops)

    ## Define the db
    #output_fish_folder = os.path.join(output_base_folder, os.path.basename(input_fish_folder))
    db = {'look_one_level_down': True, # whether to look in ALL subfolders when searching for tiffs
	  'data_path': [input_fish_folder], # a list of folders with tiffs 
											 # (or folder of folders with tiffs if look_one_level_down is True, or subfolders is not empty)         
	  'fast_disk': os.environ["TMPDIR"], # string which specifies where the binary file will be stored (should be an SSD)
	  'save_folder': fish_output_path,
	}

    # classify path cannot have a ~ in it, so we need to swap ~ for users
    # home directory
    if ops.get('classifier_path'):
        if '~' in ops.get('classifier_path'):
            home_dir = os.path.expanduser('~')
            ops['classifier_path'] = ops.get('classifier_path').replace('~', home_dir)
            print(f"Updated classifer path to: {ops['classifier_path']}")

    ops['parallel_planes'] = True

    print(f"pre if: {array_num}, {len(planes_left)}, {ops.get('nplanes')}")
    if array_num == 1 and len(planes_left) == ops.get('nplanes'):
        print("OPS:", ops)
        ## Run suite2p
        opsEnd=suite2p.run_s2p(ops=ops,db=db)
    else:
        ops_location = os.path.join(fish_output_path, f'plane{plane_num}/ops.npy')
        print(f'Will look for ops file: {ops_location}')
        count = 10
        while count > 0:
            if os.path.isfile(ops_location):
                print('ops file find, launch s2p single plane')
                call([f'python -m suite2p --single_plane --ops {ops_location}'], shell=True)
                return
            print('Could not find ops file, wait 3 mins') # wait for first plane to create ops folders
            time.sleep(180)
            count -= 1
        print('ERROR: could not find ops file after 10 tries, quitting.')

if __name__ == '__main__':
    main()