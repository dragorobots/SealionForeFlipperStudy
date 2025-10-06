#!/usr/bin/env python3
"""
Power Stroke Trial Processing Script

This script processes all Power stroke experimental data to:
1. Load the PowerStroke_Complete HDF5 dataset (same as GUI)
2. For each experiment, detect trials using Arduino signal
3. Align trials (throw out first, use next 5)
4. Apply filters and zero correction
5. Calculate means and variances for thrust and lift
6. Save results to a new HDF5 file

The output dataset will be used as the source for final analysis GUIs.
"""

import h5py
import numpy as np
import os
import sys
import json
from scipy.signal import medfilt, filtfilt, firwin
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class PowerStrokeTrialProcessor:
    def __init__(self, input_hdf5_path, output_hdf5_path):
        """
        Initialize the processor
        
        Args:
            input_hdf5_path: Path to the input PowerStroke_Complete HDF5 file
            output_hdf5_path: Path to save the processed trial data
        """
        self.input_path = input_hdf5_path
        self.output_path = output_hdf5_path
        
        # Processing parameters (matching GUI settings)
        self.before_trial_include = 10  # samples
        self.low_threshold = 1.5
        self.high_threshold = 2.0
        self.min_gap_samples = 250  # 0.5 seconds at 500 Hz
        self.fs = 500.0  # sampling rate
        
        # Period-based trial lengths
        self.trial_lengths = {
            1.75: 150,
            2.25: 175
        }
        
        # Filtering parameters
        self.median_window = 11
        self.lowpass_cutoff = 8.0
        
    def load_data(self):
        """Load the input HDF5 data (same structure as GUI)"""
        print(f"Loading data from {self.input_path}")
        
        with h5py.File(self.input_path, 'r') as f:
            # Load main data array (3, 264, 7500) - thrust, lift, arduino
            self.data = f['data'][:]
            
            # Prefer per-experiment parameters saved by the loader
            if 'experiment_parameters' in f:
                # Columns: [period, yaw_amplitude, roll_angle, flow_speed]
                self.parameter_combinations = f['experiment_parameters'][:]
            else:
                # Fallback: construct Cartesian product (order may not align with data!)
                param_group = f['parameter_combinations']
                unique_periods = param_group['periods'][:]
                unique_yaw_amplitudes = param_group['yaw_amplitudes'][:]
                unique_roll_angles = param_group['roll_angles'][:]
                unique_flow_speeds = param_group['flow_speeds'][:]

                combinations = []
                for period in unique_periods:
                    for yaw in unique_yaw_amplitudes:
                        for roll in unique_roll_angles:
                            for flow in unique_flow_speeds:
                                combinations.append([period, yaw, roll, flow])
                self.parameter_combinations = np.array(combinations)
            
            # Load settings
            self.settings = {}
            for key in f['settings'].keys():
                self.settings[key] = f['settings'][key][:]
            
            # Load metadata
            self.metadata = dict(f.attrs)
            
        print(f"Loaded data shape: {self.data.shape}")
        print(f"Number of experiments: {self.data.shape[1]}")
        print(f"Parameter combinations: {self.parameter_combinations.shape}")
        
        # Extract unique parameter values from per-experiment parameters to preserve labels
        self.periods = np.unique(self.parameter_combinations[:, 0])
        self.yaw_amplitudes = np.unique(self.parameter_combinations[:, 1])
        self.roll_angles = np.unique(self.parameter_combinations[:, 2])
        self.flow_speeds = np.unique(self.parameter_combinations[:, 3])
        
        print(f"Parameters: {len(self.periods)} periods, {len(self.yaw_amplitudes)} yaw amplitudes, "
              f"{len(self.roll_angles)} roll angles, {len(self.flow_speeds)} flow speeds")
        
    def apply_data_filters(self, data, median_window=11, fs=500, cf=4.0):
        """
        Apply filters to thrust and lift data (NOT Arduino) - same as GUI
        
        Args:
            data: 3xN array (thrust, lift, arduino)
            median_window: Median filter window size
            fs: Sampling frequency
            cf: Low-pass filter cutoff frequency
            
        Returns:
            Filtered data array
        """
        # Step 1: Scale thrust and lift to Newtons; keep Arduino unchanged
        scaled = np.zeros_like(data)
        scaled[0, :] = data[0, :] * 2.22  # thrust
        scaled[1, :] = data[1, :] * 2.22  # lift
        scaled[2, :] = data[2, :]         # arduino (unchanged)

        # Step 2: Median filter ONLY thrust and lift; Arduino passes through raw
        median_filtered = np.zeros_like(scaled)
        median_filtered[0, :] = medfilt(scaled[0, :], kernel_size=median_window)
        median_filtered[1, :] = medfilt(scaled[1, :], kernel_size=median_window)
        median_filtered[2, :] = scaled[2, :]

        # Step 3: Low-pass filter ONLY thrust and lift; Arduino unchanged
        low_pass_filtered = np.zeros_like(median_filtered)

        nyquist = fs / 2
        normalized_cutoff = cf / nyquist
        b = firwin(101, normalized_cutoff, window='hamming')

        low_pass_filtered[0, :] = filtfilt(b, [1], median_filtered[0, :])
        low_pass_filtered[1, :] = filtfilt(b, [1], median_filtered[1, :])
        low_pass_filtered[2, :] = scaled[2, :]

        return low_pass_filtered
    
    def apply_arduino_filters(self, arduino_signal, median_window=21):
        """Apply filtering specifically to Arduino signal for trial detection - same as GUI"""
        try:
            if median_window % 2 == 0:
                median_window += 1
            filtered_signal = medfilt(arduino_signal, kernel_size=median_window)
            return filtered_signal
        except Exception as e:
            print(f"Arduino filter error: {str(e)}")
            return arduino_signal
    
    def detect_trials(self, arduino_signal):
        """
        Detect trials in Arduino signal using the same logic as the GUI
        
        Args:
            arduino_signal: Arduino signal array
            
        Returns:
            List of selected trial start indices
        """
        # Use raw Arduino signal for detection (no filtering)
        filtered_arduino = arduino_signal

        # Detect band membership
        low_band_samples = filtered_arduino <= self.low_threshold
        high_band_samples = filtered_arduino >= self.high_threshold
        
        # Find all trial starts
        raw_trial_starts = []
        for i in range(len(filtered_arduino)):
            if high_band_samples[i] and (i == 0 or not high_band_samples[i-1]):
                raw_trial_starts.append(i)
        
        # Merge close trial starts (remove noise artifacts)
        trial_starts = []
        for start in raw_trial_starts:
            if not trial_starts or (start - trial_starts[-1]) >= self.min_gap_samples:
                trial_starts.append(start)
            else:
                # Replace the last start with this one (later start)
                trial_starts[-1] = start
        
        # Select trials: throw out first, use next 5, throw out remaining
        if len(trial_starts) >= 6:  # Need at least 6 trials (1 to throw out + 5 to use)
            selected_trial_starts = trial_starts[1:6]  # Skip first, take next 5
        elif len(trial_starts) >= 2:  # Have at least 2 trials
            selected_trial_starts = trial_starts[1:]  # Use all but the first
        else:
            selected_trial_starts = []  # Not enough trials
        
        return selected_trial_starts
    
    def process_experiment(self, exp_idx):
        """
        Process a single experiment
        
        Args:
            exp_idx: Experiment index
            
        Returns:
            Dictionary with processed trial data or None if processing failed
        """
        try:
            # Get experiment data
            exp_data = self.data[:, exp_idx, :]  # Shape: (3, 7500)
            
            # Get parameters for this experiment
            params = self.parameter_combinations[exp_idx]
            period = params[0]
            yaw_amplitude = params[1]
            roll_angle = params[2]
            flow_speed = params[3]
            
            # Get trial length for this period
            trial_length = self.trial_lengths.get(period, 150)  # Default to 150
            
            # Apply filters to the data
            filtered_data = self.apply_data_filters(exp_data)
            
            # Zero the data (subtract mean of first 100 samples)
            zeroed_data = filtered_data.copy()
            for i in range(2):  # Only zero thrust and lift (not Arduino)
                zeroed_data[i, :] = filtered_data[i, :] - np.mean(filtered_data[i, :100])
            
            # Detect trials using Arduino signal
            arduino_signal = zeroed_data[2, :]  # Arduino is channel 2
            trial_starts = self.detect_trials(arduino_signal)
            
            if len(trial_starts) == 0:
                print(f"Experiment {exp_idx}: No trials detected")
                return None
            
            # Extract and align trials
            trials = []
            for start in trial_starts:
                # Adjust start with before trial include
                adjusted_start = start - self.before_trial_include
                adjusted_start = max(0, adjusted_start)
                
                # Calculate end
                end = adjusted_start + trial_length
                end = min(zeroed_data.shape[1], end)
                
                # Extract trial data (only thrust and lift)
                trial_data = zeroed_data[:2, adjusted_start:end]  # Only thrust and lift
                
                # Pad or truncate to exact trial length
                if trial_data.shape[1] < trial_length:
                    padded_trial = np.zeros((2, trial_length))
                    padded_trial[:, :trial_data.shape[1]] = trial_data
                    trial_data = padded_trial
                else:
                    trial_data = trial_data[:, :trial_length]
                
                trials.append(trial_data)
            
            if len(trials) == 0:
                print(f"Experiment {exp_idx}: No valid trials extracted")
                return None
            
            # Stack trials and calculate statistics
            trials_array = np.stack(trials, axis=0)  # Shape: (n_trials, 2, trial_length)
            
            # Calculate mean and variance across trials
            trial_mean = np.mean(trials_array, axis=0)  # Shape: (2, trial_length)
            trial_var = np.var(trials_array, axis=0)    # Shape: (2, trial_length)
            
            result = {
                'experiment_index': exp_idx,
                'parameters': {
                    'period': period,
                    'yaw_amplitude': yaw_amplitude,
                    'roll_angle': roll_angle,
                    'flow_speed': flow_speed
                },
                'trial_starts': trial_starts,
                'num_trials': len(trials),
                'trial_length': trial_length,
                'thrust_mean': trial_mean[0, :],  # Thrust mean
                'lift_mean': trial_mean[1, :],    # Lift mean
                'thrust_var': trial_var[0, :],    # Thrust variance
                'lift_var': trial_var[1, :],      # Lift variance
                'time_vector': np.arange(trial_length) / self.fs
            }
            
            print(f"Experiment {exp_idx}: Processed {len(trials)} trials successfully")
            return result
            
        except Exception as e:
            print(f"Error processing experiment {exp_idx}: {str(e)}")
            return None
    
    def process_all_experiments(self):
        """Process all experiments and save results"""
        print("Starting batch processing of all experiments...")
        
        processed_results = []
        successful_count = 0
        failed_count = 0
        
        for exp_idx in range(self.data.shape[1]):
            params = self.parameter_combinations[exp_idx]
            print(f"\nProcessing experiment {exp_idx + 1}/{self.data.shape[1]}: "
                  f"period={params[0]}, yaw={params[1]}, roll={params[2]}, flow={params[3]}")
            
            result = self.process_experiment(exp_idx)
            if result is not None:
                processed_results.append(result)
                successful_count += 1
            else:
                failed_count += 1
        
        print(f"\nProcessing complete!")
        print(f"Successful: {successful_count}")
        print(f"Failed: {failed_count}")
        
        # Save results
        self.save_results(processed_results)
        
        return processed_results
    
    def save_results(self, results):
        """Save processed results to HDF5 file"""
        print(f"Saving results to {self.output_path}")
        
        with h5py.File(self.output_path, 'w') as f:
            # Create datasets for each experiment
            for i, result in enumerate(results):
                exp_idx = result['experiment_index']
                group_name = f'experiment_{exp_idx:03d}'
                group = f.create_group(group_name)
                
                # Store parameters
                params = result['parameters']
                group.attrs['period'] = params['period']
                group.attrs['yaw_amplitude'] = params['yaw_amplitude']
                group.attrs['roll_angle'] = params['roll_angle']
                group.attrs['flow_speed'] = params['flow_speed']
                
                # Store trial information
                group.attrs['num_trials'] = result['num_trials']
                group.attrs['trial_length'] = result['trial_length']
                
                # Store data
                group.create_dataset('thrust_mean', data=result['thrust_mean'])
                group.create_dataset('lift_mean', data=result['lift_mean'])
                group.create_dataset('thrust_var', data=result['thrust_var'])
                group.create_dataset('lift_var', data=result['lift_var'])
                group.create_dataset('time_vector', data=result['time_vector'])
                group.create_dataset('trial_starts', data=result['trial_starts'])
            
            # Store metadata
            f.attrs['processing_date'] = datetime.now().isoformat()
            f.attrs['input_file'] = self.input_path
            f.attrs['total_experiments'] = len(results)
            
            # Store processing parameters as JSON string (to avoid HDF5 object dtype issues)
            processing_params = {
                'before_trial_include': self.before_trial_include,
                'low_threshold': self.low_threshold,
                'high_threshold': self.high_threshold,
                'min_gap_samples': self.min_gap_samples,
                'trial_lengths': self.trial_lengths,
                'median_window': self.median_window,
                'lowpass_cutoff': self.lowpass_cutoff,
                'sampling_rate': self.fs
            }
            f.attrs['processing_parameters'] = json.dumps(processing_params)
            
            # Store original parameters for reference
            f.create_dataset('original_parameter_combinations', data=self.parameter_combinations)
            f.create_dataset('original_periods', data=np.unique(self.periods))
            f.create_dataset('original_yaw_amplitudes', data=np.unique(self.yaw_amplitudes))
            f.create_dataset('original_roll_angles', data=np.unique(self.roll_angles))
            f.create_dataset('original_flow_speeds', data=np.unique(self.flow_speeds))
        
        print(f"Results saved successfully!")


def main():
    """Main function to run the processing"""
    # Define paths
    input_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "PowerStroke_Complete_2025-01-27.h5")
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "power_stroke_aligned_trials.h5")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found!")
        print("Please make sure the PowerStroke_Complete HDF5 file exists.")
        return
    
    # Create processor
    processor = PowerStrokeTrialProcessor(input_path, output_path)
    
    # Load data
    processor.load_data()
    
    # Process all experiments
    results = processor.process_all_experiments()
    
    print(f"\nProcessing complete! Results saved to {output_path}")
    print(f"Processed {len(results)} experiments successfully")


if __name__ == "__main__":
    main()