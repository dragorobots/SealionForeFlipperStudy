#!/usr/bin/env python3
"""
Example_Analysis.py - Example of how to analyze the Full Stroke dataset

This script demonstrates how to load and analyze the pruned Full Stroke data
using Python and the HDF5 format.
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import json

def load_experiment_data(h5_filename, experiment_id):
    """Load data for a specific experiment"""
    with h5py.File(h5_filename, 'r') as f:
        exp_key = f'exp_{experiment_id:03d}'
        
        # Load data (3x15000: lift, thrust, arduino)
        data = f['data'][exp_key][:]
        
        # Load parameters
        params = f['parameters'][exp_key][:]
        period = params[0,0]
        yaw = params[1,0]
        roll = params[2,0]
        paddle = params[3,0]
        
        # Load zeros
        zeros = f['zeros'][exp_key][:]
        
        return data, zeros, (period, yaw, roll, paddle)

def analyze_single_experiment(h5_filename, experiment_id=0):
    """Analyze a single experiment"""
    print(f"=== ANALYZING EXPERIMENT {experiment_id} ===")
    
    data, zeros, params = load_experiment_data(h5_filename, experiment_id)
    period, yaw, roll, paddle = params
    
    print(f"Parameters:")
    print(f"  Period: {period:.2f}s")
    print(f"  Yaw: {yaw:.0f}°")
    print(f"  Roll: {roll:.0f}°")
    print(f"  Paddle: {paddle:.2f}")
    
    print(f"\nData shape: {data.shape}")
    print(f"Time points: {data.shape[1]}")
    print(f"Channels: {data.shape[0]} (lift, thrust, arduino)")
    
    # Basic statistics
    lift_data = data[0, :]  # First channel
    thrust_data = data[1, :]  # Second channel
    arduino_data = data[2, :]  # Third channel
    
    print(f"\nForce Statistics:")
    print(f"  Lift - Min: {lift_data.min():.3f}, Max: {lift_data.max():.3f}, Mean: {lift_data.mean():.3f}")
    print(f"  Thrust - Min: {thrust_data.min():.3f}, Max: {thrust_data.max():.3f}, Mean: {thrust_data.mean():.3f}")
    
    # Arduino signal analysis
    arduino_changes = np.diff(arduino_data)
    sync_points = np.where(np.abs(arduino_changes) > 0.5)[0]
    print(f"  Arduino sync points: {len(sync_points)}")
    
    return data, zeros, params

def compare_flow_speeds(h5_filename):
    """Compare experiments with different flow speeds"""
    print(f"\n=== COMPARING FLOW SPEEDS ===")
    
    with h5py.File(h5_filename, 'r') as f:
        # Get metadata
        meta = f['metadata']
        total_experiments = meta.attrs['total_experiments']
        experiments_20Jan = meta.attrs['experiments_from_20Jan']
        
        print(f"Total experiments: {total_experiments}")
        print(f"20-Jan experiments (0.1 m/s): {experiments_20Jan}")
        print(f"30-Jan experiments (0.0 m/s): {total_experiments - experiments_20Jan}")
        
        # Compare first experiment from each flow speed
        print(f"\nComparing first experiment from each flow speed:")
        
        # 20-Jan (0.1 m/s) - first experiment
        data_01, zeros_01, params_01 = load_experiment_data(h5_filename, 0)
        print(f"  0.1 m/s - Thrust range: [{data_01[1,:].min():.3f}, {data_01[1,:].max():.3f}]")
        
        # 30-Jan (0.0 m/s) - first experiment from 30-Jan dataset
        data_00, zeros_00, params_00 = load_experiment_data(h5_filename, experiments_20Jan)
        print(f"  0.0 m/s - Thrust range: [{data_00[1,:].min():.3f}, {data_00[1,:].max():.3f}]")

def parameter_sweep_analysis(h5_filename):
    """Analyze the parameter sweep"""
    print(f"\n=== PARAMETER SWEEP ANALYSIS ===")
    
    with h5py.File(h5_filename, 'r') as f:
        data_keys = list(f['data'].keys())
        
        # Collect all parameters
        all_params = []
        for key in data_keys:
            params = f['parameters'][key][:]
            all_params.append(params.flatten())
        
        all_params = np.array(all_params)
        
        print(f"Parameter combinations:")
        print(f"  Periods: {sorted(set(all_params[:, 0]))}")
        print(f"  Yaw amplitudes: {sorted(set(all_params[:, 1]))}")
        print(f"  Roll angles: {sorted(set(all_params[:, 2]))}")
        print(f"  Paddle transitions: {sorted(set(all_params[:, 3]))}")
        
        # Count combinations
        unique_combinations = len(set(tuple(row) for row in all_params))
        print(f"  Unique parameter combinations: {unique_combinations}")

def main():
    """Main analysis function"""
    h5_filename = 'data/processed/2025-01-27_ProcessedData/FullStroke_Complete_2025-01-27.h5'
    
    print("=== FULL STROKE DATA ANALYSIS EXAMPLE ===")
    print(f"Dataset: {h5_filename}")
    
    # Analyze a single experiment
    data, zeros, params = analyze_single_experiment(h5_filename, 0)
    
    # Compare flow speeds
    compare_flow_speeds(h5_filename)
    
    # Parameter sweep analysis
    parameter_sweep_analysis(h5_filename)
    
    print(f"\n🎉 Analysis complete!")
    print(f"✅ Dataset is working correctly")
    print(f"✅ Ready for your research analysis!")

if __name__ == "__main__":
    main()

