#!/usr/bin/env python3
"""
Inspect Paddle stroke .mat files to understand their structure
"""

import sys
import os
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def inspect_mat_file(filepath):
    """Inspect a .mat file and print its structure"""
    print(f"\n=== Inspecting: {filepath} ===")
    
    try:
        import scipy.io
        data = scipy.io.loadmat(filepath)
        print(f"scipy.io Keys: {list(data.keys())}")
        for key, value in data.items():
            if not key.startswith('__'):
                print(f"  {key}: {type(value)} {getattr(value, 'shape', 'no shape')}")
                if hasattr(value, 'dtype'):
                    print(f"    dtype: {value.dtype}")
                if isinstance(value, np.ndarray) and value.size < 100:
                    print(f"    data: {value}")
    except Exception as e:
        print(f"scipy.io failed: {e}")
        
    try:
        import mat73
        data = mat73.loadmat(filepath)
        print(f"mat73 Keys: {list(data.keys())}")
        for key, value in data.items():
            if not key.startswith('__'):
                print(f"  {key}: {type(value)} {getattr(value, 'shape', 'no shape')}")
                if hasattr(value, 'dtype'):
                    print(f"    dtype: {value.dtype}")
                if isinstance(value, np.ndarray) and value.size < 100:
                    print(f"    data: {value}")
                elif isinstance(value, dict):
                    print(f"    dict keys: {list(value.keys())}")
                    for subkey, subvalue in list(value.items())[:10]:  # Show first 10 items
                        print(f"      {subkey}: {type(subvalue)} {getattr(subvalue, 'shape', 'no shape')}")
                        if isinstance(subvalue, np.ndarray) and subvalue.size < 50:
                            print(f"        data: {subvalue}")
                        elif isinstance(subvalue, list):
                            print(f"        list length: {len(subvalue)}")
                            if subvalue and len(subvalue) > 0:
                                print(f"        first item type: {type(subvalue[0])}")
                                if hasattr(subvalue[0], 'shape'):
                                    print(f"        first item shape: {subvalue[0].shape}")
                                elif isinstance(subvalue[0], dict):
                                    print(f"        first item keys: {list(subvalue[0].keys())[:5]}")
                        elif isinstance(subvalue, dict):
                            print(f"        dict keys: {list(subvalue.keys())[:5]}")
                            # Look deeper into nested data structures
                            for subsubkey, subsubvalue in list(subvalue.items())[:3]:
                                print(f"          {subsubkey}: {type(subsubvalue)} {getattr(subsubvalue, 'shape', 'no shape')}")
                                if isinstance(subsubvalue, list) and len(subsubvalue) > 0:
                                    print(f"            list length: {len(subsubvalue)}")
                                    if hasattr(subsubvalue[0], 'shape'):
                                        print(f"            first item shape: {subsubvalue[0].shape}")
                                        if subsubvalue[0].shape[0] < 10:  # Show sample if small
                                            print(f"            first item sample: {subsubvalue[0]}")
                    # Show more details about key fields for Paddle stroke
                    if 'data' in value:
                        print(f"      data: {type(value['data'])} {getattr(value['data'], 'shape', 'no shape')}")
                        if isinstance(value['data'], list):
                            print(f"        data list length: {len(value['data'])}")
                            if value['data'] and hasattr(value['data'][0], 'shape'):
                                print(f"        first data item shape: {value['data'][0].shape}")
                                if value['data'][0].shape[0] < 10:
                                    print(f"        first data item sample: {value['data'][0]}")
                    if 'parameters' in value:
                        print(f"      parameters: {type(value['parameters'])} {getattr(value['parameters'], 'shape', 'no shape')}")
                        if isinstance(value['parameters'], list):
                            print(f"        parameters list length: {len(value['parameters'])}")
                            if value['parameters'] and hasattr(value['parameters'][0], 'shape'):
                                print(f"        first param item shape: {value['parameters'][0].shape}")
                                if value['parameters'][0].size < 10:
                                    print(f"        first param item data: {value['parameters'][0]}")
                    if 'param_names' in value:
                        print(f"      param_names: {type(value['param_names'])} {getattr(value['param_names'], 'shape', 'no shape')}")
                        if isinstance(value['param_names'], list) and len(value['param_names']) > 0:
                            print(f"        first param_names: {value['param_names'][0]}")
    except Exception as e:
        print(f"mat73 failed: {e}")

if __name__ == "__main__":
    files = [
        "data/raw/Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat",
        "data/raw/Raw_Experimental_Data/19-Oct-2022_Paddle_Stroke_Flipper_Results/19-Oct-2022_results_PaddleStroke.mat",
        "data/raw/Raw_Experimental_Data/27-Oct-2022_Power_Stroke_Flipper_Results/27-Oct-2022_results_PaddleStroke.mat"
    ]
    
    for filepath in files:
        if os.path.exists(filepath):
            inspect_mat_file(filepath)
        else:
            print(f"File not found: {filepath}")
