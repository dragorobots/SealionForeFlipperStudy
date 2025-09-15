#!/usr/bin/env python3
"""
FullStroke_Extract_Complete_Data.py - Build a combined Full Stroke dataset

This script scans the Full Stroke master datasets (20-Jan, 23-Jan, 30-Jan),
filters experiments by target parameters, and extracts the actual time-series
data, zeros, and parameters into a single organized HDF5 file that downstream
Python tools can consume efficiently.

Changes (Sept 2025):
- Re-includes flow speed 0.05 m/s (23-Jan dataset)
- Re-includes stroke period 1.75 s in addition to 2.25 s
- Saves counts per source dataset to enable flow mapping downstream

Output format: HDF5 (.h5)
"""

import numpy as np
import h5py
import os
import json
from datetime import datetime

def _matches_criteria(param_vec, periods, yaw_amplitudes, paddle_transitions):
    """Return True if this parameter vector matches desired criteria.

    We expect MATLAB-style parameter vectors stored per-experiment under
    results/parameters/parameters as an (N, 1) array. For our historical
    datasets, indices map as follows (0-based):
      0: period (s)
      1: yaw amplitude (deg)
      2: roll angle (deg)
      3: paddle transition (fraction)
      [4: flow speed (m/s) if present]

    We do not filter by roll angle and we do not rely on embedded flow speed.
    """
    try:
        period = float(param_vec[0])
        yaw = float(param_vec[1])
        paddle = float(param_vec[3]) if len(param_vec) >= 4 else None
    except Exception:
        return False

    if periods is not None and period not in periods:
        return False
    if yaw_amplitudes is not None and yaw not in yaw_amplitudes:
        return False
    if paddle_transitions is not None and paddle not in paddle_transitions:
        return False
    return True


def filter_indices_by_criteria(filepath, dataset_name, periods, yaw_amplitudes, paddle_transitions):
    """Scan a master dataset and return indices of experiments matching criteria."""
    print(f"\nScanning {dataset_name} for matching experiments...")
    indices = []
    with h5py.File(filepath, 'r') as f:
        results = f['results']
        parameters_array = results['parameters']['parameters'][:]
        num_experiments = parameters_array.shape[0]
        for i in range(num_experiments):
            param_ref = parameters_array[i][0]
            param_data = f[param_ref][:].flatten()
            if _matches_criteria(param_data, periods, yaw_amplitudes, paddle_transitions):
                indices.append(i)
    print(f"  Found {len(indices)} matching experiments out of {num_experiments}")
    return indices

def extract_experiment_data(filepath, experiment_indices, dataset_name):
    """Extract data for specific experiment indices from a .mat file"""
    print(f"\nExtracting data from {dataset_name}...")
    
    extracted_data = {
        'data': [],
        'zeros': [],
        'parameters': []
    }
    
    with h5py.File(filepath, 'r') as f:
        results = f['results']
        data_array = results['data']['data'][:]
        parameters_array = results['parameters']['parameters'][:]
        zeros_array = results['zeros']['zeros'][:]
        
        print(f"  Processing {len(experiment_indices)} experiments...")
        
        for i, exp_idx in enumerate(experiment_indices):
            if i % 20 == 0:  # Progress indicator
                print(f"    Progress: {i}/{len(experiment_indices)}")
            
            # Extract data
            data_ref = data_array[exp_idx][0]
            data_data = f[data_ref][:]  # This should be the 15000x3 array
            extracted_data['data'].append(data_data)
            
            # Extract zeros
            zeros_ref = zeros_array[exp_idx][0]
            zeros_data = f[zeros_ref][:]
            extracted_data['zeros'].append(zeros_data)
            
            # Extract parameters
            param_ref = parameters_array[exp_idx][0]
            param_data = f[param_ref][:]
            extracted_data['parameters'].append(param_data)
    
    print(f"  Extracted {len(extracted_data['data'])} experiments")
    return extracted_data

def create_combined_dataset():
    """Create the final combined dataset"""
    print("=== EXTRACTING COMPLETE FULL STROKE DATA ===")
    
    # Selection criteria
    desired_periods = [1.75, 2.25]
    desired_yaws = [-70, -80, -90]
    desired_paddles = [0.5, 0.55, 0.6]

    # Source files and their flow speeds
    src = [
        ('data/raw/Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat', '20-Jan dataset (0.1 m/s)', 0.1),
        ('data/raw/Master_Data_Set_Backup/23-Jan-2023_results_FullStroke.mat', '23-Jan dataset (0.05 m/s)', 0.05),
        ('data/raw/Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat', '30-Jan dataset (0.0 m/s)', 0.0),
    ]

    all_data_parts = []
    counts = []

    for filepath, label, flow in src:
        if not os.path.exists(filepath):
            print(f"WARNING: Missing source file: {filepath} — skipping")
            counts.append(0)
            continue
        match_indices = filter_indices_by_criteria(
            filepath,
            label,
            desired_periods,
            desired_yaws,
            desired_paddles,
        )
        part = extract_experiment_data(filepath, match_indices, label)
        all_data_parts.append((part, flow))
        counts.append(len(match_indices))

    # Combine the datasets in the specified order: 20-Jan, 23-Jan, 30-Jan
    print("\n=== COMBINING DATASETS ===")
    combined_data = {'data': [], 'zeros': [], 'parameters': []}
    for part, _flow in all_data_parts:
        combined_data['data'] += part['data']
        combined_data['zeros'] += part['zeros']
        combined_data['parameters'] += part['parameters']
    
    total_experiments = len(combined_data['data'])
    print(f"Combined dataset: {total_experiments} experiments")
    
    # Add metadata
    metadata = {
        'experiment_type': 'Full Stroke',
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_datasets': [
            '20-Jan-2023_results_FullStroke.mat',
            '23-Jan-2023_results_FullStroke.mat',
            '30-Jan-2023_results_FullStroke.mat'
        ],
        'target_parameters': {
            'periods': desired_periods,
            'yaw_amplitudes': desired_yaws,
            'paddle_transitions': desired_paddles,
            'flow_speeds': [0.0, 0.05, 0.1]
        },
        'total_experiments': total_experiments,
        'experiments_from_20Jan': counts[0] if len(counts) > 0 else 0,
        'experiments_from_23Jan': counts[1] if len(counts) > 1 else 0,
        'experiments_from_30Jan': counts[2] if len(counts) > 2 else 0,
        'source_order': ['20-Jan', '23-Jan', '30-Jan'],
        'data_dimensions': {
            'time_points': 15000,
            'channels': 3,
            'channel_names': ['lift', 'thrust', 'arduino_sync']
        }
    }
    
    # Save as HDF5
    output_dir = 'data/processed/2025-01-27_ProcessedData'
    h5_filename = os.path.join(output_dir, 'FullStroke_Complete_2025-01-27.h5')
    
    print(f"\n=== SAVING TO HDF5 ===")
    print(f"Saving to: {h5_filename}")
    
    with h5py.File(h5_filename, 'w') as f:
        # Create groups
        data_group = f.create_group('data')
        zeros_group = f.create_group('zeros')
        params_group = f.create_group('parameters')
        meta_group = f.create_group('metadata')
        
        # Save experiment data
        for i in range(total_experiments):
            # Save time-series data (15000x3)
            data_group.create_dataset(f'exp_{i:03d}', data=combined_data['data'][i], 
                                    compression='gzip', compression_opts=9)
            
            # Save zeros data
            zeros_group.create_dataset(f'exp_{i:03d}', data=combined_data['zeros'][i],
                                     compression='gzip', compression_opts=9)
            
            # Save parameters as stored in the master file (vector of values)
            # Historical consumers expect a small vector dataset per experiment.
            params_group.create_dataset(f'exp_{i:03d}', data=combined_data['parameters'][i])
        
        # Save metadata
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                meta_group.attrs[key] = json.dumps(value)
            else:
                meta_group.attrs[key] = value
    
    print(f"Successfully saved {total_experiments} experiments to HDF5 format")
    
    # Also save a summary JSON for easy inspection
    summary_filename = os.path.join(output_dir, 'FullStroke_Summary_2025-01-27.json')
    with open(summary_filename, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Summary saved to: {summary_filename}")
    
    return h5_filename, total_experiments

def verify_dataset(h5_filename):
    """Verify the created dataset"""
    print(f"\n=== VERIFYING DATASET ===")
    print(f"Verifying: {h5_filename}")
    
    with h5py.File(h5_filename, 'r') as f:
        print(f"Top-level groups: {list(f.keys())}")
        
        # Check data group
        data_group = f['data']
        data_keys = list(data_group.keys())
        print(f"Data experiments: {len(data_keys)}")
        
        # Check first experiment
        first_exp = data_group[data_keys[0]]
        print(f"First experiment data shape: {first_exp.shape}")
        print(f"First experiment data type: {first_exp.dtype}")
        
        # Check parameters
        params_group = f['parameters']
        first_params = params_group[data_keys[0]]
        print(f"First experiment parameters: {first_params[:]}")
        
        # Check metadata
        meta_group = f['metadata']
        print(f"Metadata attributes: {list(meta_group.attrs.keys())}")
        print(f"Total experiments: {meta_group.attrs['total_experiments']}")
        print(f"Experiment type: {meta_group.attrs['experiment_type']}")
        
        # Show parameter distribution
        print(f"\nParameter distribution:")
        periods = []
        yaw_amps = []
        paddle_trans = []
        
        for key in data_keys[:10]:  # Check first 10
            params = params_group[key][:]
            # Params are typically shape (4,1); coerce to floats
            def _scalar(x):
                try:
                    x = np.array(x)
                    return float(x.flatten()[0])
                except Exception:
                    return float(x)
            periods.append(_scalar(params[0]))
            yaw_amps.append(_scalar(params[1]))
            paddle_trans.append(_scalar(params[3]))
        
        print(f"  Sample periods: {sorted(set(periods))}")
        print(f"  Sample yaw amplitudes: {sorted(set(yaw_amps))}")
        print(f"  Sample paddle transitions: {sorted(set(paddle_trans))}")
    
    print("Dataset verification complete!")

def main():
    """Main function"""
    try:
        # Create the complete dataset
        h5_filename, total_experiments = create_combined_dataset()
        
        # Verify the dataset
        verify_dataset(h5_filename)
        
        print(f"\n🎉 SUCCESS!")
        print(f"Created complete Full Stroke dataset with {total_experiments} experiments")
        print(f"Saved to: {h5_filename}")
        print(f"Format: HDF5 (efficient for Python processing)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

