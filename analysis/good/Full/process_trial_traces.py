#!/usr/bin/env python3
"""
Process Trial Traces - Extract and analyze individual trial data

This script processes all experiments in the FullStroke dataset to extract
individual trial traces, calculate mean and standard deviation traces,
and store everything in a comprehensive, interpretable format.

Pipeline:
1. Load FullStroke dataset
2. For each experiment:
   - Detect trial timing (start, duration, gap)
   - Extract 5 individual trial traces
   - Apply filtering (low-pass, zero correction, scaling)
   - Calculate mean and std traces
3. Store all data in a single comprehensive file

Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import h5py
import os
from scipy import signal
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
from datetime import datetime

class TrialTraceProcessor:
    def __init__(self, h5_file_path, cutoff_freq=4.0, sampling_rate=500.0, scale_factor=2.22):
        """
        Initialize the trial trace processor
        
        Parameters:
        -----------
        h5_file_path : str
            Path to the FullStroke HDF5 file
        cutoff_freq : float
            Low-pass filter cutoff frequency (Hz)
        sampling_rate : float
            Sampling rate (Hz)
        scale_factor : float
            Data scaling factor
        """
        self.h5_file_path = h5_file_path
        self.cutoff_freq = cutoff_freq
        self.sampling_rate = sampling_rate
        self.scale_factor = scale_factor
        self.data = None
        self.parameters = None
        self.zeros = None
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load data from HDF5 file"""
        print(f"Loading data from: {self.h5_file_path}")
        
        with h5py.File(self.h5_file_path, 'r') as f:
            # Load data
            data_group = f['data']
            self.data = {}
            for exp_key in data_group.keys():
                self.data[exp_key] = np.array(data_group[exp_key])
            
            # Load parameters
            param_group = f['parameters']
            self.parameters = {}
            for exp_key in param_group.keys():
                # Parameters are stored as a single dataset with shape (4, 1)
                # [period, yaw_amp, roll_angle, paddle_transition]
                param_data = np.array(param_group[exp_key])
                self.parameters[exp_key] = {
                    'period': param_data[0, 0],
                    'yaw_amplitude': param_data[1, 0],
                    'roll_angle': param_data[2, 0],
                    'paddle_transition': param_data[3, 0]
                }
            
            # Load zeros
            zeros_group = f['zeros']
            self.zeros = {}
            for exp_key in zeros_group.keys():
                self.zeros[exp_key] = np.array(zeros_group[exp_key])
        
        print(f"Loaded {len(self.data)} experiments")
    
    def detect_trial_timing_from_arduino(self, arduino_signal, fs=500):
        """
        Automatically detect trial timing from arduino signal
        Uses the same logic as the GUI
        """
        # Use raw signal for detection
        diff = np.diff(arduino_signal)
        
        # Find significant changes (big jumps)
        threshold = 1.0
        significant_negative = np.where(diff < -threshold)[0]  # Away from zero (trial start)
        significant_positive = np.where(diff > threshold)[0]   # Towards zero (trial end)
        
        if len(significant_negative) == 0 or len(significant_positive) == 0:
            return None
        
        # Step 1: Find first trial start (first negative jump not preceded by positive jump)
        first_trial_start = None
        for neg_idx in significant_negative:
            # Check if there's a positive jump within 100 samples before this negative jump
            recent_positives = significant_positive[significant_positive < neg_idx]
            if len(recent_positives) == 0 or (neg_idx - recent_positives[-1]) > 100:
                first_trial_start = neg_idx
                break
        
        if first_trial_start is None:
            return None
        
        # Step 2: Detect trial duration (time from start to first positive jump)
        trial_end_candidates = significant_positive[significant_positive > first_trial_start]
        if len(trial_end_candidates) == 0:
            return None
        
        trial_duration_samples = trial_end_candidates[0] - first_trial_start
        trial_duration = trial_duration_samples / fs
        
        # Step 3: Detect inter-trial gap (time from end of first trial to start of second trial)
        first_trial_end = first_trial_start + trial_duration_samples
        second_trial_candidates = significant_negative[significant_negative > first_trial_end]
        
        if len(second_trial_candidates) > 0:
            inter_trial_gap = (second_trial_candidates[0] - first_trial_end) / fs
        else:
            inter_trial_gap = 3.0  # Default gap
        
        # Step 4: Calculate number of trials (start with 5, reduce if needed)
        num_trials = 5
        total_time_needed = first_trial_start/fs + num_trials * (trial_duration + inter_trial_gap)
        total_time_available = len(arduino_signal) / fs
        
        if total_time_needed > total_time_available:
            num_trials = 4
            total_time_needed = first_trial_start/fs + num_trials * (trial_duration + inter_trial_gap)
            if total_time_needed > total_time_available:
                return None
        
        return {
            'first_trial_start': first_trial_start / fs,  # Convert to seconds
            'trial_duration': trial_duration,
            'inter_trial_gap': inter_trial_gap,
            'num_trials': num_trials
        }
    
    def extract_trials(self, data, timing_info):
        """
        Extract individual trial traces based on timing information
        
        Parameters:
        -----------
        data : np.ndarray
            Full experiment data (3 channels: thrust, lift, arduino)
        timing_info : dict
            Trial timing information
            
        Returns:
        --------
        trials : list
            List of trial data arrays
        time_vector : np.ndarray
            Time vector for trials
        """
        trials = []
        first_offset = timing_info['first_trial_start']
        trial_duration = timing_info['trial_duration']
        inter_gap = timing_info['inter_trial_gap']
        num_trials = timing_info['num_trials']
        
        # Calculate exact trial length in samples
        trial_length_samples = int(trial_duration * self.sampling_rate)
        
        for i in range(num_trials):
            # Calculate trial start time
            trial_start_time = first_offset + i * (trial_duration + inter_gap)
            
            # Convert to sample indices
            start_idx = int(trial_start_time * self.sampling_rate)
            end_idx = start_idx + trial_length_samples
            
            # Check bounds
            if start_idx >= 0 and end_idx < data.shape[1]:
                trial_data = data[:, start_idx:end_idx]
                trials.append(trial_data)
        
        # Create time vector
        time_vector = np.linspace(0, trial_duration, trial_length_samples)
        
        return trials, time_vector
    
    def apply_filters(self, data, zeros_data):
        """
        Apply filtering to data (low-pass, zero correction, scaling)
        
        Parameters:
        -----------
        data : np.ndarray
            Data to filter (3 channels: thrust, lift, arduino)
        zeros_data : np.ndarray
            Zero measurements for correction
            
        Returns:
        --------
        filtered_data : np.ndarray
            Filtered data
        """
        filtered_data = data.copy()
        
        # Apply filters to thrust and lift (channels 0 and 1)
        for channel in [0, 1]:  # Thrust and lift
            # Zero correction
            zero_mean = np.mean(zeros_data[channel, :])
            filtered_data[channel, :] -= zero_mean
            
            # Scaling
            filtered_data[channel, :] *= self.scale_factor
            
            # Median filter
            filtered_data[channel, :] = signal.medfilt(filtered_data[channel, :], kernel_size=11)
            
            # Low-pass filter (use shorter filter for short signals)
            nyquist = self.sampling_rate / 2
            normalized_cutoff = self.cutoff_freq / nyquist
            
            # Use shorter filter for short signals
            filter_length = min(101, len(filtered_data[channel, :]) // 3)
            if filter_length % 2 == 0:
                filter_length += 1
            
            if filter_length > 3:  # Only apply if filter is long enough
                b = signal.firwin(filter_length, normalized_cutoff, window=('kaiser', 1))
                filtered_data[channel, :] = signal.filtfilt(b, 1, filtered_data[channel, :])
        
        # Apply only median filter to arduino (channel 2)
        filtered_data[2, :] = signal.medfilt(filtered_data[2, :], kernel_size=11)
        
        return filtered_data
    
    def process_experiment(self, exp_key):
        """
        Process a single experiment to extract trial traces and statistics
        
        Parameters:
        -----------
        exp_key : str
            Experiment key (e.g., 'exp_0')
            
        Returns:
        --------
        result : dict
            Processed experiment data
        """
        print(f"Processing {exp_key}...")
        
        # Get experiment data
        data = self.data[exp_key]  # Shape: (3, 15000)
        zeros = self.zeros[exp_key]  # Shape: (3, N)
        params = self.parameters[exp_key]
        
        # Detect trial timing
        arduino_signal = data[2, :]  # Arduino is channel 2
        timing_info = self.detect_trial_timing_from_arduino(arduino_signal, self.sampling_rate)
        
        if timing_info is None:
            print(f"  Warning: Could not detect trials for {exp_key}")
            return None
        
        # Extract trials
        trials, time_vector = self.extract_trials(data, timing_info)
        
        if len(trials) == 0:
            print(f"  Warning: No trials extracted for {exp_key}")
            return None
        
        # Apply filters to each trial
        filtered_trials = []
        for trial in trials:
            filtered_trial = self.apply_filters(trial, zeros)
            filtered_trials.append(filtered_trial)
        
        # Calculate statistics
        # Stack trials: (num_trials, channels, time_points)
        stacked_trials = np.stack(filtered_trials, axis=0)
        
        # Calculate mean and std for thrust and lift
        thrust_trials = stacked_trials[:, 0, :]  # (num_trials, time_points)
        lift_trials = stacked_trials[:, 1, :]    # (num_trials, time_points)
        
        thrust_mean = np.mean(thrust_trials, axis=0)
        thrust_std = np.std(thrust_trials, axis=0)
        lift_mean = np.mean(lift_trials, axis=0)
        lift_std = np.std(lift_trials, axis=0)
        
        # Store individual trials
        thrust_individual = thrust_trials.T  # (time_points, num_trials)
        lift_individual = lift_trials.T      # (time_points, num_trials)
        
        result = {
            'experiment_key': exp_key,
            'parameters': params,
            'timing_info': timing_info,
            'time_vector': time_vector,
            'thrust': {
                'individual_trials': thrust_individual,
                'mean_trace': thrust_mean,
                'std_trace': thrust_std,
                'num_trials': len(trials)
            },
            'lift': {
                'individual_trials': lift_individual,
                'mean_trace': lift_mean,
                'std_trace': lift_std,
                'num_trials': len(trials)
            }
        }
        
        print(f"  Successfully processed {len(trials)} trials")
        return result
    
    def process_all_experiments(self):
        """
        Process all experiments and return comprehensive results
        
        Returns:
        --------
        results : dict
            Comprehensive results for all experiments
        """
        print("Processing all experiments...")
        
        results = {
            'metadata': {
                'processing_date': datetime.now().isoformat(),
                'source_file': self.h5_file_path,
                'cutoff_frequency': self.cutoff_freq,
                'sampling_rate': self.sampling_rate,
                'scale_factor': self.scale_factor,
                'total_experiments': len(self.data)
            },
            'experiments': {}
        }
        
        successful_count = 0
        for exp_key in self.data.keys():
            result = self.process_experiment(exp_key)
            if result is not None:
                results['experiments'][exp_key] = result
                successful_count += 1
        
        results['metadata']['successful_experiments'] = successful_count
        print(f"Successfully processed {successful_count}/{len(self.data)} experiments")
        
        return results
    
    def save_results(self, results, output_file):
        """
        Save results to HDF5 file in an interpretable format
        
        Parameters:
        -----------
        results : dict
            Comprehensive results
        output_file : str
            Output file path
        """
        print(f"Saving results to: {output_file}")
        
        with h5py.File(output_file, 'w') as f:
            # Save metadata
            meta_group = f.create_group('metadata')
            for key, value in results['metadata'].items():
                if isinstance(value, str):
                    meta_group.attrs[key] = value
                else:
                    meta_group.attrs[key] = value
            
            # Save experiments
            exp_group = f.create_group('experiments')
            for exp_key, exp_data in results['experiments'].items():
                exp_subgroup = exp_group.create_group(exp_key)
                
                # Save parameters
                param_subgroup = exp_subgroup.create_group('parameters')
                for param_key, param_value in exp_data['parameters'].items():
                    param_subgroup.attrs[param_key] = param_value
                
                # Save timing info
                timing_subgroup = exp_subgroup.create_group('timing_info')
                for timing_key, timing_value in exp_data['timing_info'].items():
                    timing_subgroup.attrs[timing_key] = timing_value
                
                # Save time vector
                exp_subgroup.create_dataset('time_vector', data=exp_data['time_vector'])
                
                # Save thrust data
                thrust_subgroup = exp_subgroup.create_group('thrust')
                thrust_subgroup.create_dataset('individual_trials', data=exp_data['thrust']['individual_trials'])
                thrust_subgroup.create_dataset('mean_trace', data=exp_data['thrust']['mean_trace'])
                thrust_subgroup.create_dataset('std_trace', data=exp_data['thrust']['std_trace'])
                thrust_subgroup.attrs['num_trials'] = exp_data['thrust']['num_trials']
                
                # Save lift data
                lift_subgroup = exp_subgroup.create_group('lift')
                lift_subgroup.create_dataset('individual_trials', data=exp_data['lift']['individual_trials'])
                lift_subgroup.create_dataset('mean_trace', data=exp_data['lift']['mean_trace'])
                lift_subgroup.create_dataset('std_trace', data=exp_data['lift']['std_trace'])
                lift_subgroup.attrs['num_trials'] = exp_data['lift']['num_trials']
        
        print("Results saved successfully!")
    
    def create_summary_report(self, results, output_file):
        """
        Create a human-readable summary report
        
        Parameters:
        -----------
        results : dict
            Comprehensive results
        output_file : str
            Output file path for the report
        """
        print(f"Creating summary report: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("TRIAL TRACE PROCESSING SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            f.write("PROCESSING METADATA:\n")
            f.write("-" * 20 + "\n")
            for key, value in results['metadata'].items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            # Experiment summary
            f.write("EXPERIMENT SUMMARY:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total experiments: {results['metadata']['total_experiments']}\n")
            f.write(f"Successfully processed: {results['metadata']['successful_experiments']}\n")
            f.write(f"Success rate: {results['metadata']['successful_experiments']/results['metadata']['total_experiments']*100:.1f}%\n\n")
            
            # Individual experiment details
            f.write("INDIVIDUAL EXPERIMENT DETAILS:\n")
            f.write("-" * 30 + "\n")
            for exp_key, exp_data in results['experiments'].items():
                f.write(f"\n{exp_key}:\n")
                f.write(f"  Parameters:\n")
                for param_key, param_value in exp_data['parameters'].items():
                    f.write(f"    {param_key}: {param_value}\n")
                f.write(f"  Timing:\n")
                for timing_key, timing_value in exp_data['timing_info'].items():
                    f.write(f"    {timing_key}: {timing_value:.3f}s\n")
                f.write(f"  Trials: {exp_data['thrust']['num_trials']}\n")
                f.write(f"  Time vector length: {len(exp_data['time_vector'])} samples\n")
                f.write(f"  Trial duration: {exp_data['time_vector'][-1]:.3f}s\n")
        
        print("Summary report created successfully!")

def main():
    """Main processing function"""
    # Configuration
    h5_file_path = "data/processed/2025-01-27_ProcessedData/FullStroke_Complete_2025-01-27.h5"
    cutoff_freq = 4.0  # Hz - Easy to change this parameter
    sampling_rate = 500.0  # Hz
    scale_factor = 2.22
    
    # Output files
    output_file = "data/processed/2025-01-27_ProcessedData/TrialTraces_Complete_2025-01-27.h5"
    report_file = "data/processed/2025-01-27_ProcessedData/TrialTraces_Summary_2025-01-27.txt"
    
    # Check if input file exists
    if not os.path.exists(h5_file_path):
        print(f"Error: Input file not found: {h5_file_path}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize processor
    processor = TrialTraceProcessor(
        h5_file_path=h5_file_path,
        cutoff_freq=cutoff_freq,
        sampling_rate=sampling_rate,
        scale_factor=scale_factor
    )
    
    # Process all experiments
    results = processor.process_all_experiments()
    
    # Save results
    processor.save_results(results, output_file)
    
    # Create summary report
    processor.create_summary_report(results, report_file)
    
    print("\n" + "="*60)
    print("PROCESSING COMPLETE!")
    print("="*60)
    print(f"Results saved to: {output_file}")
    print(f"Summary report: {report_file}")
    print(f"Cutoff frequency: {cutoff_freq} Hz")
    print(f"Successfully processed: {results['metadata']['successful_experiments']}/{results['metadata']['total_experiments']} experiments")

if __name__ == "__main__":
    main()
