#!/usr/bin/env python3
"""
Dataset Inspector - View the contents, structure, and field names of the Full Stroke dataset
"""

import h5py
import numpy as np
import os
from datetime import datetime

def inspect_dataset():
    """Inspect the Full Stroke dataset structure and contents"""
    
    # Find the dataset file
    processed_dir = "data/processed"
    h5_files = []
    for root, dirs, files in os.walk(processed_dir):
        for file in files:
            if file.startswith("FullStroke_Complete") and file.endswith(".h5"):
                h5_files.append(os.path.join(root, file))
    
    if not h5_files:
        print("❌ No FullStroke_Complete.h5 files found!")
        return
    
    h5_file = sorted(h5_files)[-1]
    print(f"🔍 INSPECTING DATASET: {os.path.basename(h5_file)}")
    print(f"📁 Full path: {h5_file}")
    print("=" * 80)
    
    with h5py.File(h5_file, 'r') as f:
        # Top-level structure
        print("📊 TOP-LEVEL STRUCTURE:")
        print(f"   Groups: {list(f.keys())}")
        print()
        
        # Metadata inspection
        print("📋 METADATA:")
        if 'metadata' in f:
            meta_group = f['metadata']
            print(f"   Metadata attributes:")
            for attr_name, attr_value in meta_group.attrs.items():
                if isinstance(attr_value, bytes):
                    attr_value = attr_value.decode('utf-8')
                print(f"     {attr_name}: {attr_value}")
        print()
        
        # Data structure inspection
        print("📈 DATA STRUCTURE:")
        if 'data' in f:
            data_group = f['data']
            data_keys = sorted(data_group.keys(), key=lambda x: int(x.split('_')[1]))
            print(f"   Number of experiments: {len(data_keys)}")
            print(f"   Experiment keys: {data_keys[:5]}...{data_keys[-5:] if len(data_keys) > 10 else data_keys[5:]}")
            
            # Inspect first experiment
            first_key = data_keys[0]
            first_data = data_group[first_key]
            print(f"   First experiment ({first_key}):")
            print(f"     Data shape: {first_data.shape}")
            print(f"     Data type: {first_data.dtype}")
            print(f"     Data size: {first_data.size:,} elements")
            print(f"     Memory size: {first_data.nbytes:,} bytes ({first_data.nbytes/1024/1024:.2f} MB)")
        print()
        
        # Parameters structure inspection
        print("⚙️ PARAMETERS STRUCTURE:")
        if 'parameters' in f:
            params_group = f['parameters']
            print(f"   Number of parameter sets: {len(params_group.keys())}")
            
            # Inspect first parameter set
            first_key = data_keys[0]
            first_params = params_group[first_key]
            print(f"   First parameter set ({first_key}):")
            print(f"     Parameter shape: {first_params.shape}")
            print(f"     Parameter type: {first_params.dtype}")
            print(f"     Parameter values: {first_params[:].flatten()}")
        print()
        
        # Zeros structure inspection
        print("🔢 ZEROS STRUCTURE:")
        if 'zeros' in f:
            zeros_group = f['zeros']
            print(f"   Number of zero sets: {len(zeros_group.keys())}")
            
            # Inspect first zero set
            first_key = data_keys[0]
            first_zeros = zeros_group[first_key]
            print(f"   First zero set ({first_key}):")
            print(f"     Zeros shape: {first_zeros.shape}")
            print(f"     Zeros type: {first_zeros.dtype}")
            print(f"     Zeros values: {first_zeros[:].flatten()}")
        print()
        
        # Parameter distribution analysis
        print("📊 PARAMETER DISTRIBUTION:")
        if 'parameters' in f:
            periods = []
            yaw_amps = []
            roll_angles = []
            paddle_trans = []
            
            for key in data_keys:
                params = params_group[key][:]
                periods.append(float(params[0,0]))
                yaw_amps.append(float(params[1,0]))
                roll_angles.append(float(params[2,0]))
                paddle_trans.append(float(params[3,0]))
            
            print(f"   Periods: {sorted(set(periods))}")
            print(f"   Yaw amplitudes: {sorted(set(yaw_amps))}")
            print(f"   Roll angles: {sorted(set(roll_angles))}")
            print(f"   Paddle transitions: {sorted(set(paddle_trans))}")
            
            # Flow speed distribution
            flow_speeds = []
            for i, key in enumerate(data_keys):
                exp_num = int(key.split('_')[1])
                if exp_num < 63:
                    flow_speeds.append(0.1)
                else:
                    flow_speeds.append(0.0)
            print(f"   Flow speeds: {sorted(set(flow_speeds))}")
        print()
        
        # Data quality inspection
        print("🔍 DATA QUALITY INSPECTION:")
        if 'data' in f:
            # Check first few experiments
            sample_data = data_group[data_keys[0]][:]
            print(f"   Sample data (first experiment):")
            print(f"     Shape: {sample_data.shape}")
            print(f"     Min value: {sample_data.min():.6f}")
            print(f"     Max value: {sample_data.max():.6f}")
            print(f"     Mean value: {sample_data.mean():.6f}")
            print(f"     Std deviation: {sample_data.std():.6f}")
            
            # Check for data issues
            has_nan = np.isnan(sample_data).any()
            has_inf = np.isinf(sample_data).any()
            print(f"     Contains NaN: {has_nan}")
            print(f"     Contains Inf: {has_inf}")
            
            # Show sample time series
            print(f"   Sample time series (first 10 time points):")
            print(f"     Channel 0 (Lift):  {sample_data[0, :10]}")
            print(f"     Channel 1 (Thrust): {sample_data[1, :10]}")
            print(f"     Channel 2 (Arduino): {sample_data[2, :10]}")
        print()
        
        # File size information
        print("💾 FILE INFORMATION:")
        file_size = os.path.getsize(h5_file)
        print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"   Created: {datetime.fromtimestamp(os.path.getctime(h5_file))}")
        print(f"   Modified: {datetime.fromtimestamp(os.path.getmtime(h5_file))}")
        print()
        
        # Summary
        print("✅ DATASET SUMMARY:")
        print(f"   ✅ Total experiments: {len(data_keys)}")
        print(f"   ✅ Data dimensions: {first_data.shape}")
        print(f"   ✅ Time points per experiment: {first_data.shape[1]:,}")
        print(f"   ✅ Sampling rate: 500 Hz")
        print(f"   ✅ Total duration per experiment: {first_data.shape[1]/500:.1f} seconds")
        print(f"   ✅ Data format: HDF5 (efficient for Python)")
        print(f"   ✅ Ready for analysis!")

if __name__ == "__main__":
    inspect_dataset()
