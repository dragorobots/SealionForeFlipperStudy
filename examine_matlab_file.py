#!/usr/bin/env python3
"""
Examine MATLAB v7.3 file structure
"""

import h5py
import numpy as np
import os

def examine_matlab_file(file_path):
    """Examine the structure of a MATLAB v7.3 file"""
    
    print(f"Examining: {file_path}")
    print("=" * 50)
    
    with h5py.File(file_path, 'r') as f:
        print("Top-level keys:")
        for key in f.keys():
            print(f"  {key}: {type(f[key])}")
            
        # If there's a 'results' group, examine it
        if 'results' in f:
            print("\nResults group contents:")
            results_group = f['results']
            for key in results_group.keys():
                item = results_group[key]
                print(f"  {key}: {type(item)}")
                if hasattr(item, 'shape'):
                    print(f"    Shape: {item.shape}")
                if hasattr(item, 'dtype'):
                    print(f"    Dtype: {item.dtype}")
                    
                # If it's a group, examine its contents
                if isinstance(item, h5py.Group):
                    print(f"    Group contents:")
                    for subkey in item.keys():
                        subitem = item[subkey]
                        print(f"      {subkey}: {type(subitem)}")
                        if hasattr(subitem, 'shape'):
                            print(f"        Shape: {subitem.shape}")
                        if hasattr(subitem, 'dtype'):
                            print(f"        Dtype: {subitem.dtype}")

if __name__ == "__main__":
    # Examine both Power stroke files
    files = [
        "data/raw/Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat",
        "data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat"
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            examine_matlab_file(file_path)
            print("\n")
        else:
            print(f"File not found: {file_path}")
