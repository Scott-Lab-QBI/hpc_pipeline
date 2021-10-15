""" print out stats for a s2p fish folder
"""

import argparse
import glob
import os
import numpy as np
import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fish_s2p_path', help="Absolute path to the directory with .tif files")
    args = parser.parse_args()

    ## Do sanity checks, all planex folders have all required files etc.

    fish_s2p_path = os.path.normpath(args.fish_s2p_path)
    plane_folders = glob.glob(os.path.join(args.fish_s2p_path, 'plane*'))
    plane_folders.sort(key=lambda x : int(x[-7:].split('plane')[1]))
    fish_num = os.path.basename(fish_s2p_path).split('fish')[1].split('_')[0]

    print('-' * 60)
    print(f'{datetime.datetime.now()}             Stats for fish {fish_num}')
    print('-' * 60)
    print(f'Fish full name: {os.path.basename(fish_s2p_path)}')
    print('')
    print(f"{'Plane':^6} {'ROIs':^8} {'Fall.mat (Mb)':^14} {'Missing files?':^15}")
    print('-' * 50)
    
    total_rois = 0
    for i, plane in enumerate(plane_folders):
        ops = np.load(os.path.join(plane, 'ops.npy'), allow_pickle=True).item()
        stat = np.load(os.path.join(plane, 'stat.npy'), allow_pickle=True)

        num_rois = len(stat)
        total_rois += num_rois

        expected_files = ['F.npy', 'Fall.mat', 'Fneu.npy','iscell.npy','ops.npy','spks.npy','stat.npy']
        files_missing = 0
        for file in expected_files:
            if not os.path.isfile(os.path.join(plane, file)):
                files_missing += 1

        fall_size = os.path.getsize(os.path.join(plane, 'Fall.mat'))/10**6
        
        print(f'{i:^6} {num_rois:^8} {fall_size:^12.2f} {files_missing:^15}')


    print('-' * 60)
    print(f'Full fish stats:')
    print(f'Total ROIs: {total_rois}')

if __name__ == '__main__':
    main()