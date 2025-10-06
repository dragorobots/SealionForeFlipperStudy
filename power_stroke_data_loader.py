#!/usr/bin/env python3
"""
Power Stroke Data Loader and Converter
Loads Power stroke MATLAB data and converts to HDF5 format for analysis
"""

import h5py
import numpy as np
import os
from datetime import datetime
import json

class PowerStrokeDataLoader:
    def __init__(self, data_dir="data/raw/Master_Data_Set_Backup"):
        """
        Initialize the Power stroke data loader
        
        Parameters:
        -----------
        data_dir : str
            Directory containing the Power stroke MATLAB files
        """
        self.data_dir = data_dir
        self.file_1 = os.path.join(data_dir, "14-Oct-2022_results_PowerStroke.mat")
        self.file_2 = os.path.join(data_dir, "07-Oct-2022_results_PowerStroke.mat")
        
        # Data storage
        self.data = None
        self.parameters = None
        self.zeros = None
        self.settings = None
        self.metadata = None
        
    def load_data(self):
        """Load Power stroke data from MATLAB files"""
        print("Loading Power stroke data...")
        
        # Check if files exist
        if not os.path.exists(self.file_1):
            raise FileNotFoundError(f"File not found: {self.file_1}")
        if not os.path.exists(self.file_2):
            raise FileNotFoundError(f"File not found: {self.file_2}")
        
        # Load first dataset (14-Oct-2022)
        print(f"Loading: {os.path.basename(self.file_1)}")
        data_1, settings_1, params_1 = self._load_single_file(self.file_1)
        
        # Load second dataset (07-Oct-2022)
        print(f"Loading: {os.path.basename(self.file_2)}")
        data_2, settings_2, params_2 = self._load_single_file(self.file_2)
        
        # Combine datasets
        print("Combining datasets...")
        self.data = np.concatenate([data_1, data_2], axis=1)
        
        # Combine settings and apply corrections
        self.settings = {
            'period_settings': settings_1['period_settings'],
            'y_amp_settings': np.abs(settings_1['y_amp_settings']),  # Flip sign to positive
            'roll_pow_ang_settings': np.abs(settings_1['roll_pow_ang_settings']),  # Flip sign to positive
            'flow_speed_settings': self._convert_flow_speeds(np.concatenate([settings_1['flow_speed_settings'], settings_2['flow_speed_settings']]))
        }
        
        # Apply yaw amplitude corrections: [-90°, -75°, -60°] -> [90°, 80°, 70°]
        self.settings['y_amp_settings'] = self._correct_yaw_amplitudes(self.settings['y_amp_settings'])

        # Build per-experiment parameter table (period, yaw, roll, flow) using labels
        # Concatenate parameters from both datasets in acquisition order
        params_all = np.vstack([params_1, params_2])  # shape (N, 4): [period, yaw, roll, flow_power]

        # Apply corrections per experiment
        period_vec = params_all[:, 0]
        yaw_vec = np.abs(params_all[:, 1])
        roll_vec = np.abs(params_all[:, 2])
        flow_power_vec = params_all[:, 3]

        # Correct yaw values to [90, 80, 70]
        yaw_vec_corrected = np.array([self._correct_yaw_amplitudes(np.array([y]))[0] for y in yaw_vec])
        # Convert flow power to speed
        flow_speed_vec = np.array([self._convert_flow_speeds(np.array([fp]))[0] for fp in flow_power_vec])

        # Store corrected per-experiment parameters
        self.experiment_parameters = np.column_stack([period_vec, yaw_vec_corrected, roll_vec, flow_speed_vec])
        
        # Create metadata
        self.metadata = {
            'experiment_type': 'Power_Stroke',
            'source_files': ['14-Oct-2022_results_PowerStroke.mat', '07-Oct-2022_results_PowerStroke.mat'],
            'total_experiments': self.data.shape[1],
            'experiments_from_14Oct': data_1.shape[1],
            'experiments_from_07Oct': data_2.shape[1],
            'creation_date': datetime.now().isoformat(),
            'data_shape': self.data.shape,
            'sampling_rate': 500.0,  # Hz
            'channels': ['thrust', 'lift', 'arduino'],
            'corrections_applied': {
                'yaw_amplitudes': 'Flipped signs and corrected values: [-90°, -75°, -60°] -> [90°, 80°, 70°]',
                'roll_angles': 'Flipped signs to positive values',
                'flow_speeds': 'Converted motor power to flow speed: 0->0 m/s, 28->0.05 m/s, 70->0.1 m/s, 100->0.13 m/s'
            }
        }
        
        print(f"Loaded {self.data.shape[1]} total experiments")
        print(f"  - 14-Oct-2022: {data_1.shape[1]} experiments")
        print(f"  - 07-Oct-2022: {data_2.shape[1]} experiments")
        print(f"Data shape: {self.data.shape}")
        
    def _load_single_file(self, file_path):
        """Load a single MATLAB file and extract data and parameters"""
        with h5py.File(file_path, 'r') as f:
            results = f['results']
            
            # Load settings
            settings = {
                'period_settings': results['period_settings'][:].flatten(),
                'y_amp_settings': results['y_amp_settings'][:].flatten(),
                'roll_pow_ang_settings': results['roll_pow_ang_settings'][:].flatten(),
                'flow_speed_settings': results['Flow_Speed_settings'][:].flatten()
            }
            
            # Load data - this is complex due to MATLAB cell arrays
            data_group = results['data']['data']
            num_experiments = data_group.shape[0]
            
            # Initialize data array
            # We need to determine the data length first
            first_exp_ref = data_group[0, 0]
            first_exp_data = f[first_exp_ref]
            data_length = first_exp_data.shape[1]
            
            # Create data array: (channels, experiments, time_points)
            data = np.zeros((3, num_experiments, data_length))
            
            # Load each experiment
            for i in range(num_experiments):
                exp_ref = data_group[i, 0]
                exp_data = f[exp_ref]
                data[:, i, :] = exp_data[:]
            
            # Load parameters (period, yaw_amp, roll_angle, flow_power)
            param_group = results['parameters']['parameters']
            parameters = []
            for i in range(num_experiments):
                param_ref = param_group[i, 0]
                param_data = f[param_ref]
                # Parameters are stored as [period, yaw_amp, roll_angle]
                params = param_data[:].flatten()
                parameters.append(params)
            
            # Load zeros
            zeros_group = results['zeros']['zeros']
            zeros = []
            for i in range(num_experiments):
                zero_ref = zeros_group[i, 0]
                zero_data = f[zero_ref]
                zeros.append(zero_data[:])
            
            return data, settings, np.array(parameters)
    
    def _convert_flow_speeds(self, flow_speeds):
        """Convert motor power values to actual flow speeds in m/s"""
        # 0 -> 0 m/s, 28 -> 0.05 m/s, 70 -> 0.1 m/s, 100 -> 0.13 m/s
        conversion_map = {
            0.0: 0.0,
            28.0: 0.05,
            70.0: 0.1,
            100.0: 0.13
        }
        
        converted_speeds = []
        for speed in flow_speeds:
            if speed in conversion_map:
                converted_speeds.append(conversion_map[speed])
            else:
                print(f"Warning: Unknown flow speed value {speed}, keeping original")
                converted_speeds.append(speed)
        
        return np.array(converted_speeds)
    
    def _correct_yaw_amplitudes(self, yaw_amplitudes):
        """Correct yaw amplitude values: [-90°, -75°, -60°] -> [90°, 80°, 70°]"""
        # The original values are [-90°, -75°, -60°] but should be [90°, 80°, 70°]
        correction_map = {
            90.0: 90.0,  # -90° -> 90°
            75.0: 80.0,  # -75° -> 80° (corrected)
            60.0: 70.0   # -60° -> 70° (corrected)
        }
        
        corrected_amplitudes = []
        for amp in yaw_amplitudes:
            if amp in correction_map:
                corrected_amplitudes.append(correction_map[amp])
            else:
                print(f"Warning: Unknown yaw amplitude value {amp}, keeping original")
                corrected_amplitudes.append(amp)
        
        return np.array(corrected_amplitudes)
    
    def get_parameter_combinations(self):
        """Get all unique parameter combinations"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Extract unique parameter values
        periods = sorted(list(set(self.settings['period_settings'])))
        yaw_amps = sorted(list(set(self.settings['y_amp_settings'])))
        roll_angles = sorted(list(set(self.settings['roll_pow_ang_settings'])))
        flow_speeds = sorted(list(set(self.settings['flow_speed_settings'])))
        
        return {
            'periods': periods,
            'yaw_amplitudes': yaw_amps,
            'roll_angles': roll_angles,
            'flow_speeds': flow_speeds
        }
    
    def find_experiment_by_parameters(self, period, yaw_amp, roll_angle, flow_speed):
        """Find experiment index by parameter combination"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # This would need to be implemented based on how parameters are stored
        # For now, return None as placeholder
        return None
    
    def save_to_hdf5(self, output_file):
        """Save data to HDF5 format"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print(f"Saving to HDF5: {output_file}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with h5py.File(output_file, 'w') as f:
            # Save metadata
            meta_group = f.create_group('metadata')
            for key, value in self.metadata.items():
                if isinstance(value, str):
                    meta_group.attrs[key] = value
                elif isinstance(value, (int, float, bool)):
                    meta_group.attrs[key] = value
                elif isinstance(value, list):
                    # Convert lists to strings for HDF5 compatibility
                    meta_group.attrs[key] = str(value)
                elif isinstance(value, dict):
                    # Convert dicts to JSON strings for HDF5 compatibility
                    import json
                    meta_group.attrs[key] = json.dumps(value)
                else:
                    # Convert other types to strings
                    meta_group.attrs[key] = str(value)
            
            # Save data
            f.create_dataset('data', data=self.data, compression='gzip')
            
            # Save settings
            settings_group = f.create_group('settings')
            for key, value in self.settings.items():
                settings_group.create_dataset(key, data=value)
            
            # Save per-experiment parameters (corrected labels)
            if hasattr(self, 'experiment_parameters'):
                f.create_dataset('experiment_parameters', data=self.experiment_parameters)

            # Save parameter combinations (unique values) for convenience
            param_combos = self.get_parameter_combinations()
            param_group = f.create_group('parameter_combinations')
            for key, value in param_combos.items():
                param_group.create_dataset(key, data=value)
        
        print("HDF5 file saved successfully!")
    
    def create_summary_report(self, output_file):
        """Create a summary report of the Power stroke data"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print(f"Creating summary report: {output_file}")
        
        param_combos = self.get_parameter_combinations()
        
        report = {
            'metadata': self.metadata,
            'parameter_combinations': param_combos,
            'data_statistics': {
                'total_experiments': self.data.shape[1],
                'data_length_per_experiment': self.data.shape[2],
                'sampling_rate_hz': self.metadata['sampling_rate'],
                'total_duration_per_experiment_seconds': self.data.shape[2] / self.metadata['sampling_rate'],
                'data_ranges': {
                    'thrust': {
                        'min': float(np.min(self.data[0, :, :])),
                        'max': float(np.max(self.data[0, :, :])),
                        'mean': float(np.mean(self.data[0, :, :])),
                        'std': float(np.std(self.data[0, :, :]))
                    },
                    'lift': {
                        'min': float(np.min(self.data[1, :, :])),
                        'max': float(np.max(self.data[1, :, :])),
                        'mean': float(np.mean(self.data[1, :, :])),
                        'std': float(np.std(self.data[1, :, :]))
                    },
                    'arduino': {
                        'min': float(np.min(self.data[2, :, :])),
                        'max': float(np.max(self.data[2, :, :])),
                        'mean': float(np.mean(self.data[2, :, :])),
                        'std': float(np.std(self.data[2, :, :]))
                    }
                }
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("Summary report created successfully!")

def main():
    """Main function to load and convert Power stroke data"""
    
    # Initialize loader
    loader = PowerStrokeDataLoader()
    
    # Load data
    loader.load_data()
    
    # Get parameter combinations
    param_combos = loader.get_parameter_combinations()
    print("\nParameter combinations:")
    for key, values in param_combos.items():
        print(f"  {key}: {values}")
    
    # Save to HDF5
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    h5_file = os.path.join(output_dir, "PowerStroke_Complete_2025-01-27.h5")
    loader.save_to_hdf5(h5_file)
    
    # Create summary report
    report_file = os.path.join(output_dir, "PowerStroke_Summary_2025-01-27.json")
    loader.create_summary_report(report_file)
    
    print("\nPower stroke data conversion complete!")
    print(f"HDF5 file: {h5_file}")
    print(f"Summary report: {report_file}")

if __name__ == "__main__":
    main()
