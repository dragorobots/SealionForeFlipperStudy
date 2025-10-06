#!/usr/bin/env python3
"""
Analyze Power Stroke Data Structure
This script loads and analyzes the Power stroke MATLAB data files to understand
the structure, parameters, and data organization.
"""

import h5py
import numpy as np
import os
from datetime import datetime

def analyze_power_stroke_structure():
    """Analyze the structure of Power stroke data files"""
    
    print("=== POWER STROKE DATA STRUCTURE ANALYSIS ===")
    print(f"Analysis started: {datetime.now()}")
    print()
    
    # File paths
    data_dir = "data/raw/Master_Data_Set_Backup"
    file_1 = os.path.join(data_dir, "14-Oct-2022_results_PowerStroke.mat")
    file_2 = os.path.join(data_dir, "07-Oct-2022_results_PowerStroke.mat")
    
    # Check if files exist
    if not os.path.exists(file_1):
        print(f"Error: File not found: {file_1}")
        return
    if not os.path.exists(file_2):
        print(f"Error: File not found: {file_2}")
        return
    
    print("Loading Power stroke data files...")
    
    # Load first dataset
    print(f"Loading: {file_1}")
    with h5py.File(file_1, 'r') as f:
        results_1 = {}
        for key in f.keys():
            if key != '#refs#':
                if isinstance(f[key], h5py.Group):
                    # Handle groups (like 'results')
                    results_1[key] = {}
                    for subkey in f[key].keys():
                        if subkey != '#refs#':
                            results_1[key][subkey] = f[key][subkey][:]
                else:
                    # Handle datasets
                    results_1[key] = f[key][:]
    
    # Load second dataset  
    print(f"Loading: {file_2}")
    with h5py.File(file_2, 'r') as f:
        results_2 = {}
        for key in f.keys():
            if key != '#refs#':
                if isinstance(f[key], h5py.Group):
                    # Handle groups (like 'results')
                    results_2[key] = {}
                    for subkey in f[key].keys():
                        if subkey != '#refs#':
                            results_2[key][subkey] = f[key][subkey][:]
                else:
                    # Handle datasets
                    results_2[key] = f[key][:]
    
    print("Data loaded successfully!")
    print()
    
    # Analyze structure
    print("=== STRUCTURE ANALYSIS ===")
    
    # Print available keys
    print("Available keys in 14-Oct-2022 dataset:")
    for key in results_1.keys():
        print(f"  {key}: {type(results_1[key])}, shape: {results_1[key].shape if hasattr(results_1[key], 'shape') else 'N/A'}")
    
    print()
    print("Available keys in 07-Oct-2022 dataset:")
    for key in results_2.keys():
        print(f"  {key}: {type(results_2[key])}, shape: {results_2[key].shape if hasattr(results_2[key], 'shape') else 'N/A'}")
    
    print()
    
    # Analyze parameter settings
    print("=== PARAMETER SETTINGS ===")
    
    # Flow speed settings
    if 'Flow_Speed_settings' in results_1:
        print("Flow Speed Settings:")
        print(f"  14-Oct-2022: {results_1['Flow_Speed_settings']}")
        print(f"  07-Oct-2022: {results_2['Flow_Speed_settings']}")
    
    # Yaw amplitude settings
    if 'y_amp_settings' in results_1:
        print("Yaw Amplitude Settings:")
        print(f"  14-Oct-2022: {results_1['y_amp_settings']}")
        print(f"  07-Oct-2022: {results_2['y_amp_settings']}")
    
    # Roll power angle settings
    if 'roll_pow_ang_settings' in results_1:
        print("Roll Power Angle Settings:")
        print(f"  14-Oct-2022: {results_1['roll_pow_ang_settings']}")
        print(f"  07-Oct-2022: {results_2['roll_pow_ang_settings']}")
    
    # Period settings
    if 'period_settings' in results_1:
        print("Period Settings:")
        print(f"  14-Oct-2022: {results_1['period_settings']}")
        print(f"  07-Oct-2022: {results_2['period_settings']}")
    
    print()
    
    # Data analysis
    print("=== DATA ANALYSIS ===")
    
    # Analyze data ranges if data exists
    if 'data' in results_1 and 'data' in results_2:
        print("Data shapes:")
        print(f"  14-Oct-2022 data: {results_1['data'].shape}")
        print(f"  07-Oct-2022 data: {results_2['data'].shape}")
        
        # Analyze data ranges
        print("Data ranges (14-Oct-2022):")
        if len(results_1['data'].shape) >= 2:
            print(f"  Channel 0 (Thrust): {np.min(results_1['data'][0,:]):.3f} to {np.max(results_1['data'][0,:]):.3f}")
            print(f"  Channel 1 (Lift): {np.min(results_1['data'][1,:]):.3f} to {np.max(results_1['data'][1,:]):.3f}")
            if results_1['data'].shape[0] > 2:
                print(f"  Channel 2 (Arduino): {np.min(results_1['data'][2,:]):.3f} to {np.max(results_1['data'][2,:]):.3f}")
        
        print("Data ranges (07-Oct-2022):")
        if len(results_2['data'].shape) >= 2:
            print(f"  Channel 0 (Thrust): {np.min(results_2['data'][0,:]):.3f} to {np.max(results_2['data'][0,:]):.3f}")
            print(f"  Channel 1 (Lift): {np.min(results_2['data'][1,:]):.3f} to {np.max(results_2['data'][1,:]):.3f}")
            if results_2['data'].shape[0] > 2:
                print(f"  Channel 2 (Arduino): {np.min(results_2['data'][2,:]):.3f} to {np.max(results_2['data'][2,:]):.3f}")
    
    print()
    
    # Summary
    print("=== SUMMARY ===")
    if 'data' in results_1 and 'data' in results_2:
        total_experiments = results_1['data'].shape[1] + results_2['data'].shape[1]
        print(f"Total experiments: {total_experiments}")
        print(f"  - 14-Oct-2022: {results_1['data'].shape[1]} experiments")
        print(f"  - 07-Oct-2022: {results_2['data'].shape[1]} experiments")
    
    print()
    print("Analysis complete!")
    
    return {
        'results_1': results_1,
        'results_2': results_2,
        'total_experiments': total_experiments if 'total_experiments' in locals() else 0
    }

if __name__ == "__main__":
    analyze_power_stroke_structure()
