""" Verify s2p files and print out stats for a s2p fish folder
"""

import argparse
from cmath import exp
import glob
import os
import numpy as np
import datetime
import scipy.io
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fish_s2p_path', help="Absolute path to the directory with .tif files")
    args = parser.parse_args()

    ## Do sanity checks, all planex folders have all required files etc.

    fish_s2p_path = os.path.normpath(args.fish_s2p_path)
    plane_folders = glob.glob(os.path.join(args.fish_s2p_path, 'plane*'))
    plane_folders.sort(key=lambda x : int(x[-7:].split('plane')[1]))
    fish_num = os.path.basename(fish_s2p_path).split('fish')[1].split('_')[0]

    output = []

    output.append('-' * 60)
    output.append(f'{datetime.datetime.now()}             Stats for fish {fish_num}')
    output.append('-' * 60)
    output.append(f'Fish full name: {os.path.basename(fish_s2p_path)}')
    output.append('')
    output.append(f"{'Plane':^6} {'ROIs':^8} {'Fall.mat (Mb)':^14} {'Missing files?':^15}")
    output.append('-' * 50)
    
    total_rois = 0
    all_planes_okay = True
    expected_files = ['F.npy', 'Fall.mat', 'Fneu.npy','iscell.npy','spks.npy','stat.npy','ops.npy']

    for i, plane in enumerate(plane_folders):

        files_missing = 0
        for filename in expected_files:
            
            if not os.path.isfile(os.path.join(plane, filename)):
                files_missing += 1  # technically unnecessary as trying to open will cause deletion of other

            try:
                if '.npy' in filename:
                    np.load(os.path.join(plane, filename), allow_pickle=True)
                else:
                    scipy.io.loadmat(os.path.join(plane, filename))
            except Exception as e:
                output.append(f'FAILED to load {filename}, delete plane{i} files (exc. ops.npy).')
                all_planes_okay = False
                for to_delete in expected_files[:-1]:  # Exclude last item (ops.npy)
                    full_delete_path = os.path.join(plane, to_delete)
                    
                    if os.path.isfile(full_delete_path):
                        os.remove(full_delete_path)
                    
                continue

        if files_missing > 0:
            output.append(f"{i:^6} {'-':^8} {0:^12.2f} {files_missing:^15}")
            continue  # if files missing, continue to next plane.


        # all files exist and are openable.
        ops = np.load(os.path.join(plane, 'ops.npy'), allow_pickle=True).item()
        stat = np.load(os.path.join(plane, 'stat.npy'), allow_pickle=True)
        iscell = np.load(os.path.join(plane, 'iscell.npy'), allow_pickle=True)

        num_rois = int(sum(iscell[:, 0]))
        total_rois += num_rois                

        fall_size = os.path.getsize(os.path.join(plane, 'Fall.mat'))/10**6
        
        output.append(f'{i:^6} {num_rois:^8} {fall_size:^12.2f} {files_missing:^15}')

                ## If an expected file exists, but cannot be opened, delete plane




    output.append('-' * 60)
    output.append(f'Full fish stats:')
    output.append(f'Total ROIs: {total_rois}')

    if all_planes_okay:
        output_file = os.path.join(fish_s2p_path, 's2p_stats.txt')
        with open(output_file, 'w') as fp:
            fp.write('\n'.join(output) + '\n')

if __name__ == '__main__':
    main()