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

class FullStrokeGUIAnalysis:
    def __init__(self, root):
        self.root = root
        self.root.title("Full Stroke Data Analysis GUI")
        self.root.geometry("1200x800")
        
        # Data storage
        self.data = None
        self.zeros = None
        self.parameters = None
        self.metadata = None
        self.available_params = {}
        
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
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Full Stroke Data Analysis", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Parameter selection frame
        param_frame = ttk.LabelFrame(main_frame, text="Parameter Selection", padding="10")
        param_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Parameter dropdowns
        self.param_vars = {}
        self.param_combos = {}
        
        # Row 1: Period and Yaw
        ttk.Label(param_frame, text="Period (s):").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['period'] = tk.StringVar()
        self.param_combos['period'] = ttk.Combobox(param_frame, textvariable=self.param_vars['period'], 
                                                   state="readonly", width=15)
        self.param_combos['period'].grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(param_frame, text="Yaw (°):").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['yaw'] = tk.StringVar()
        self.param_combos['yaw'] = ttk.Combobox(param_frame, textvariable=self.param_vars['yaw'], 
                                                state="readonly", width=15)
        self.param_combos['yaw'].grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        
        # Row 2: Roll and Paddle
        ttk.Label(param_frame, text="Roll (°):").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['roll'] = tk.StringVar()
        self.param_combos['roll'] = ttk.Combobox(param_frame, textvariable=self.param_vars['roll'], 
                                                 state="readonly", width=15)
        self.param_combos['roll'].grid(row=1, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(param_frame, text="Paddle Transition:").grid(row=1, column=2, padx=(0, 5), sticky=tk.W)
        self.param_vars['paddle'] = tk.StringVar()
        self.param_combos['paddle'] = ttk.Combobox(param_frame, textvariable=self.param_vars['paddle'], 
                                                   state="readonly", width=15)
        self.param_combos['paddle'].grid(row=1, column=3, padx=(0, 20), sticky=tk.W)
        
        # Row 3: Flow Speed and Plot Button
        ttk.Label(param_frame, text="Flow Speed (m/s):").grid(row=2, column=0, padx=(0, 5), sticky=tk.W)
        self.param_vars['flow_speed'] = tk.StringVar()
        self.param_combos['flow_speed'] = ttk.Combobox(param_frame, textvariable=self.param_vars['flow_speed'], 
                                                       state="readonly", width=15)
        self.param_combos['flow_speed'].grid(row=2, column=1, padx=(0, 20), sticky=tk.W)
        
        # Plot button
        plot_button = ttk.Button(param_frame, text="Plot Now", command=self.plot_data, 
                                style="Accent.TButton")
        plot_button.grid(row=2, column=2, columnspan=2, padx=(20, 0), pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(param_frame, text="Ready to plot", foreground="green")
        self.status_label.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        # Data processing frame
        processing_frame = ttk.LabelFrame(main_frame, text="Data Processing", padding="10")
        processing_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Zero correction checkbox
        self.zero_correction_var = tk.BooleanVar()
        zero_check = ttk.Checkbutton(processing_frame, text="Zero the Data", 
                                    variable=self.zero_correction_var)
        zero_check.grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        
        # Filtering checkbox
        self.apply_filters_var = tk.BooleanVar()
        filter_check = ttk.Checkbutton(processing_frame, text="Apply Filters", 
                                      variable=self.apply_filters_var)
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
        
        # Y-axis controls frame (to the right of processing frame)
        yaxis_frame = ttk.LabelFrame(main_frame, text="Y-Axis Controls", padding="10")
        yaxis_frame.grid(row=1, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
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
        
        # Plotting frame
        plot_frame = ttk.LabelFrame(main_frame, text="Data Plots", padding="10")
        plot_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax_thrust = self.fig.add_subplot(3, 1, 1)
        self.ax_lift = self.fig.add_subplot(3, 1, 2)
        self.ax_arduino = self.fig.add_subplot(3, 1, 3)
        
        # Configure subplots
        self.ax_thrust.set_title("Thrust Force", fontsize=12, fontweight="bold")
        self.ax_thrust.set_ylabel("Force (N)")
        self.ax_thrust.grid(True, alpha=0.3)
        
        self.ax_lift.set_title("Lift Force", fontsize=12, fontweight="bold")
        self.ax_lift.set_ylabel("Force (N)")
        self.ax_lift.grid(True, alpha=0.3)
        
        self.ax_arduino.set_title("Arduino Sync Signal", fontsize=12, fontweight="bold")
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
            if not os.path.exists(processed_dir):
                messagebox.showerror("Error", f"Processed data directory not found: {processed_dir}")
                return
                
            # Look for FullStroke_Complete files in subdirectories
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
            print(f"Filter error: {e}")
            print(f"Parameters: median_window={median_window}, fs={fs}, cf={cf}")
            try:
                print(f"Normalized frequency wn={wn}")
            except:
                print("Normalized frequency wn not calculated yet")
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
    
    def plot_data(self):
        """Plot the data for the selected parameters"""
        if self.data is None:
            messagebox.showerror("Error", "No data loaded")
            return
            
        # Find experiment index
        exp_idx = self.find_experiment_index()
        if exp_idx is None:
            messagebox.showerror("Error", "No experiment found matching the selected parameters")
            return
            
        try:
            # Get experiment data and zeros
            exp_data = self.data[exp_idx]  # Shape: (3, 15000)
            exp_zeros = self.zeros[exp_idx]  # Shape: (3, 15000)
            exp_params = self.parameters[exp_idx]
            
            # Apply data processing pipeline
            processed_data = self.process_experiment_data(exp_data, exp_zeros)
            
            # Create time vector (500 Hz sampling rate, 30 seconds total)
            time = np.arange(processed_data.shape[1]) / 500.0  # Convert to seconds
            
            # Clear previous plots
            self.ax_thrust.clear()
            self.ax_lift.clear()
            self.ax_arduino.clear()
            
            # Plot thrust (channel 0 - corrected order)
            self.ax_thrust.plot(time, processed_data[0, :], 'b-', linewidth=1)
            self.ax_thrust.set_title(f"Thrust Force - Exp {exp_idx}", fontsize=12, fontweight="bold")
            self.ax_thrust.set_ylabel("Force (N)")
            self.ax_thrust.grid(True, alpha=0.3)
            # Set Y-axis range
            try:
                thrust_ymin = float(self.thrust_ymin_var.get())
                thrust_ymax = float(self.thrust_ymax_var.get())
                self.ax_thrust.set_ylim(thrust_ymin, thrust_ymax)
            except ValueError:
                pass  # Use auto-scaling if invalid range
            
            # Plot lift (channel 1 - corrected order)
            self.ax_lift.plot(time, processed_data[1, :], 'r-', linewidth=1)
            self.ax_lift.set_title(f"Lift Force - Exp {exp_idx}", fontsize=12, fontweight="bold")
            self.ax_lift.set_ylabel("Force (N)")
            self.ax_lift.grid(True, alpha=0.3)
            # Set Y-axis range
            try:
                lift_ymin = float(self.lift_ymin_var.get())
                lift_ymax = float(self.lift_ymax_var.get())
                self.ax_lift.set_ylim(lift_ymin, lift_ymax)
            except ValueError:
                pass  # Use auto-scaling if invalid range
            
            # Plot arduino (channel 2)
            self.ax_arduino.plot(time, processed_data[2, :], 'g-', linewidth=1)
            self.ax_arduino.set_title(f"Arduino Sync Signal - Exp {exp_idx}", fontsize=12, fontweight="bold")
            self.ax_arduino.set_xlabel("Time (s)")
            self.ax_arduino.set_ylabel("Signal")
            self.ax_arduino.grid(True, alpha=0.3)
            # Set Y-axis range
            try:
                arduino_ymin = float(self.arduino_ymin_var.get())
                arduino_ymax = float(self.arduino_ymax_var.get())
                self.ax_arduino.set_ylim(arduino_ymin, arduino_ymax)
            except ValueError:
                pass  # Use auto-scaling if invalid range
            
            # Set X-axis range for all plots
            try:
                xmin = float(self.xmin_var.get())
                xmax = float(self.xmax_var.get())
                self.ax_thrust.set_xlim(xmin, xmax)
                self.ax_lift.set_xlim(xmin, xmax)
                self.ax_arduino.set_xlim(xmin, xmax)
            except ValueError:
                pass  # Use auto-scaling if invalid range
            
            # Add parameter info to the plot
            param_text = (f"Period: {exp_params[0]:.2f}s, Yaw: {exp_params[1]:.0f}°, "
                         f"Roll: {exp_params[2]:.0f}°, Paddle: {exp_params[3]:.2f}, "
                         f"Flow: {exp_params[4]:.1f} m/s")
            self.fig.suptitle(param_text, fontsize=10, y=0.98)
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
            # Update status with processing info
            processing_steps = []
            if self.zero_correction_var.get():
                processing_steps.append("Zero corrected")
            if self.apply_filters_var.get():
                processing_steps.append("Filtered")
            if not processing_steps:
                processing_steps.append("Raw data")
            
            status_text = f"Plotted experiment {exp_idx} ({', '.join(processing_steps)})"
            self.status_label.config(text=status_text, foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot data: {str(e)}")
            self.status_label.config(text="Failed to plot data", foreground="red")

def main():
    root = tk.Tk()
    app = FullStrokeGUIAnalysis(root)
    root.mainloop()

if __name__ == "__main__":
    main()
