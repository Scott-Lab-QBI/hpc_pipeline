""" s2p_fish.py
    Actually execute s2p on the the supplied fish
"""
import suite2p
import sys
import os
import datetime
import argparse
import json


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('fish_abs_path', help="Absolute path to the directory with .tif files")
    parser.add_argument('output_directory', help="Absolute path to this fish's individual output folder")
    parser.add_argument('s2p_config_json', help="Path to a json file containing ops for suite2p")
    args = parser.parse_args()

    print(args.fish_abs_path, args.output_directory, args.s2p_config_json)

    ## Load s2p file
    with open(args.s2p_config_json, 'r') as fp:
        input_ops = json.loads(fp.read())


    input_fish_folder = os.path.normpath(args.fish_abs_path)
    fish_output_path = os.path.normpath(args.output_directory)

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
      #'classifier_path': "~/pipelina/classifierAG.npy",
	}

    ## Debugging 
    print(f'-------------  {os.path.basename(input_fish_folder)}  -------------')
    print(f'ops: {ops}')
    print(f'db: {db}')

    ## Run suite2p
    opsEnd=suite2p.run_s2p(ops=ops,db=db)

if __name__ == '__main__':
    main()