#!/usr/bin/env python3
"""
FullStroke_Extract_Complete_Data.py - Extract and combine pruned Full Stroke data

This script takes the pruned experiment indices and extracts the actual time-series
data, zeros, and parameters, then combines them into a single organized structure.

Output format: HDF5 (.h5) for efficient Python processing
"""

import numpy as np
import h5py
import os
import json
from datetime import datetime

def load_pruned_indices():
    """Load the pruned experiment indices from JSON file"""
    json_file = 'data/processed/2025-01-27_ProcessedData/FullStroke_Pruned_Indices_2025-01-27.json'
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    return data['valid_indices_20Jan'], data['valid_indices_30Jan']

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
    
    # Load pruned indices
    indices_20Jan, indices_30Jan = load_pruned_indices()
    print(f"Loaded indices: {len(indices_20Jan)} from 20-Jan, {len(indices_30Jan)} from 30-Jan")
    
    # Extract data from both datasets
    data_20Jan = extract_experiment_data(
        'data/raw/Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat',
        indices_20Jan,
        '20-Jan dataset (0.1 m/s)'
    )
    
    data_30Jan = extract_experiment_data(
        'data/raw/Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat',
        indices_30Jan,
        '30-Jan dataset (0.0 m/s)'
    )
    
    # Combine the datasets
    print("\n=== COMBINING DATASETS ===")
    combined_data = {
        'data': data_20Jan['data'] + data_30Jan['data'],
        'zeros': data_20Jan['zeros'] + data_30Jan['zeros'],
        'parameters': data_20Jan['parameters'] + data_30Jan['parameters']
    }
    
    total_experiments = len(combined_data['data'])
    print(f"Combined dataset: {total_experiments} experiments")
    
    # Add metadata
    metadata = {
        'experiment_type': 'Full Stroke',
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_datasets': [
            '20-Jan-2023_results_FullStroke.mat',
            '30-Jan-2023_results_FullStroke.mat'
        ],
        'target_parameters': {
            'period': 2.25,
            'yaw_amplitudes': [-70, -80, -90],
            'paddle_transitions': [0.5, 0.55, 0.6],
            'flow_speeds': [0.0, 0.1]
        },
        'total_experiments': total_experiments,
        'experiments_from_20Jan': len(indices_20Jan),
        'experiments_from_30Jan': len(indices_30Jan),
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
            
            # Save parameters (4 values: period, yaw, roll, paddle)
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
            periods.append(params[0])
            yaw_amps.append(params[1])
            paddle_trans.append(params[3])
        
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

