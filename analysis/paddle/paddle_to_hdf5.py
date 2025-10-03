#!/usr/bin/env python3
"""
Convert Paddle stroke .mat files to GUI-compatible HDF5 format.

This script processes Paddle stroke experimental data from .mat files and converts
them to the same HDF5 format used by the Full stroke GUI.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import h5py


def try_import(name: str):
    """Try importing a module and return it or None."""
    try:
        return __import__(name)
    except ImportError:
        return None


def _param_map(params: Dict[str, Any]) -> Dict[str, float]:
    """Normalize parameter keys and enforce absolute sweep/twist."""
    # Map parameter names to canonical terms
    flow = params.get('flow_speed', params.get('flow', 0.0))
    period = params.get('period', params.get('stroke_period', 0.0))
    sweep_raw = params.get('yaw_amplitude', params.get('sweep', 0.0))
    twist_raw = params.get('roll_angle', params.get('twist', 0.0))
    overlap = params.get('paddle_transition', params.get('phase_overlap', 0.0))
    
    return {
        'flow': float(flow),
        'stroke_period': float(period),
        'sweep': float(abs(sweep_raw)),
        'twist': float(abs(twist_raw)),
        'overlap': float(overlap)
    }


def _resample_to_phase(time: np.ndarray, y: np.ndarray, num: int = 1001) -> Tuple[np.ndarray, np.ndarray]:
    """Normalize time to phase 0..1 and resample to a uniform grid."""
    if len(time) == 0 or len(y) == 0:
        return np.array([]), np.array([])
    
    # Normalize time to phase [0, 1]
    phase = (time - time.min()) / (time.max() - time.min())
    
    # Create uniform phase grid
    phase_grid = np.linspace(0, 1, num)
    
    # Interpolate signal to uniform grid
    y_interp = np.interp(phase_grid, phase, y)
    
    return phase_grid, y_interp


def _load_mat(path: str) -> Dict[str, Any]:
    """Load a .mat file using mat73 (for v7.3 files)."""
    mat73 = try_import('mat73')
    if mat73 is None:
        raise ImportError("mat73 is required for Paddle stroke .mat files")
    
    try:
        return mat73.loadmat(path)
    except Exception as e:
        raise RuntimeError(f"Failed to load {path}: {e}")


def _find_trials_paddle_layout(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle the Paddle stroke layout: results['data'] is list of trials,
    results['parameters'] is list of parameter arrays.
    """
    trials: List[Dict[str, Any]] = []
    
    # Paddle stroke structure: results['data'] is the trials list
    data_arr = d.get('data')
    params_arr = d.get('parameters')
    
    if data_arr is None or params_arr is None:
        return trials

    data_list = list(data_arr) if isinstance(data_arr, list) else [data_arr]
    params_list = list(params_arr) if isinstance(params_arr, list) else [params_arr]
    n = min(len(data_list), len(params_list))

    for i in range(n):
        # Paddle stroke: trial data is numpy array (7500, 3)
        trial_data = data_list[i]  # numpy array (7500, 3)
        param_data = params_list[i]  # numpy array (4,)
        
        if not isinstance(trial_data, np.ndarray) or trial_data.shape != (7500, 3):
            continue
        if not isinstance(param_data, np.ndarray) or param_data.shape != (4,):
            continue
            
        # Extract time, lift, thrust from trial data
        time_vector = trial_data[:, 0]  # First column: time
        lift_data = trial_data[:, 1]    # Second column: lift
        thrust_data = trial_data[:, 2]  # Third column: thrust
        
        # Extract parameters: [Period, Yaw, Roll, Motor_power]
        period = float(param_data[0])
        yaw_amplitude = float(param_data[1])  # sweep
        roll_angle = float(param_data[2])     # twist
        flow_speed = float(param_data[3])     # flow
        
        # Create trial dict for Paddle stroke data
        tr: Dict[str, Any] = {
            'time': time_vector,
            'lift': lift_data, 
            'thrust': thrust_data,
            'params': {
                'period': period,
                'yaw_amplitude': yaw_amplitude,  # sweep
                'roll_angle': roll_angle,         # twist  
                'flow_speed': flow_speed,         # flow
                'experiment_id': i + 1
            }
        }
        trials.append(tr)

    return trials


def _group_key(p: Dict[str, float]) -> Tuple[float, float, float, float, float]:
    return (p['flow'], p['sweep'], p['twist'], p['stroke_period'], p['overlap'])


def process_files(paths: List[str], out_path: str, resample_n: int = 1001) -> None:
    """Process Paddle stroke .mat files and save to HDF5."""
    # Collect trials from all inputs
    all_trials: List[Dict[str, Any]] = []
    
    for path in paths:
        print(f"Loading {path}...")
        try:
            data = _load_mat(path)
            results = data.get('results', {})
            trials = _find_trials_paddle_layout(results)
            print(f"Found {len(trials)} trials in {path}")
            all_trials.extend(trials)
        except Exception as e:
            print(f"WARN: failed to process {path}: {e}")
            continue
    
    if not all_trials:
        raise RuntimeError("No trials found in inputs.")
    
    print(f"Total trials: {len(all_trials)}")
    
    # Group trials by parameters
    groups: Dict[Tuple[float, float, float, float, float], List[Dict[str, Any]]] = {}
    
    for trial in all_trials:
        # Normalize parameters
        params = _param_map(trial['params'])
        key = _group_key(params)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(trial)
    
    print(f"Parameter groups: {len(groups)}")
    
    # Create HDF5 file
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with h5py.File(out_path, 'w') as f:
        # Create datasets for each parameter group
        for (flow, sweep, twist, period, overlap), trials in groups.items():
            group_name = f"flow_{flow:.1f}_sweep_{sweep:.0f}_twist_{twist:.0f}_period_{period:.2f}_overlap_{overlap:.2f}"
            grp = f.create_group(group_name)
            
            # Store parameters as attributes
            grp.attrs['flow'] = flow
            grp.attrs['sweep'] = sweep
            grp.attrs['twist'] = twist
            grp.attrs['stroke_period'] = period
            grp.attrs['overlap'] = overlap
            grp.attrs['num_trials'] = len(trials)
            
            # Resample all trials to uniform phase grid
            phase_grid = np.linspace(0, 1, resample_n)
            
            # Stack all trials for each channel
            lift_trials = []
            thrust_trials = []
            
            for trial in trials:
                time_vec = trial['time']
                lift_vec = trial['lift']
                thrust_vec = trial['thrust']
                
                # Resample to uniform phase
                _, lift_resampled = _resample_to_phase(time_vec, lift_vec, resample_n)
                _, thrust_resampled = _resample_to_phase(time_vec, thrust_vec, resample_n)
                
                lift_trials.append(lift_resampled)
                thrust_trials.append(thrust_resampled)
            
            # Create datasets
            lift_array = np.array(lift_trials)  # Shape: (num_trials, resample_n)
            thrust_array = np.array(thrust_trials)
            
            grp.create_dataset('lift', data=lift_array, compression='gzip')
            grp.create_dataset('thrust', data=thrust_array, compression='gzip')
            grp.create_dataset('phase', data=phase_grid, compression='gzip')
            
            print(f"Created group {group_name} with {len(trials)} trials")
    
    print(f"Saved Paddle stroke data to {out_path}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Convert Paddle stroke .mat to GUI‑compatible HDF5.")
    ap.add_argument("inputs", nargs="+", help="Input .mat files")
    ap.add_argument("-o", "--output", required=True, help="Output HDF5 file")
    ap.add_argument("-n", "--resample", type=int, default=1001, help="Resample to N points (default: 1001)")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    
    try:
        process_files(args.inputs, args.output, args.resample)
        return 0
    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
