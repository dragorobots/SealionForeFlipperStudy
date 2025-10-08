"""
Process Paddle Stroke Trials - Automated Processing Script

This script processes all Paddle stroke raw .mat files, applies trial detection and alignment,
and saves mean/variance traces to a new HDF5 file for the final overview GUI.

Based on the trial detection algorithm from paddle_trial_alignment_gui.py
"""

import os
import numpy as np
import h5py
import mat73
from scipy.signal import medfilt, firwin, filtfilt
from datetime import datetime
import json


class PaddleStrokeProcessor:
    def __init__(self):
        self.sampling_rate = 500.0
        self.median_window = 11
        self.cutoff_freq = 4.0
        self.arduino_median_window = 21
        self.before_trial_include = 10
        self.low_threshold = 1.5
        self.high_threshold = 2.0
        
        # Parameter mappings
        self.sweep_map = {60.0: 70.0, 75.0: 80.0, 90.0: 90.0, 105.0: 100.0}
        self.flow_map = {0.0: 0.0, 70.0: 0.1}
        
        # Trial length by period
        self.trial_lengths = {1.75: 200, 2.25: 290}
        
    def apply_zero_correction(self, data_3xT: np.ndarray) -> np.ndarray:
        """Apply zero correction to thrust and lift channels"""
        d = data_3xT.copy()
        d[0, :] = d[0, :] - float(np.mean(d[0, :100]))
        d[1, :] = d[1, :] - float(np.mean(d[1, :100]))
        return d
    
    def apply_data_filters(self, data_3xT: np.ndarray) -> np.ndarray:
        """Apply median and low-pass filters to thrust and lift"""
        out = data_3xT.copy()
        
        # Only apply filters if data is long enough
        if data_3xT.shape[1] > 100:
            # Median filter
            out[0, :] = medfilt(out[0, :], kernel_size=self.median_window)
            out[1, :] = medfilt(out[1, :], kernel_size=self.median_window)
            
            # Low-pass filter (only if data is long enough)
            if data_3xT.shape[1] > 3000:
                wn = (2.0 / self.sampling_rate) * self.cutoff_freq
                b = firwin(1001, wn, window=('kaiser', 1))
                out[0, :] = filtfilt(b, [1], out[0, :])
                out[1, :] = filtfilt(b, [1], out[1, :])
        
        return out
    
    def apply_arduino_filters(self, arduino: np.ndarray) -> np.ndarray:
        """Apply median filter to Arduino signal"""
        if len(arduino) > self.arduino_median_window:
            return medfilt(arduino, kernel_size=self.arduino_median_window)
        return arduino
    
    def extract_trial_from_single_trace(self, trace_data: np.ndarray, period: float) -> np.ndarray:
        """Extract a single trial from a Paddle trace using Arduino signal"""
        # Convert to (3, T) format if needed
        if trace_data.shape[1] == 3:
            d = trace_data.T  # Convert (T, 3) to (3, T)
        else:
            d = trace_data
        
        # Apply processing
        d = self.apply_zero_correction(d)
        d = self.apply_data_filters(d)
        ard = self.apply_arduino_filters(d[2, :])
        
        # Get trial length for this period
        trial_length = self.trial_lengths.get(period, 200)
        
        # Find Arduino start (first rising edge)
        base = float(np.median(ard[:50])) if ard.size >= 50 else float(np.median(ard))
        a = ard - base
        a[a < 0] = 0.0
        hb = a >= self.high_threshold
        
        # Find first rising edge
        rising = np.where((hb[1:] & (~hb[:-1])))[0] + 1
        if hb[0]:
            rising = np.concatenate([np.array([0]), rising])
        
        if len(rising) == 0:
            # No rising edge found, use start of trace
            start_idx = 0
        else:
            start_idx = int(rising[0])
        
        # Extract trial segment
        start = start_idx - self.before_trial_include
        start = max(0, start)
        end = min(start + trial_length, d.shape[1])
        
        seg = d[:, start:end]
        if seg.shape[1] < trial_length:
            pad = np.zeros((3, trial_length))
            pad[:, :seg.shape[1]] = seg
            seg = pad
        else:
            seg = seg[:, :trial_length]
        
        return seg
    
    def process_experiment(self, trace_data: np.ndarray, params: list, exp_idx: int) -> dict:
        """Process a single experiment (single trial) and return the trial data"""
        period = float(params[0])
        sweep_raw = abs(float(params[1]))
        twist = abs(float(params[2]))
        flow_raw = float(params[3])
        
        # Apply parameter corrections
        sweep = self.sweep_map.get(sweep_raw, sweep_raw)
        flow = self.flow_map.get(flow_raw, flow_raw)
        
        # Extract single trial from this experiment
        trial = self.extract_trial_from_single_trace(trace_data, period)
        
        if trial is None:
            print(f"Warning: Failed to extract trial for experiment {exp_idx}")
            return None
        
        return {
            'thrust': trial[0, :],
            'lift': trial[1, :],
            'arduino': trial[2, :],
            'period': period,
            'sweep': sweep,
            'twist': twist,
            'flow': flow,
            'exp_idx': exp_idx
        }
    
    def load_data(self, file_paths: list) -> tuple:
        """Load data from multiple .mat files"""
        all_data = []
        all_params = []
        all_exp_indices = []
        
        for file_idx, file_path in enumerate(file_paths):
            if not os.path.exists(file_path):
                print(f"Warning: File not found: {file_path}")
                continue
                
            print(f"Loading {file_path}...")
            data = mat73.loadmat(file_path)
            results = data.get('results', {})
            data_list = results.get('data', [])
            params_list = results.get('parameters', [])
            
            if not isinstance(data_list, list) or not isinstance(params_list, list):
                print(f"Warning: Invalid data format in {file_path}")
                continue
            
            n = min(len(data_list), len(params_list))
            for i in range(n):
                all_data.append(data_list[i])
                all_params.append(params_list[i])
                all_exp_indices.append(len(all_data) - 1)
        
        return all_data, all_params, all_exp_indices
    
    def process_all_experiments(self, file_paths: list, output_path: str):
        """Process all experiments and save to HDF5"""
        print("Loading data...")
        all_data, all_params, all_exp_indices = self.load_data(file_paths)
        
        if len(all_data) == 0:
            print("No data loaded!")
            return
        
        print(f"Processing {len(all_data)} experiments...")
        
        # Group experiments by parameters
        param_groups = {}
        for i, (data, params, exp_idx) in enumerate(zip(all_data, all_params, all_exp_indices)):
            period = float(params[0])
            sweep_raw = abs(float(params[1]))
            twist = abs(float(params[2]))
            flow_raw = float(params[3])
            
            sweep = self.sweep_map.get(sweep_raw, sweep_raw)
            flow = self.flow_map.get(flow_raw, flow_raw)
            
            key = (flow, sweep, twist, period)
            if key not in param_groups:
                param_groups[key] = []
            param_groups[key].append((data, params, exp_idx))
        
        print(f"Found {len(param_groups)} unique parameter combinations")
        
        # Process each parameter group
        processed_data = {}
        for key, experiments in param_groups.items():
            flow, sweep, twist, period = key
            print(f"Processing group: flow={flow}, sweep={sweep}, twist={twist}, period={period}")
            
            # Process all experiments in this group
            group_trials = []
            for data, params, exp_idx in experiments:
                result = self.process_experiment(data, params, exp_idx)
                if result is not None:
                    group_trials.append(result)
            
            if len(group_trials) > 0:
                # Stack all trials for this parameter group
                thrust_trials = np.stack([t['thrust'] for t in group_trials], axis=0)
                lift_trials = np.stack([t['lift'] for t in group_trials], axis=0)
                arduino_trials = np.stack([t['arduino'] for t in group_trials], axis=0)
                
                # Calculate mean and variance across trials
                mean_thrust = np.mean(thrust_trials, axis=0)
                mean_lift = np.mean(lift_trials, axis=0)
                mean_arduino = np.mean(arduino_trials, axis=0)
                
                var_thrust = np.var(thrust_trials, axis=0)
                var_lift = np.var(lift_trials, axis=0)
                var_arduino = np.var(arduino_trials, axis=0)
                
                processed_data[key] = {
                    'mean_thrust': mean_thrust,
                    'mean_lift': mean_lift,
                    'mean_arduino': mean_arduino,
                    'var_thrust': var_thrust,
                    'var_lift': var_lift,
                    'var_arduino': var_arduino,
                    'n_trials': len(group_trials),
                    'n_experiments': len(group_trials)
                }
        
        # Save to HDF5
        print(f"Saving results to {output_path}...")
        with h5py.File(output_path, 'w') as f:
            # Save metadata
            f.attrs['creation_date'] = datetime.now().isoformat()
            f.attrs['sampling_rate'] = self.sampling_rate
            f.attrs['n_parameter_groups'] = len(processed_data)
            
            # Save each parameter group
            for i, (key, data) in enumerate(processed_data.items()):
                flow, sweep, twist, period = key
                group_name = f"group_{i:03d}"
                grp = f.create_group(group_name)
                
                # Save data
                grp.create_dataset('mean_thrust', data=data['mean_thrust'])
                grp.create_dataset('mean_lift', data=data['mean_lift'])
                grp.create_dataset('mean_arduino', data=data['mean_arduino'])
                grp.create_dataset('var_thrust', data=data['var_thrust'])
                grp.create_dataset('var_lift', data=data['var_lift'])
                grp.create_dataset('var_arduino', data=data['var_arduino'])
                
                # Save attributes
                grp.attrs['flow'] = flow
                grp.attrs['sweep'] = sweep
                grp.attrs['twist'] = twist
                grp.attrs['period'] = period
                grp.attrs['n_trials'] = data['n_trials']
                grp.attrs['n_experiments'] = data['n_experiments']
        
        print(f"Processing complete! Saved {len(processed_data)} parameter groups to {output_path}")


def main():
    # File paths
    file_paths = [
        'data/raw/Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat',
        'data/raw/Raw_Experimental_Data/19-Oct-2022_Paddle_Stroke_Flipper_Results/19-Oct-2022_results_PaddleStroke.mat',
        'data/raw/Raw_Experimental_Data/27-Oct-2022_Power_Stroke_Flipper_Results/27-Oct-2022_results_PaddleStroke.mat',
    ]
    
    # Filter to existing files
    existing_files = [p for p in file_paths if os.path.exists(p)]
    if not existing_files:
        print("No Paddle .mat files found!")
        return
    
    # Output path
    output_path = 'data/processed/Paddle/PaddleStroke_Processed_2025-01-27.h5'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process
    processor = PaddleStrokeProcessor()
    processor.process_all_experiments(existing_files, output_path)


if __name__ == "__main__":
    main()
