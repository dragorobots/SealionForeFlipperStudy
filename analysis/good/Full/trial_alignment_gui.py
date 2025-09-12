#!/usr/bin/env python3
"""
Trial Alignment GUI - Manual trial alignment with timing controls
Allows user to specify trial timing parameters and visualize aligned trials
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

class TrialAlignmentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trial Alignment GUI - Full Stroke Data")
        self.root.geometry("1600x1000")
        
        # Data storage
        self.data = None
        self.zeros = None
        self.parameters = None
        self.metadata = None
        self.available_params = {}
        self.current_experiment_data = None
        self.current_experiment_zeros = None
        
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
        title_label = ttk.Label(main_frame, text="Trial Alignment Analysis - Full Stroke Data", 
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
        
        ttk.Label(param_frame, text="Yaw (°):").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['yaw'] = tk.StringVar()
        self.param_combos['yaw'] = ttk.Combobox(param_frame, textvariable=self.param_vars['yaw'], 
                                                state="readonly", width=15)
        self.param_combos['yaw'].grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        self.param_combos['yaw'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        # Row 2: Roll and Paddle
        ttk.Label(param_frame, text="Roll (°):").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['roll'] = tk.StringVar()
        self.param_combos['roll'] = ttk.Combobox(param_frame, textvariable=self.param_vars['roll'], 
                                                 state="readonly", width=15)
        self.param_combos['roll'].grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        self.param_combos['roll'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        ttk.Label(param_frame, text="Paddle Transition:").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['paddle'] = tk.StringVar()
        self.param_combos['paddle'] = ttk.Combobox(param_frame, textvariable=self.param_vars['paddle'], 
                                                   state="readonly", width=15)
        self.param_combos['paddle'].grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        self.param_combos['paddle'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        # Row 3: Flow Speed and Load Button
        ttk.Label(param_frame, text="Flow Speed (m/s):").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['flow_speed'] = tk.StringVar()
        self.param_combos['flow_speed'] = ttk.Combobox(param_frame, textvariable=self.param_vars['flow_speed'], 
                                                       state="readonly", width=15)
        self.param_combos['flow_speed'].grid(row=2, column=1, padx=(0, 20), sticky=tk.W)
        self.param_combos['flow_speed'].bind('<<ComboboxSelected>>', self.on_param_change)
        
        # Load experiment button
        load_button = ttk.Button(param_frame, text="Load Experiment", command=self.load_experiment, 
                                style="Accent.TButton")
        load_button.grid(row=2, column=2, columnspan=2, padx=(20, 0), pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(param_frame, text="Select experiment parameters and click Load", foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        # Trial timing controls frame
        timing_frame = ttk.LabelFrame(main_frame, text="Trial Timing Controls", padding="10")
        timing_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Trial timing parameters
        ttk.Label(timing_frame, text="First Trial Offset (s):").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.first_trial_offset_var = tk.StringVar(value="1.5")
        ttk.Entry(timing_frame, textvariable=self.first_trial_offset_var, width=10).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(timing_frame, text="Trial Duration (s):").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.trial_duration_var = tk.StringVar(value="2.2")
        ttk.Entry(timing_frame, textvariable=self.trial_duration_var, width=10).grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(timing_frame, text="Inter-Trial Gap (s):").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.inter_trial_gap_var = tk.StringVar(value="3.8")
        ttk.Entry(timing_frame, textvariable=self.inter_trial_gap_var, width=10).grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(timing_frame, text="Number of Trials:").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.num_trials_var = tk.StringVar(value="5")
        ttk.Entry(timing_frame, textvariable=self.num_trials_var, width=10).grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        
        # Update button
        update_button = ttk.Button(timing_frame, text="Update Alignment", command=self.update_alignment)
        update_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # Auto-detect button
        auto_detect_button = ttk.Button(timing_frame, text="Re-detect Trials", command=self.auto_detect_trials)
        auto_detect_button.grid(row=2, column=2, columnspan=2, pady=(10, 0))
        
        # Data processing frame
        processing_frame = ttk.LabelFrame(main_frame, text="Data Processing", padding="10")
        processing_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Zero correction checkbox
        self.zero_correction_var = tk.BooleanVar()
        zero_check = ttk.Checkbutton(processing_frame, text="Zero the Data", 
                                    variable=self.zero_correction_var, command=self.update_alignment)
        zero_check.grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        
        # Filtering checkbox
        self.apply_filters_var = tk.BooleanVar()
        filter_check = ttk.Checkbutton(processing_frame, text="Apply Filters", 
                                      variable=self.apply_filters_var, command=self.update_alignment)
        filter_check.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
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
        self.cutoff_freq_var = tk.StringVar(value="2.2")
        cf_entry = ttk.Entry(processing_frame, textvariable=self.cutoff_freq_var, width=8)
        cf_entry.grid(row=2, column=1, padx=(0, 20), sticky=tk.W)
        
        # Y-axis controls frame (to the right)
        yaxis_frame = ttk.LabelFrame(main_frame, text="Y-Axis Controls", padding="10")
        yaxis_frame.grid(row=1, column=3, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Thrust Y-axis
        ttk.Label(yaxis_frame, text="Thrust Range:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.thrust_ymin_var = tk.StringVar(value="-6")
        self.thrust_ymax_var = tk.StringVar(value="6")
        ttk.Entry(yaxis_frame, textvariable=self.thrust_ymin_var, width=6).grid(row=0, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.thrust_ymax_var, width=6).grid(row=0, column=3, padx=(0, 0), sticky=tk.W)
        
        # Lift Y-axis
        ttk.Label(yaxis_frame, text="Lift Range:").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.lift_ymin_var = tk.StringVar(value="-6")
        self.lift_ymax_var = tk.StringVar(value="6")
        ttk.Entry(yaxis_frame, textvariable=self.lift_ymin_var, width=6).grid(row=1, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=1, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.lift_ymax_var, width=6).grid(row=1, column=3, padx=(0, 0), sticky=tk.W)
        
        # Arduino Y-axis
        ttk.Label(yaxis_frame, text="Arduino Range:").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.arduino_ymin_var = tk.StringVar(value="-8")
        self.arduino_ymax_var = tk.StringVar(value="1")
        ttk.Entry(yaxis_frame, textvariable=self.arduino_ymin_var, width=6).grid(row=2, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=2, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.arduino_ymax_var, width=6).grid(row=2, column=3, padx=(0, 0), sticky=tk.W)
        
        # X-axis control
        ttk.Label(yaxis_frame, text="X-Axis Range:").grid(row=3, column=0, padx=(0, 5), sticky=tk.W)
        self.xmin_var = tk.StringVar(value="0")
        self.xmax_var = tk.StringVar(value="30")
        ttk.Entry(yaxis_frame, textvariable=self.xmin_var, width=6).grid(row=3, column=1, padx=(0, 5), sticky=tk.W)
        ttk.Label(yaxis_frame, text="to").grid(row=3, column=2, padx=(0, 5))
        ttk.Entry(yaxis_frame, textvariable=self.xmax_var, width=6).grid(row=3, column=3, padx=(0, 0), sticky=tk.W)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(yaxis_frame, text="Trial Statistics", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=4, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30, font=("Courier", 8))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Plotting frame
        plot_frame = ttk.LabelFrame(main_frame, text="Trial Alignment Visualization", padding="10")
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
        """Load the Full Stroke dataset"""
        try:
            # Find the most recent processed data file
            processed_dir = "data/processed"
            h5_files = []
            for root, dirs, files in os.walk(processed_dir):
                for file in files:
                    if file.startswith("FullStroke_Complete") and file.endswith(".h5"):
                        h5_files.append(os.path.join(root, file))
            
            if not h5_files:
                messagebox.showerror("Error", "No FullStroke_Complete.h5 files found in processed data directory")
                return
                
            # Use the most recent file
            h5_file = sorted(h5_files)[-1]
            file_path = h5_file
            
            with h5py.File(file_path, 'r') as f:
                # Load metadata
                self.metadata = dict(f['metadata'].attrs)
                
                # Load data structure - it's organized by experiment keys
                data_group = f['data']
                zeros_group = f['zeros']
                params_group = f['parameters']
                
                # Get all experiment keys
                self.experiment_keys = sorted(data_group.keys(), key=lambda x: int(x.split('_')[1]))
                
                # Load data, zeros, and parameters for all experiments
                self.data = []
                self.zeros = []
                self.parameters = []
                
                for key in self.experiment_keys:
                    # Load data (shape: 3, 15000)
                    exp_data = data_group[key][:]
                    self.data.append(exp_data)
                    
                    # Load zeros (shape: 3, 15000)
                    exp_zeros = zeros_group[key][:]
                    self.zeros.append(exp_zeros)
                    
                    # Load parameters (shape: 4, 1) - [period, yaw, roll, paddle]
                    exp_params = params_group[key][:]
                    # Flatten and add flow speed from metadata
                    params_flat = exp_params.flatten()
                    
                    # Determine flow speed based on experiment number
                    exp_num = int(key.split('_')[1])
                    if exp_num < 63:  # First 63 experiments are from 20-Jan (0.1 m/s)
                        flow_speed = 0.1
                    else:  # Last 63 experiments are from 30-Jan (0.0 m/s)
                        flow_speed = 0.0
                    
                    # Add flow speed to parameters
                    params_with_flow = np.append(params_flat, flow_speed)
                    self.parameters.append(params_with_flow)
                
                # Convert to numpy arrays
                self.data = np.array(self.data)
                self.zeros = np.array(self.zeros)
                self.parameters = np.array(self.parameters)
                
            # Extract available parameters
            self.extract_available_parameters()
            self.populate_dropdowns()
            
            # Get just the filename for display
            filename = os.path.basename(h5_file)
            self.status_label.config(text=f"Loaded {len(self.data)} experiments from {filename}", 
                                   foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_label.config(text="Failed to load data", foreground="red")
    
    def extract_available_parameters(self):
        """Extract unique parameter values from the dataset"""
        if self.parameters is None:
            return
            
        # Extract unique values for each parameter
        self.available_params = {
            'period': sorted(list(set(self.parameters[:, 0]))),
            'yaw': sorted(list(set(self.parameters[:, 1]))),
            'roll': sorted(list(set(self.parameters[:, 2]))),
            'paddle': sorted(list(set(self.parameters[:, 3]))),
            'flow_speed': sorted(list(set(self.parameters[:, 4])))
        }
    
    def populate_dropdowns(self):
        """Populate the parameter dropdown menus"""
        for param, values in self.available_params.items():
            # Convert to strings for display
            str_values = [str(v) for v in values]
            self.param_combos[param]['values'] = str_values
            
            # Set baseline parameters as default
            if param == 'period':
                self.param_vars[param].set("2.25")  # Baseline period
            elif param == 'yaw':
                self.param_vars[param].set("-70")   # Baseline yaw
            elif param == 'roll':
                self.param_vars[param].set("-45")   # Baseline roll
            elif param == 'paddle':
                self.param_vars[param].set("0.5")   # Baseline paddle
            elif param == 'flow_speed':
                self.param_vars[param].set("0.1")   # Default flow speed
            else:
                # Set default to first value for other parameters
                if str_values:
                    self.param_vars[param].set(str_values[0])
    
    def apply_zero_correction(self, exp_data, exp_zeros):
        """Apply zero correction to thrust and lift data"""
        if self.zero_correction_var.get():  # If toggle is ON
            # Calculate zero means for thrust and lift (corrected channel order)
            zero_thrust_mean = exp_zeros[0, :].mean()  # Thrust channel (index 0)
            zero_lift_mean = exp_zeros[1, :].mean()    # Lift channel (index 1)
            
            # Apply correction
            corrected_data = exp_data.copy()
            corrected_data[0, :] -= zero_thrust_mean  # Thrust
            corrected_data[1, :] -= zero_lift_mean    # Lift
            # Arduino (index 2) remains unchanged
            
            return corrected_data
        else:
            return exp_data  # Return raw data
    
    def apply_data_filters(self, data, median_window=10, fs=500, cf=40):
        """Apply the same filtering as your MATLAB function"""
        try:
            # Step 1: Scale by 2.22
            scaled_data = data * 2.22
            
            # Step 2: Median filter - ensure kernel size is odd
            if median_window % 2 == 0:
                median_window += 1  # Make it odd
            median_filtered = np.zeros_like(scaled_data)
            for i in range(min(scaled_data.shape)):
                median_filtered[i, :] = medfilt(scaled_data[i, :], kernel_size=median_window)
            
            # Step 3: Low-pass filter (skip arduino channel - index 2)
            wn = (2/fs) * cf
            # Create Kaiser window manually (equivalent to kaiser(1001, 1) in MATLAB)
            b = firwin(1001, wn, window=('kaiser', 1))
            
            low_pass_filtered = np.zeros_like(median_filtered)
            for i in range(min(median_filtered.shape)):
                if i == 2:  # Arduino channel - only median filter, no low-pass
                    low_pass_filtered[i, :] = median_filtered[i, :]
                else:  # Thrust and Lift channels - apply low-pass filter
                    low_pass_filtered[i, :] = filtfilt(b, [1], median_filtered[i, :])
            
            return low_pass_filtered
            
        except Exception as e:
            print(f"Filter error: {str(e)}")
            raise e
    
    def process_experiment_data(self, exp_data, exp_zeros):
        """Complete data processing pipeline"""
        # Step 1: Apply zero correction (if enabled)
        if self.zero_correction_var.get():
            exp_data = self.apply_zero_correction(exp_data, exp_zeros)
        
        # Step 2: Apply filters (if enabled)
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
    
    def find_experiment_index(self):
        """Find the experiment index matching the selected parameters"""
        if self.parameters is None:
            return None
            
        try:
            # Get selected parameter values
            selected_params = {}
            for param in ['period', 'yaw', 'roll', 'paddle', 'flow_speed']:
                value_str = self.param_vars[param].get()
                if not value_str:
                    return None
                selected_params[param] = float(value_str)
            
            # Find matching experiment
            for i, params in enumerate(self.parameters):
                if (abs(params[0] - selected_params['period']) < 1e-6 and
                    abs(params[1] - selected_params['yaw']) < 1e-6 and
                    abs(params[2] - selected_params['roll']) < 1e-6 and
                    abs(params[3] - selected_params['paddle']) < 1e-6 and
                    abs(params[4] - selected_params['flow_speed']) < 1e-6):
                    return i
            
            return None
            
        except (ValueError, IndexError) as e:
            return None
    
    def detect_trial_timing_from_arduino(self, arduino_signal, fs=500):
        """Automatically detect trial timing from arduino signal"""
        # Use raw signal for detection (smoothing was removing the big jumps)
        # Find significant changes in arduino signal (big jumps)
        # Use difference to find edges
        diff = np.diff(arduino_signal)
        
        # Use threshold to find big jumps
        threshold = 1.0  # Look for jumps > 1.0
        
        # Find significant changes (both positive and negative)
        significant_negative = diff < -threshold  # Away from zero (trial start)
        significant_positive = diff > threshold   # Towards zero (trial end)
        
        negative_indices = np.where(significant_negative)[0]
        positive_indices = np.where(significant_positive)[0]
        
        print(f"Found {len(negative_indices)} negative jumps (away from zero)")
        print(f"Found {len(positive_indices)} positive jumps (towards zero)")
        
        if len(negative_indices) == 0 or len(positive_indices) == 0:
            print("Not enough edges found for trial detection")
            return None
        
        # Step 1: Find first major change away from zero (trial start)
        first_trial_start = None
        for neg_idx in negative_indices:
            # Check if this is the first significant change away from zero
            # Look for the first negative jump that's not preceded by a positive jump
            prev_positive = positive_indices[positive_indices < neg_idx]
            if len(prev_positive) == 0 or (neg_idx - prev_positive[-1] > 100):  # 100 samples = 0.2s gap
                first_trial_start = neg_idx
                break
        
        if first_trial_start is None:
            print("No valid first trial start found")
            return None
        
        print(f"First trial starts at sample {first_trial_start} (time {first_trial_start/fs:.2f}s)")
        
        # Step 2: Detect trial duration (first trial end)
        trial_duration = None
        for pos_idx in positive_indices:
            if pos_idx > first_trial_start:
                trial_duration = pos_idx - first_trial_start
                break
        
        if trial_duration is None:
            print("No trial end found")
            return None
        
        trial_duration_time = trial_duration / fs
        print(f"Trial duration: {trial_duration} samples ({trial_duration_time:.2f}s)")
        
        # Step 3: Detect gap between trials
        inter_trial_gap = None
        for neg_idx in negative_indices:
            if neg_idx > first_trial_start + trial_duration:
                # This is the start of the second trial
                gap_samples = neg_idx - (first_trial_start + trial_duration)
                inter_trial_gap = gap_samples / fs
                break
        
        if inter_trial_gap is None:
            print("No second trial found, using default gap")
            inter_trial_gap = 3.0  # Default 3 second gap
        
        print(f"Inter-trial gap: {inter_trial_gap:.2f}s")
        
        # Step 4: Check if first trial was already happening (ignore if so)
        first_trial_offset = first_trial_start / fs
        
        # Step 5: Calculate number of trials (start with 5, check for overflow)
        num_trials = 5
        total_time_needed = first_trial_offset + (num_trials * trial_duration_time) + ((num_trials - 1) * inter_trial_gap)
        total_time_available = len(arduino_signal) / fs
        
        if total_time_needed > total_time_available:
            print(f"5 trials would overflow data ({total_time_needed:.1f}s > {total_time_available:.1f}s)")
            num_trials = 4
            total_time_needed = first_trial_offset + (num_trials * trial_duration_time) + ((num_trials - 1) * inter_trial_gap)
            if total_time_needed > total_time_available:
                print(f"4 trials would also overflow data ({total_time_needed:.1f}s > {total_time_available:.1f}s)")
                return None
        
        print(f"Using {num_trials} trials")
        
        return {
            'first_offset': first_trial_offset,
            'trial_duration': trial_duration_time,
            'inter_gap': inter_trial_gap,
            'num_trials': num_trials
        }
    
    def auto_detect_trials(self):
        """Re-run automatic trial detection"""
        if self.current_experiment_data is None:
            messagebox.showerror("Error", "No experiment loaded. Please load an experiment first.")
            return
        
        # Process data to get arduino signal for detection
        processed_data = self.process_experiment_data(self.current_experiment_data, self.current_experiment_zeros)
        arduino_signal = processed_data[2, :]  # Arduino channel
        
        # Debug: Print signal info
        print(f"Arduino signal range: {np.min(arduino_signal):.2f} to {np.max(arduino_signal):.2f}")
        print(f"Arduino signal length: {len(arduino_signal)} samples")
        print(f"Arduino signal first 100 samples: {arduino_signal[:100]}")
        
        # Look for the big jumps in the signal
        diff = np.diff(arduino_signal)
        print(f"Signal differences range: {np.min(diff):.3f} to {np.max(diff):.3f}")
        print(f"Largest negative changes: {np.sort(diff)[:10]}")
        print(f"Largest positive changes: {np.sort(diff)[-10:]}")
        
        # Automatically detect trial timing
        fs = float(self.sampling_rate_var.get())
        
        # Find the biggest jumps in the signal
        big_negative_jumps = np.where(diff < -1.0)[0]  # Look for drops > 1.0
        big_positive_jumps = np.where(diff > 1.0)[0]   # Look for rises > 1.0
        print(f"Found {len(big_negative_jumps)} big negative jumps (>1.0)")
        print(f"Found {len(big_positive_jumps)} big positive jumps (>1.0)")
        if len(big_negative_jumps) > 0:
            print(f"Big negative jump times: {big_negative_jumps[:10] / fs}")
        if len(big_positive_jumps) > 0:
            print(f"Big positive jump times: {big_positive_jumps[:10] / fs}")
        timing_info = self.detect_trial_timing_from_arduino(arduino_signal, fs)
        
        if timing_info is not None:
            # Update timing controls with detected values
            self.first_trial_offset_var.set(f"{timing_info['first_offset']:.2f}")
            self.trial_duration_var.set(f"{timing_info['trial_duration']:.2f}")
            self.inter_trial_gap_var.set(f"{timing_info['inter_gap']:.2f}")
            self.num_trials_var.set(f"{timing_info['num_trials']}")
            
            # Update status
            self.status_label.config(text=f"Re-detected {timing_info['num_trials']} trials. Click Update Alignment to see results.", 
                                   foreground="green")
            
            # Auto-update alignment
            self.update_alignment()
        else:
            # Fall back to defaults if detection fails
            self.status_label.config(text="Auto-detection failed. Please adjust timing parameters manually.", 
                                   foreground="orange")
    
    def load_experiment(self):
        """Load the selected experiment data"""
        exp_idx = self.find_experiment_index()
        if exp_idx is None:
            messagebox.showerror("Error", "No experiment found matching the selected parameters")
            return
        
        # Store current experiment data
        self.current_experiment_data = self.data[exp_idx]
        self.current_experiment_zeros = self.zeros[exp_idx]
        
        # Process data to get arduino signal for detection
        processed_data = self.process_experiment_data(self.current_experiment_data, self.current_experiment_zeros)
        arduino_signal = processed_data[2, :]  # Arduino channel
        
        # Automatically detect trial timing
        fs = float(self.sampling_rate_var.get())
        timing_info = self.detect_trial_timing_from_arduino(arduino_signal, fs)
        
        if timing_info is not None:
            # Update timing controls with detected values
            self.first_trial_offset_var.set(f"{timing_info['first_offset']:.2f}")
            self.trial_duration_var.set(f"{timing_info['trial_duration']:.2f}")
            self.inter_trial_gap_var.set(f"{timing_info['inter_gap']:.2f}")
            self.num_trials_var.set(f"{timing_info['num_trials']}")
            
            # Update status
            self.status_label.config(text=f"Loaded experiment {exp_idx}. Auto-detected {timing_info['num_trials']} trials. Adjust timing if needed and click Update Alignment.", 
                                   foreground="green")
        else:
            # Fall back to defaults if detection fails
            self.status_label.config(text=f"Loaded experiment {exp_idx}. Auto-detection failed. Using default timing parameters.", 
                                   foreground="orange")
        
        # Update alignment
        self.update_alignment()
    
    def on_param_change(self, event=None):
        """Called when any parameter selection changes - automatically reload experiment"""
        # Only reload if we have data loaded
        if hasattr(self, 'data') and self.data is not None:
            self.load_experiment()
    
    def extract_trials(self, data, first_offset, trial_duration, inter_gap, num_trials, fs):
        """Extract trials based on timing parameters"""
        trials = []
        
        # Ensure data is 2D (channels, time_points)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        # Calculate exact trial length in samples to ensure consistency
        trial_length_samples = int(trial_duration * fs)
        
        for i in range(num_trials):
            # Calculate trial start time
            trial_start_time = first_offset + i * (trial_duration + inter_gap)
            
            # Convert to sample indices
            start_idx = int(trial_start_time * fs)
            end_idx = start_idx + trial_length_samples  # Use exact length
            
            # Check bounds - data shape is (channels, time_points)
            if start_idx >= 0 and end_idx <= data.shape[1]:
                trial_data = data[:, start_idx:end_idx]
                trials.append(trial_data)
        
        return trials
    
    def calculate_statistics(self, trials):
        """Calculate mean and variance for aligned trials"""
        if len(trials) == 0:
            return None
        
        # Ensure all trials have the same shape
        if len(trials) > 1:
            # Check if all trials have the same shape
            shapes = [trial.shape for trial in trials]
            if not all(shape == shapes[0] for shape in shapes):
                print(f"Warning: Trials have different shapes: {shapes}")
                # Find minimum dimensions
                min_channels = min(shape[0] for shape in shapes)
                min_time = min(shape[1] for shape in shapes)
                # Truncate all trials to minimum size
                trials = [trial[:min_channels, :min_time] for trial in trials]
        
        # Stack all trials
        stacked_trials = np.stack(trials, axis=0)  # Shape: (num_trials, channels, time_points)
        
        # Calculate statistics
        mean_trials = np.mean(stacked_trials, axis=0)  # Mean across trials
        var_trials = np.var(stacked_trials, axis=0)    # Variance across trials
        std_trials = np.std(stacked_trials, axis=0)    # Standard deviation across trials
        
        return {
            'mean': mean_trials,
            'variance': var_trials,
            'std': std_trials,
            'num_trials': len(trials)
        }
    
    def update_alignment(self):
        """Update the trial alignment visualization"""
        if self.current_experiment_data is None:
            return
        
        try:
            # Get timing parameters
            first_offset = float(self.first_trial_offset_var.get())
            trial_duration = float(self.trial_duration_var.get())
            inter_gap = float(self.inter_trial_gap_var.get())
            num_trials = int(self.num_trials_var.get())
            fs = float(self.sampling_rate_var.get())
            
            # Process data
            processed_data = self.process_experiment_data(self.current_experiment_data, self.current_experiment_zeros)
            
            # Extract trials
            trials = self.extract_trials(processed_data, first_offset, trial_duration, inter_gap, num_trials, fs)
            
            if len(trials) == 0:
                messagebox.showerror("Error", "No trials could be extracted with current parameters")
                return
            
            # Calculate statistics
            stats = self.calculate_statistics(trials)
            
            # Clear previous plots
            self.ax_thrust.clear()
            self.ax_lift.clear()
            self.ax_arduino.clear()
            
            # Plot individual trials
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
            time = np.arange(trials[0].shape[1]) / fs
            
            for i, trial_data in enumerate(trials):
                color = colors[i % len(colors)]
                alpha = 0.6
                
                # Plot individual trials
                self.ax_thrust.plot(time, trial_data[0, :], color=color, linewidth=1, 
                                   alpha=alpha, label=f'Trial {i+1}')
                self.ax_lift.plot(time, trial_data[1, :], color=color, linewidth=1, 
                                 alpha=alpha, label=f'Trial {i+1}')
                self.ax_arduino.plot(time, trial_data[2, :], color=color, linewidth=1, 
                                    alpha=alpha, label=f'Trial {i+1}')
            
            # Plot mean
            if stats is not None:
                self.ax_thrust.plot(time, stats['mean'][0, :], color='black', linewidth=3, 
                                   label='Mean', alpha=0.8)
                self.ax_lift.plot(time, stats['mean'][1, :], color='black', linewidth=3, 
                                 label='Mean', alpha=0.8)
                self.ax_arduino.plot(time, stats['mean'][2, :], color='black', linewidth=3, 
                                    label='Mean', alpha=0.8)
            
            # Configure plots
            self.ax_thrust.set_title(f"Thrust Force - {len(trials)} Aligned Trials", 
                                   fontsize=12, fontweight="bold")
            self.ax_thrust.set_ylabel("Force (N)")
            self.ax_thrust.grid(True, alpha=0.3)
            self.ax_thrust.legend()
            
            self.ax_lift.set_title(f"Lift Force - {len(trials)} Aligned Trials", 
                                 fontsize=12, fontweight="bold")
            self.ax_lift.set_ylabel("Force (N)")
            self.ax_lift.grid(True, alpha=0.3)
            self.ax_lift.legend()
            
            self.ax_arduino.set_title(f"Arduino Sync Signal - {len(trials)} Aligned Trials", 
                                    fontsize=12, fontweight="bold")
            self.ax_arduino.set_xlabel("Time (s)")
            self.ax_arduino.set_ylabel("Signal")
            self.ax_arduino.grid(True, alpha=0.3)
            self.ax_arduino.legend()
            
            # Set axis ranges
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
            
            # Update statistics display
            if stats is not None:
                stats_text = f"Trial Statistics:\n"
                stats_text += f"Number of trials: {stats['num_trials']}\n"
                stats_text += f"Trial duration: {trial_duration:.1f}s\n\n"
                
                # Thrust statistics
                thrust_mean = np.mean(stats['mean'][0, :])
                thrust_std = np.mean(stats['std'][0, :])
                stats_text += f"Thrust:\n"
                stats_text += f"  Mean: {thrust_mean:.3f} N\n"
                stats_text += f"  Avg Std: {thrust_std:.3f} N\n\n"
                
                # Lift statistics
                lift_mean = np.mean(stats['mean'][1, :])
                lift_std = np.mean(stats['std'][1, :])
                stats_text += f"Lift:\n"
                stats_text += f"  Mean: {lift_mean:.3f} N\n"
                stats_text += f"  Avg Std: {lift_std:.3f} N\n\n"
                
                # Peak forces
                thrust_peak = np.max(np.abs(stats['mean'][0, :]))
                lift_peak = np.max(np.abs(stats['mean'][1, :]))
                stats_text += f"Peak Forces:\n"
                stats_text += f"  Thrust: {thrust_peak:.3f} N\n"
                stats_text += f"  Lift: {lift_peak:.3f} N\n"
                
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, stats_text)
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update alignment: {str(e)}")
            self.status_label.config(text="Failed to update alignment", foreground="red")

def main():
    root = tk.Tk()
    app = TrialAlignmentGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
