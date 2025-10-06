#!/usr/bin/env python3
"""
Power Stroke Trial Alignment GUI - Manual trial alignment with Arduino signal detection
Detects Arduino signal transitions from low (~0) to high (~5) bands to identify trials
and allows user to align multiple traces for thrust, lift, and Arduino data
"""

import tkinter as tk
from tkinter import ttk, messagebox
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from datetime import datetime
from scipy.signal import medfilt, firwin, filtfilt
from scipy.ndimage import gaussian_filter1d

class PowerTrialAlignmentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Power Stroke Trial Alignment GUI")
        self.root.geometry("1600x1000")
        
        # Data storage
        self.data = None
        self.parameters = None
        self.settings = None
        self.metadata = None
        self.available_params = {}
        self.current_experiment_data = None
        self.current_experiment_index = None
        self.detected_trials = None
        
        # GUI components
        self.setup_gui()
        self.load_data()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Power Stroke Trial Alignment - Arduino Signal Detection", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Parameter selection frame
        param_frame = ttk.LabelFrame(main_frame, text="Experiment Selection", padding="10")
        param_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Parameter dropdowns
        self.param_vars = {}
        self.param_combos = {}
        
        # Row 1: Period and Yaw
        ttk.Label(param_frame, text="Period (s):").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['period'] = tk.StringVar()
        self.param_combos['period'] = ttk.Combobox(param_frame, textvariable=self.param_vars['period'], 
                                                   state="readonly", width=15)
        self.param_combos['period'].grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        self.param_combos['period'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        ttk.Label(param_frame, text="Yaw Amplitude (°):").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['yaw_amplitude'] = tk.StringVar()
        self.param_combos['yaw_amplitude'] = ttk.Combobox(param_frame, textvariable=self.param_vars['yaw_amplitude'], 
                                                          state="readonly", width=15)
        self.param_combos['yaw_amplitude'].grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        self.param_combos['yaw_amplitude'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        # Row 2: Roll and Flow Speed
        ttk.Label(param_frame, text="Roll Angle (°):").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['roll_angle'] = tk.StringVar()
        self.param_combos['roll_angle'] = ttk.Combobox(param_frame, textvariable=self.param_vars['roll_angle'], 
                                                       state="readonly", width=15)
        self.param_combos['roll_angle'].grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        self.param_combos['roll_angle'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        ttk.Label(param_frame, text="Flow Speed (m/s):").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['flow_speed'] = tk.StringVar()
        self.param_combos['flow_speed'] = ttk.Combobox(param_frame, textvariable=self.param_vars['flow_speed'], 
                                                       state="readonly", width=15)
        self.param_combos['flow_speed'].grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        self.param_combos['flow_speed'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        # Load experiment button
        load_button = ttk.Button(param_frame, text="Load Experiment", command=self.load_experiment, 
                                style="Accent.TButton")
        load_button.grid(row=2, column=0, columnspan=2, padx=(0, 20), pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(param_frame, text="Select experiment parameters and click Load", foreground="blue")
        self.status_label.grid(row=2, column=2, columnspan=2, pady=(10, 0))
        
        # Trial detection controls frame
        detection_frame = ttk.LabelFrame(main_frame, text="Arduino Signal Trial Detection", padding="10")
        detection_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Detection parameters
        ttk.Label(detection_frame, text="Low Band Max:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.low_threshold_var = tk.StringVar(value="1.5")
        ttk.Entry(detection_frame, textvariable=self.low_threshold_var, width=8).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(detection_frame, text="High Band Min:").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.high_threshold_var = tk.StringVar(value="2.0")
        ttk.Entry(detection_frame, textvariable=self.high_threshold_var, width=8).grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(detection_frame, text="Min Trial Duration (s):").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.min_trial_duration_var = tk.StringVar(value="1.0")
        ttk.Entry(detection_frame, textvariable=self.min_trial_duration_var, width=8).grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(detection_frame, text="Min Gap Duration (s):").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.min_gap_duration_var = tk.StringVar(value="0.5")
        ttk.Entry(detection_frame, textvariable=self.min_gap_duration_var, width=8).grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        
        # Before trial include
        ttk.Label(detection_frame, text="Before Trial Include (samples):").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.before_trial_include_var = tk.StringVar(value="10")
        ttk.Entry(detection_frame, textvariable=self.before_trial_include_var, width=8).grid(row=2, column=1, padx=(0, 20), sticky=tk.W)
        
        # Trial length (editable)
        ttk.Label(detection_frame, text="Trial Length (samples):").grid(row=2, column=2, padx=(0, 5), sticky=tk.W)
        self.trial_length_var = tk.StringVar(value="150")
        self.trial_length_entry = ttk.Entry(detection_frame, textvariable=self.trial_length_var, width=8)
        self.trial_length_entry.grid(row=2, column=3, padx=(0, 20), sticky=tk.W)
        
        # Detection buttons
        detect_button = ttk.Button(detection_frame, text="Detect Trials", command=self.detect_trials)
        detect_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        align_button = ttk.Button(detection_frame, text="Align & Plot Trials", command=self.align_and_plot_trials)
        align_button.grid(row=3, column=2, columnspan=2, pady=(10, 0))
        
        # Data processing frame
        processing_frame = ttk.LabelFrame(main_frame, text="Data Processing", padding="10")
        processing_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Zero correction checkbox
        self.zero_correction_var = tk.BooleanVar()
        zero_check = ttk.Checkbutton(processing_frame, text="Zero the Data", 
                                    variable=self.zero_correction_var, command=self.update_plot)
        zero_check.grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        
        # Filtering checkbox
        self.apply_filters_var = tk.BooleanVar()
        filter_check = ttk.Checkbutton(processing_frame, text="Apply Filters (Thrust/Lift Only)", 
                                      variable=self.apply_filters_var, command=self.update_plot)
        filter_check.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        # Arduino filtering checkbox
        self.apply_arduino_filters_var = tk.BooleanVar()
        arduino_filter_check = ttk.Checkbutton(processing_frame, text="Apply Arduino Filters", 
                                              variable=self.apply_arduino_filters_var, command=self.update_plot)
        arduino_filter_check.grid(row=0, column=2, padx=(0, 20), sticky=tk.W)
        
        # Filtering parameters
        ttk.Label(processing_frame, text="Median Window:").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.median_window_var = tk.StringVar(value="11")
        median_entry = ttk.Entry(processing_frame, textvariable=self.median_window_var, width=8)
        median_entry.grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(processing_frame, text="Sampling Rate (Hz):").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.sampling_rate_var = tk.StringVar(value="500")
        fs_entry = ttk.Entry(processing_frame, textvariable=self.sampling_rate_var, width=8)
        fs_entry.grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(processing_frame, text="Cutoff Freq (Hz):").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.cutoff_freq_var = tk.StringVar(value="4.0")
        cf_entry = ttk.Entry(processing_frame, textvariable=self.cutoff_freq_var, width=8)
        cf_entry.grid(row=2, column=1, padx=(0, 20), sticky=tk.W)
        
        # Arduino filter parameters
        ttk.Label(processing_frame, text="Arduino Median Window:").grid(row=2, column=2, padx=(0, 5), sticky=tk.W)
        self.arduino_median_window_var = tk.StringVar(value="21")
        arduino_median_entry = ttk.Entry(processing_frame, textvariable=self.arduino_median_window_var, width=8)
        arduino_median_entry.grid(row=2, column=3, padx=(0, 20), sticky=tk.W)
        
        # Y-axis controls frame (to the right)
        yaxis_frame = ttk.LabelFrame(main_frame, text="Y-Axis Controls", padding="10")
        yaxis_frame.grid(row=1, column=3, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Thrust Y-axis
        ttk.Label(yaxis_frame, text="Thrust Range:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.thrust_ymin_var = tk.StringVar(value="-4")
        self.thrust_ymax_var = tk.StringVar(value="4")
        ttk.Entry(yaxis_frame, textvariable=self.thrust_ymin_var, width=6).grid(row=0, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.thrust_ymax_var, width=6).grid(row=0, column=3, padx=(0, 0), sticky=tk.W)
        
        # Lift Y-axis
        ttk.Label(yaxis_frame, text="Lift Range:").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.lift_ymin_var = tk.StringVar(value="-5")
        self.lift_ymax_var = tk.StringVar(value="4")
        ttk.Entry(yaxis_frame, textvariable=self.lift_ymin_var, width=6).grid(row=1, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=1, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.lift_ymax_var, width=6).grid(row=1, column=3, padx=(0, 0), sticky=tk.W)
        
        # Arduino Y-axis
        ttk.Label(yaxis_frame, text="Arduino Range:").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.arduino_ymin_var = tk.StringVar(value="-2")
        self.arduino_ymax_var = tk.StringVar(value="6")
        ttk.Entry(yaxis_frame, textvariable=self.arduino_ymin_var, width=6).grid(row=2, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=2, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.arduino_ymax_var, width=6).grid(row=2, column=3, padx=(0, 0), sticky=tk.W)
        
        # X-axis control
        ttk.Label(yaxis_frame, text="X-Axis Range:").grid(row=3, column=0, padx=(0, 5), sticky=tk.W)
        self.xmin_var = tk.StringVar(value="0")
        self.xmax_var = tk.StringVar(value="15")
        ttk.Entry(yaxis_frame, textvariable=self.xmin_var, width=6).grid(row=3, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=3, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.xmax_var, width=6).grid(row=3, column=3, padx=(0, 0), sticky=tk.W)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(yaxis_frame, text="Trial Statistics", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=4, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30, font=("Courier", 8))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Plotting frame
        plot_frame = ttk.LabelFrame(main_frame, text="Power Stroke Trial Alignment Visualization", padding="10")
        plot_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(16, 12), dpi=100)
        self.ax_thrust = self.fig.add_subplot(3, 1, 1)
        self.ax_lift = self.fig.add_subplot(3, 1, 2)
        self.ax_arduino = self.fig.add_subplot(3, 1, 3)
        
        # Configure subplots
        self.ax_thrust.set_title("Thrust Force - Aligned Trials", fontsize=12, fontweight="bold")
        self.ax_thrust.set_ylabel("Force (N)")
        self.ax_thrust.grid(True, alpha=0.3)
        
        self.ax_lift.set_title("Lift Force - Aligned Trials", fontsize=12, fontweight="bold")
        self.ax_lift.set_ylabel("Force (N)")
        self.ax_lift.grid(True, alpha=0.3)
        
        self.ax_arduino.set_title("Arduino Sync Signal - Aligned Trials", fontsize=12, fontweight="bold")
        self.ax_arduino.set_xlabel("Time (s)")
        self.ax_arduino.set_ylabel("Signal")
        self.ax_arduino.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        
        # Canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def load_data(self):
        """Load the Power Stroke dataset"""
        try:
            # Find the most recent processed data file
            processed_dir = "data/processed"
            h5_files = []
            for root, dirs, files in os.walk(processed_dir):
                for file in files:
                    if file.startswith("PowerStroke_Complete") and file.endswith(".h5"):
                        h5_files.append(os.path.join(root, file))
            
            if not h5_files:
                messagebox.showerror("Error", "No PowerStroke_Complete.h5 files found in processed data directory")
                return
                
            # Use the most recent file
            h5_file = sorted(h5_files)[-1]
            file_path = h5_file
            
            with h5py.File(file_path, 'r') as f:
                # Load metadata
                self.metadata = dict(f['metadata'].attrs)
                
                # Load data structure
                self.data = f['data'][:]  # Shape: (3, 264, 7500)
                
                # Load settings
                settings_group = f['settings']
                self.settings = {}
                for key in settings_group.keys():
                    self.settings[key] = settings_group[key][:]
                
                # Load per-experiment parameters if present (period, yaw, roll, flow_speed)
                if 'experiment_parameters' in f:
                    self.experiment_parameters = f['experiment_parameters'][:]
                else:
                    self.experiment_parameters = None

                # Load parameter combinations
                param_group = f['parameter_combinations']
                self.available_params = {}
                for key in param_group.keys():
                    self.available_params[key] = param_group[key][:]
                
            # Extract available parameters
            self.populate_dropdowns()
            
            # Get just the filename for display
            filename = os.path.basename(h5_file)
            self.status_label.config(text=f"Loaded {self.data.shape[1]} experiments from {filename}", 
                                   foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_label.config(text="Failed to load data", foreground="red")
    
    def populate_dropdowns(self):
        """Populate the parameter dropdown menus"""
        try:
            # Map HDF5 parameter keys to GUI parameter keys
            param_mapping = {
                'periods': 'period',
                'yaw_amplitudes': 'yaw_amplitude', 
                'roll_angles': 'roll_angle',
                'flow_speeds': 'flow_speed'
            }
            
            for hdf5_key, values in self.available_params.items():
                if hdf5_key in param_mapping:
                    gui_key = param_mapping[hdf5_key]
                    # Convert to strings for display
                    str_values = [str(v) for v in values]
                    self.param_combos[gui_key]['values'] = str_values
                    
                    # Set default values
                    if hdf5_key == 'periods':
                        self.param_vars[gui_key].set("1.75")  # Default period
                    elif hdf5_key == 'yaw_amplitudes':
                        self.param_vars[gui_key].set("70")   # Default yaw (corrected value)
                    elif hdf5_key == 'roll_angles':
                        self.param_vars[gui_key].set("0")   # Default roll
                    elif hdf5_key == 'flow_speeds':
                        self.param_vars[gui_key].set("0.0")   # Default flow speed
                else:
                    print(f"Warning: Unknown parameter key '{hdf5_key}' in HDF5 file")
            
            print("Successfully populated parameter dropdowns")
            
        except Exception as e:
            print(f"Error populating dropdowns: {str(e)}")
            messagebox.showerror("Error", f"Failed to populate parameter dropdowns: {str(e)}")
    
    def apply_zero_correction(self, exp_data):
        """Apply zero correction to thrust and lift data"""
        if self.zero_correction_var.get():  # If toggle is ON
            # For Power stroke, we'll use the mean of the first 100 samples as zero
            corrected_data = exp_data.copy()
            corrected_data[0, :] -= np.mean(exp_data[0, :100])  # Thrust
            corrected_data[1, :] -= np.mean(exp_data[1, :100])  # Lift
            # Arduino (index 2) remains unchanged
            
            return corrected_data
        else:
            return exp_data  # Return raw data
    
    def apply_data_filters(self, data, median_window=11, fs=500, cf=4.0):
        """Apply filtering to thrust and lift channels only (NOT Arduino)"""
        try:
            # Step 1: Scale by 2.22
            scaled_data = data * 2.22
            
            # Step 2: Median filter - ensure kernel size is odd
            if median_window % 2 == 0:
                median_window += 1  # Make it odd
            median_filtered = np.zeros_like(scaled_data)
            for i in range(min(scaled_data.shape)):
                median_filtered[i, :] = medfilt(scaled_data[i, :], kernel_size=median_window)
            
            # Step 3: Low-pass filter (ONLY for thrust and lift channels - index 0 and 1)
            wn = (2/fs) * cf
            # Create Kaiser window manually (equivalent to kaiser(1001, 1) in MATLAB)
            b = firwin(1001, wn, window=('kaiser', 1))
            
            low_pass_filtered = np.zeros_like(median_filtered)
            for i in range(min(median_filtered.shape)):
                if i == 2:  # Arduino channel - NO filtering applied
                    low_pass_filtered[i, :] = data[i, :]  # Keep original Arduino signal
                else:  # Thrust and Lift channels - apply low-pass filter
                    low_pass_filtered[i, :] = filtfilt(b, [1], median_filtered[i, :])
            
            return low_pass_filtered
            
        except Exception as e:
            print(f"Filter error: {str(e)}")
            raise e
    
    def apply_arduino_filters(self, arduino_signal, median_window=21):
        """Apply filtering specifically to Arduino signal for trial detection"""
        try:
            # Only apply median filter to reduce noise while preserving transitions
            if median_window % 2 == 0:
                median_window += 1  # Make it odd
            
            filtered_signal = medfilt(arduino_signal, kernel_size=median_window)
            return filtered_signal
            
        except Exception as e:
            print(f"Arduino filter error: {str(e)}")
            return arduino_signal  # Return original if filtering fails
    
    def process_experiment_data(self, exp_data):
        """Complete data processing pipeline"""
        # Step 1: Apply zero correction (if enabled)
        if self.zero_correction_var.get():
            exp_data = self.apply_zero_correction(exp_data)
        
        # Step 2: Apply filters to thrust/lift only (if enabled)
        if self.apply_filters_var.get():
            try:
                median_window = int(self.median_window_var.get())
                fs = float(self.sampling_rate_var.get())
                cf = float(self.cutoff_freq_var.get())
                exp_data = self.apply_data_filters(exp_data, median_window, fs, cf)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid filter parameters: {str(e)}")
                return exp_data
            except Exception as e:
                messagebox.showerror("Error", f"Filter processing error: {str(e)}")
                return exp_data
        
        return exp_data
    
    def get_arduino_signal_for_detection(self, exp_data):
        """Get Arduino signal with optional filtering for trial detection"""
        arduino_signal = exp_data[2, :]  # Arduino channel
        
        # Apply Arduino-specific filtering if enabled
        if self.apply_arduino_filters_var.get():
            try:
                arduino_median_window = int(self.arduino_median_window_var.get())
                arduino_signal = self.apply_arduino_filters(arduino_signal, arduino_median_window)
            except ValueError as e:
                print(f"Invalid Arduino filter parameters: {str(e)}")
                # Continue with unfiltered signal
        
        return arduino_signal
    
    def find_experiment_index(self):
        """Find the experiment index matching the selected parameters"""
        if self.data is None:
            return None
            
        try:
            # Get selected parameter values
            selected_params = {}
            for param in ['period', 'yaw_amplitude', 'roll_angle', 'flow_speed']:
                value_str = self.param_vars[param].get()
                if not value_str:
                    return None
                selected_params[param] = float(value_str)
            
            # Prefer explicit per-experiment parameters if available
            if getattr(self, 'experiment_parameters', None) is not None:
                ep = self.experiment_parameters
                p = selected_params['period']
                y = selected_params['yaw_amplitude']
                r = selected_params['roll_angle']
                f = selected_params['flow_speed']
                # Tolerant float match
                tol = 1e-6
                mask = (
                    (np.abs(ep[:, 0] - p) < tol) &
                    (np.abs(ep[:, 1] - y) < tol) &
                    (np.abs(ep[:, 2] - r) < tol) &
                    (np.abs(ep[:, 3] - f) < tol)
                )
                idxs = np.where(mask)[0]
                if idxs.size > 0:
                    return int(idxs[0])
                else:
                    return None
            
            # Fallback: if full factorial and known ordering, compute index; else return None
            return None
            
        except (ValueError, IndexError) as e:
            return None
    
    def load_experiment(self):
        """Load the selected experiment data"""
        exp_idx = self.find_experiment_index()
        if exp_idx is None:
            messagebox.showerror("Error", "No experiment found matching the selected parameters")
            return
        
        # Store current experiment data
        self.current_experiment_data = self.data[:, exp_idx, :]
        self.current_experiment_index = exp_idx
        
        # Set trial length based on period
        period = float(self.param_vars['period'].get())
        self.set_trial_length_for_period(period)
        
        # Update status
        self.status_label.config(text=f"Loaded experiment {exp_idx}. Click 'Detect Trials' to find trial boundaries.", 
                               foreground="green")
        
        # Clear previous trials
        self.detected_trials = None
        
        # Update plot with raw data
        self.update_plot()
    
    def set_trial_length_for_period(self, period):
        """Set trial length based on period parameter"""
        if period == 1.75:
            self.trial_length_var.set("150")
        elif period == 2.25:
            self.trial_length_var.set("175")
        else:
            # Default fallback
            self.trial_length_var.set("150")
            print(f"Warning: Unknown period {period}, using default trial length 150")
    
    def on_param_change(self, event=None):
        """Called when any parameter selection changes"""
        # Clear current experiment when parameters change
        self.current_experiment_data = None
        self.current_experiment_index = None
        self.detected_trials = None
        self.status_label.config(text="Parameters changed. Click Load Experiment to load new data.", 
                               foreground="blue")
    
    def detect_trials(self):
        """Detect trials based on Arduino signal band transitions"""
        if self.current_experiment_data is None:
            messagebox.showerror("Error", "No experiment loaded. Please load an experiment first.")
            return
        
        try:
            # Process data to get arduino signal
            processed_data = self.process_experiment_data(self.current_experiment_data)
            arduino_signal = self.get_arduino_signal_for_detection(processed_data)
            
            # Get detection parameters
            low_threshold = float(self.low_threshold_var.get())
            high_threshold = float(self.high_threshold_var.get())
            min_trial_duration = float(self.min_trial_duration_var.get())
            min_gap_duration = float(self.min_gap_duration_var.get())
            fs = float(self.sampling_rate_var.get())
            
            # Convert durations to samples
            min_trial_samples = int(min_trial_duration * fs)
            min_gap_samples = int(min_gap_duration * fs)
            
            print(f"Arduino signal range: {np.min(arduino_signal):.2f} to {np.max(arduino_signal):.2f}")
            print(f"Using thresholds: low={low_threshold}, high={high_threshold}")
            
            # Improved band detection algorithm
            # First, identify the two bands by analyzing the signal distribution
            signal_mean = np.mean(arduino_signal)
            signal_std = np.std(arduino_signal)
            
            # Create a more robust band detection
            # Low band: oscillations around 0 with +/- 1
            # High band: oscillations around 3.5 with +/- 1.5
            low_band_center = 0.0
            high_band_center = 3.5
            
            # Use user-provided thresholds or adaptive thresholds
            low_band_max = low_threshold  # User-provided threshold
            high_band_min = high_threshold  # User-provided threshold
            
            print(f"Band centers: low={low_band_center}, high={high_band_center}")
            print(f"Adaptive thresholds: low_max={low_band_max}, high_min={high_band_min}")
            
            # Detect band membership for each sample
            low_band_samples = arduino_signal <= low_band_max
            high_band_samples = arduino_signal >= high_band_min
            
            # Debug: count samples in each band
            num_low_samples = np.sum(low_band_samples)
            num_high_samples = np.sum(high_band_samples)
            print(f"Band membership: {num_low_samples} low-band samples, {num_high_samples} high-band samples")
            
            # Debug: find first few high-band samples
            high_indices = np.where(high_band_samples)[0]
            if len(high_indices) > 0:
                print(f"First 10 high-band sample indices: {high_indices[:10]}")
                print(f"First 10 high-band sample times: {high_indices[:10] / fs}")
            else:
                print("No high-band samples found!")
            
            # Find all trial starts first
            raw_trial_starts = []
            for i in range(len(arduino_signal)):
                if high_band_samples[i] and (i == 0 or not high_band_samples[i-1]):
                    raw_trial_starts.append(i)
            
            print(f"Raw trial starts found: {len(raw_trial_starts)}")
            print(f"Raw starts: {[f'{s/fs:.2f}s' for s in raw_trial_starts]}")
            
            # Merge close trial starts (remove noise artifacts)
            # If two starts are within 0.5 seconds, use the later one
            min_gap_samples = int(0.5 * fs)  # 0.5 second minimum gap
            trial_starts = []
            
            for start in raw_trial_starts:
                if not trial_starts or (start - trial_starts[-1]) >= min_gap_samples:
                    trial_starts.append(start)
                else:
                    # Replace the last start with this one (later start)
                    trial_starts[-1] = start
                    print(f"Merged close starts, using later one at {start/fs:.2f}s")
            
            print(f"After merging: {len(trial_starts)} trial starts")
            print(f"Final starts: {[f'{s/fs:.2f}s' for s in trial_starts]}")
            
            # Now find the duration of each high-band period
            trial_durations = []
            for i, start in enumerate(trial_starts):
                # Find the end of this high-band period
                trial_end = None
                
                # Look for the next trial start
                if i + 1 < len(trial_starts):
                    next_start = trial_starts[i + 1]
                    # Find the last high-band sample before the next trial
                    for j in range(next_start - 1, start, -1):
                        if high_band_samples[j]:
                            trial_end = j
                            break
                else:
                    # This is the last trial, find the last high-band sample
                    for j in range(len(arduino_signal) - 1, start, -1):
                        if high_band_samples[j]:
                            trial_end = j
                            break
                
                if trial_end is not None:
                    duration = trial_end - start
                    trial_durations.append(duration)
                    print(f"Trial {i+1}: {start/fs:.2f}s to {trial_end/fs:.2f}s (duration: {duration/fs:.2f}s)")
            
            # Select trials: throw out first, use next 5, throw out remaining
            if len(trial_starts) >= 6:  # Need at least 6 trials (1 to throw out + 5 to use)
                # Throw out first trial, use next 5
                selected_trial_starts = trial_starts[1:6]  # Skip first, take next 5
                print(f"Selected trials 2-6 out of {len(trial_starts)} total trials")
                print(f"Threw out first trial at {trial_starts[0]/fs:.2f}s")
                if len(trial_starts) > 6:
                    print(f"Threw out remaining {len(trial_starts) - 6} trials")
            elif len(trial_starts) >= 2:  # Have at least 2 trials
                # Use all but the first
                selected_trial_starts = trial_starts[1:]
                print(f"Selected trials 2-{len(trial_starts)} out of {len(trial_starts)} total trials")
                print(f"Threw out first trial at {trial_starts[0]/fs:.2f}s")
            else:
                # Not enough trials
                selected_trial_starts = []
                print(f"Not enough trials found. Need at least 2, found {len(trial_starts)}")
            
            # Use the trial length from the GUI (set based on period)
            trial_length_samples = int(self.trial_length_var.get())
            trial_ends = [start + trial_length_samples for start in selected_trial_starts]
            
            print(f"Using trial length of {trial_length_samples} samples for all selected trials")
            
            # Debug: print final results
            print(f"Final selected trial count: {len(selected_trial_starts)}")
            if len(selected_trial_starts) > 0:
                print(f"Selected trial starts: {selected_trial_starts}")
                print(f"Selected trial ends: {trial_ends}")
                for i, (start, end) in enumerate(zip(selected_trial_starts, trial_ends)):
                    print(f"Selected Trial {i+1}: {start/fs:.2f}s to {end/fs:.2f}s (duration: {(end-start)/fs:.2f}s)")
            
            # Store detected trials (using selected trials)
            self.detected_trials = {
                'starts': selected_trial_starts,
                'ends': trial_ends,
                'num_trials': len(selected_trial_starts),
                'low_band_max': low_band_max,
                'high_band_min': high_band_min
            }
            
            print(f"Total selected trials: {len(selected_trial_starts)}")
            
            # Update status
            self.status_label.config(text=f"Detected {len(selected_trial_starts)} selected trials. Click 'Align & Plot Trials' to visualize.", 
                                   foreground="green")
            
            # Update plot to show detection results
            self.update_plot_with_detection()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect trials: {str(e)}")
            self.status_label.config(text="Failed to detect trials", foreground="red")
            import traceback
            traceback.print_exc()
    
    def align_and_plot_trials(self):
        """Align and plot the detected trials"""
        if self.detected_trials is None or self.detected_trials['num_trials'] == 0:
            messagebox.showerror("Error", "No trials detected. Please run trial detection first.")
            return
        
        try:
            # Get user parameters
            before_trial_include = int(self.before_trial_include_var.get())
            trial_length_samples = int(self.trial_length_var.get())
            
            if trial_length_samples <= 0:
                messagebox.showerror("Invalid Input", "Trial length must be greater than 0.")
                return
            
            # Process data
            processed_data = self.process_experiment_data(self.current_experiment_data)
            fs = float(self.sampling_rate_var.get())
            
            # Extract trials using user-defined parameters
            trials = []
            for i in range(self.detected_trials['num_trials']):
                # Adjust start with before trial include
                start_idx = self.detected_trials['starts'][i] - before_trial_include
                end_idx = start_idx + trial_length_samples
                
                # Ensure indices are within bounds
                start_idx = max(0, start_idx)
                end_idx = min(processed_data.shape[1], end_idx)
                
                trial_data = processed_data[:, start_idx:end_idx]
                trials.append(trial_data)
            
            # Use the user-defined trial length for alignment
            target_length = trial_length_samples
            
            # Align trials to the same length
            aligned_trials = []
            for trial in trials:
                if trial.shape[1] >= target_length:
                    # Trial is long enough, truncate to target length
                    aligned_trial = trial[:, :target_length]
                else:
                    # Trial is too short, pad with zeros
                    aligned_trial = np.zeros((trial.shape[0], target_length))
                    aligned_trial[:, :trial.shape[1]] = trial
                aligned_trials.append(aligned_trial)
            
            # Create time vector (adjusted for before trial include)
            time = np.arange(target_length) / fs
            if before_trial_include > 0:
                time = time - (before_trial_include / fs)  # Shift time to show negative values for before-trial period
            
            # Clear previous plots
            self.ax_thrust.clear()
            self.ax_lift.clear()
            self.ax_arduino.clear()
            
            # Plot individual trials
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
            for i, trial_data in enumerate(aligned_trials):
                color = colors[i % len(colors)]
                alpha = 0.6
                
                # Plot individual trials
                self.ax_thrust.plot(time, trial_data[0, :], color=color, linewidth=1, 
                                   alpha=alpha, label=f'Trial {i+1}')
                self.ax_lift.plot(time, trial_data[1, :], color=color, linewidth=1, 
                                 alpha=alpha, label=f'Trial {i+1}')
                self.ax_arduino.plot(time, trial_data[2, :], color=color, linewidth=1, 
                                    alpha=alpha, label=f'Trial {i+1}')
            
            # Calculate and plot mean
            if len(aligned_trials) > 1:
                stacked_trials = np.stack(aligned_trials, axis=0)
                mean_trials = np.mean(stacked_trials, axis=0)
                
                self.ax_thrust.plot(time, mean_trials[0, :], color='black', linewidth=3, 
                                   label='Mean', alpha=0.8)
                self.ax_lift.plot(time, mean_trials[1, :], color='black', linewidth=3, 
                                 label='Mean', alpha=0.8)
                self.ax_arduino.plot(time, mean_trials[2, :], color='black', linewidth=3, 
                                    label='Mean', alpha=0.8)
            
            # Configure plots
            self.ax_thrust.set_title(f"Thrust Force - {len(aligned_trials)} Aligned Trials", 
                                   fontsize=12, fontweight="bold")
            self.ax_thrust.set_ylabel("Force (N)")
            self.ax_thrust.grid(True, alpha=0.3)
            self.ax_thrust.legend()
            
            self.ax_lift.set_title(f"Lift Force - {len(aligned_trials)} Aligned Trials", 
                                 fontsize=12, fontweight="bold")
            self.ax_lift.set_ylabel("Force (N)")
            self.ax_lift.grid(True, alpha=0.3)
            self.ax_lift.legend()
            
            self.ax_arduino.set_title(f"Arduino Sync Signal - {len(aligned_trials)} Aligned Trials", 
                                    fontsize=12, fontweight="bold")
            self.ax_arduino.set_xlabel("Time (s)")
            self.ax_arduino.set_ylabel("Signal")
            self.ax_arduino.grid(True, alpha=0.3)
            self.ax_arduino.legend()
            
            # Set axis ranges
            self.set_axis_ranges()
            
            # Update statistics
            self.update_trial_statistics(aligned_trials, time)
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to align and plot trials: {str(e)}")
    
    def update_plot_with_detection(self):
        """Update plot to show trial detection results"""
        if self.current_experiment_data is None:
            return
        
        try:
            # Process data
            processed_data = self.process_experiment_data(self.current_experiment_data)
            fs = float(self.sampling_rate_var.get())
            time = np.arange(processed_data.shape[1]) / fs
            
            # Clear previous plots
            self.ax_thrust.clear()
            self.ax_lift.clear()
            self.ax_arduino.clear()
            
            # Plot data
            self.ax_thrust.plot(time, processed_data[0, :], 'b-', linewidth=1, label='Thrust')
            self.ax_lift.plot(time, processed_data[1, :], 'r-', linewidth=1, label='Lift')
            self.ax_arduino.plot(time, processed_data[2, :], 'g-', linewidth=1, label='Arduino')
            
            # Add trial detection visualization
            if self.detected_trials is not None:
                # Add band visualization
                if 'low_band_max' in self.detected_trials:
                    low_band_max = self.detected_trials['low_band_max']
                    high_band_min = self.detected_trials['high_band_min']
                    
                    # Add band boundary lines
                    self.ax_arduino.axhline(y=low_band_max, color='orange', linestyle='--', alpha=0.7, label='Low Band Max')
                    self.ax_arduino.axhline(y=high_band_min, color='red', linestyle='--', alpha=0.7, label='High Band Min')
                    
                    # Add band center lines
                    self.ax_arduino.axhline(y=0.0, color='lightblue', linestyle=':', alpha=0.5, label='Low Band Center')
                    self.ax_arduino.axhline(y=3.5, color='lightgreen', linestyle=':', alpha=0.5, label='High Band Center')
                
                # Highlight detected trials
                for i in range(self.detected_trials['num_trials']):
                    start_time = self.detected_trials['starts'][i] / fs
                    end_time = self.detected_trials['ends'][i] / fs
                    
                    # Add shaded regions for trials
                    self.ax_arduino.axvspan(start_time, end_time, alpha=0.2, color='yellow', 
                                          label='Detected Trial' if i == 0 else "")
            
            # Configure plots
            self.ax_thrust.set_title(f"Thrust Force - Trial Detection (Exp {self.current_experiment_index})", 
                                   fontsize=12, fontweight="bold")
            self.ax_thrust.set_ylabel("Force (N)")
            self.ax_thrust.grid(True, alpha=0.3)
            self.ax_thrust.legend()
            
            self.ax_lift.set_title(f"Lift Force - Trial Detection (Exp {self.current_experiment_index})", 
                                 fontsize=12, fontweight="bold")
            self.ax_lift.set_ylabel("Force (N)")
            self.ax_lift.grid(True, alpha=0.3)
            self.ax_lift.legend()
            
            self.ax_arduino.set_title(f"Arduino Signal - Trial Detection (Exp {self.current_experiment_index})", 
                                    fontsize=12, fontweight="bold")
            self.ax_arduino.set_xlabel("Time (s)")
            self.ax_arduino.set_ylabel("Signal")
            self.ax_arduino.grid(True, alpha=0.3)
            self.ax_arduino.legend()
            
            # Set axis ranges
            self.set_axis_ranges()
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update plot: {str(e)}")
    
    def update_plot(self):
        """Update the basic data visualization"""
        if self.current_experiment_data is None:
            return
        
        try:
            # Process data
            processed_data = self.process_experiment_data(self.current_experiment_data)
            fs = float(self.sampling_rate_var.get())
            time = np.arange(processed_data.shape[1]) / fs
            
            # Clear previous plots
            self.ax_thrust.clear()
            self.ax_lift.clear()
            self.ax_arduino.clear()
            
            # Plot data
            self.ax_thrust.plot(time, processed_data[0, :], 'b-', linewidth=1, label='Thrust')
            self.ax_lift.plot(time, processed_data[1, :], 'r-', linewidth=1, label='Lift')
            self.ax_arduino.plot(time, processed_data[2, :], 'g-', linewidth=1, label='Arduino')
            
            # Configure plots
            self.ax_thrust.set_title(f"Thrust Force - Power Stroke (Exp {self.current_experiment_index})", 
                                   fontsize=12, fontweight="bold")
            self.ax_thrust.set_ylabel("Force (N)")
            self.ax_thrust.grid(True, alpha=0.3)
            self.ax_thrust.legend()
            
            self.ax_lift.set_title(f"Lift Force - Power Stroke (Exp {self.current_experiment_index})", 
                                 fontsize=12, fontweight="bold")
            self.ax_lift.set_ylabel("Force (N)")
            self.ax_lift.grid(True, alpha=0.3)
            self.ax_lift.legend()
            
            self.ax_arduino.set_title(f"Arduino Sync Signal - Power Stroke (Exp {self.current_experiment_index})", 
                                    fontsize=12, fontweight="bold")
            self.ax_arduino.set_xlabel("Time (s)")
            self.ax_arduino.set_ylabel("Signal")
            self.ax_arduino.grid(True, alpha=0.3)
            self.ax_arduino.legend()
            
            # Set axis ranges
            self.set_axis_ranges()
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update plot: {str(e)}")
    
    def set_axis_ranges(self):
        """Set axis ranges from GUI controls"""
        try:
            # Y-axis ranges
            thrust_ymin = float(self.thrust_ymin_var.get())
            thrust_ymax = float(self.thrust_ymax_var.get())
            self.ax_thrust.set_ylim(thrust_ymin, thrust_ymax)
            
            lift_ymin = float(self.lift_ymin_var.get())
            lift_ymax = float(self.lift_ymax_var.get())
            self.ax_lift.set_ylim(lift_ymin, lift_ymax)
            
            arduino_ymin = float(self.arduino_ymin_var.get())
            arduino_ymax = float(self.arduino_ymax_var.get())
            self.ax_arduino.set_ylim(arduino_ymin, arduino_ymax)
            
            # X-axis range
            xmin = float(self.xmin_var.get())
            xmax = float(self.xmax_var.get())
            self.ax_thrust.set_xlim(xmin, xmax)
            self.ax_lift.set_xlim(xmin, xmax)
            self.ax_arduino.set_xlim(xmin, xmax)
        except ValueError:
            pass  # Use auto-scaling if invalid range
    
    def update_trial_statistics(self, aligned_trials, time):
        """Update trial statistics display"""
        if len(aligned_trials) == 0:
            return
        
        # Calculate statistics
        stacked_trials = np.stack(aligned_trials, axis=0)
        mean_trials = np.mean(stacked_trials, axis=0)
        std_trials = np.std(stacked_trials, axis=0)
        
        stats_text = f"Trial Statistics:\n"
        stats_text += f"Number of trials: {len(aligned_trials)}\n"
        stats_text += f"Trial duration: {time[-1]:.1f}s\n"
        stats_text += f"Sampling rate: {float(self.sampling_rate_var.get())} Hz\n\n"
        
        # Thrust statistics
        thrust_mean = np.mean(mean_trials[0, :])
        thrust_std = np.mean(std_trials[0, :])
        thrust_peak = np.max(np.abs(mean_trials[0, :]))
        stats_text += f"Thrust:\n"
        stats_text += f"  Mean: {thrust_mean:.3f} N\n"
        stats_text += f"  Avg Std: {thrust_std:.3f} N\n"
        stats_text += f"  Peak: {thrust_peak:.3f} N\n\n"
        
        # Lift statistics
        lift_mean = np.mean(mean_trials[1, :])
        lift_std = np.mean(std_trials[1, :])
        lift_peak = np.max(np.abs(mean_trials[1, :]))
        stats_text += f"Lift:\n"
        stats_text += f"  Mean: {lift_mean:.3f} N\n"
        stats_text += f"  Avg Std: {lift_std:.3f} N\n"
        stats_text += f"  Peak: {lift_peak:.3f} N\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

def main():
    root = tk.Tk()
    app = PowerTrialAlignmentGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
