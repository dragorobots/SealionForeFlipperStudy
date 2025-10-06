#!/usr/bin/env python3
"""
Combined Full-Stroke Analysis GUI

This GUI combines:
1. Trial Traces Plotter (Tab 1) - with experiment selection and window finder
2. Overview Metrics (Tabs 2-4) - Mean Force, Peak Location, Vector plots

The experiment selection from Tab 1 determines which experiments are analyzed
in the overview metrics tabs. The window finder allows interactive selection
of the evaluation window for metrics calculation.

Author: Generated for Sea Lion AUV Flow Tank Analysis
Date: 2025-01-27
"""

import sys
import os
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QComboBox, QCheckBox,
                             QFileDialog, QMessageBox, QProgressBar, QGroupBox,
                             QGridLayout, QSpinBox, QDoubleSpinBox, QTabWidget,
                             QTextEdit, QSplitter, QSlider, QLineEdit, QListWidget,
                             QListWidgetItem, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import json
from datetime import datetime

class CombinedFullStrokeGUI(QMainWindow):
    """Combined GUI for trial traces and overview metrics"""
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.selected_experiments = set()  # Set of selected experiment keys
        self.window_start = 0.0  # Start of evaluation window (normalized phase)
        self.window_end = 1.0    # End of evaluation window (normalized phase)
        self.trial_traces_file = None
        self.window_finder_enabled = False
        self.window_lines = None  # Will store the vertical line objects
        
        self.init_ui()
        self.auto_load_data()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Combined Full-Stroke Analysis GUI")
        self.setGeometry(100, 100, 1800, 1200)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel for controls
        self.create_control_panel(splitter)
        
        # Right panel for tabbed plots
        self.create_tabbed_plot_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([450, 1350])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready - Auto-loading mean traces data...")
        
    def create_control_panel(self, parent):
        """Create the control panel with data loading and plot options"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Data loading section
        data_group = QGroupBox("Data Status")
        data_layout = QVBoxLayout(data_group)
        
        self.data_path_label = QLabel("Auto-loading mean traces data...")
        self.data_path_label.setWordWrap(True)
        data_layout.addWidget(self.data_path_label)
        
        control_layout.addWidget(data_group)
        
        # Experiment selection section
        exp_group = QGroupBox("Experiment Selection")
        exp_layout = QVBoxLayout(exp_group)
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_experiments)
        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self.select_none_experiments)
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.select_none_button)
        exp_layout.addLayout(button_layout)
        
        # Experiment list
        self.experiment_list = QListWidget()
        self.experiment_list.setSelectionMode(QListWidget.MultiSelection)
        self.experiment_list.itemChanged.connect(self.on_experiment_selection_changed)
        exp_layout.addWidget(self.experiment_list)
        
        control_layout.addWidget(exp_group)
        
        # Window finder section
        window_group = QGroupBox("Window Finder")
        window_layout = QVBoxLayout(window_group)
        
        # Window finder toggle
        self.window_finder_checkbox = QCheckBox("Enable Window Finder")
        self.window_finder_checkbox.toggled.connect(self.toggle_window_finder)
        window_layout.addWidget(self.window_finder_checkbox)
        
        # Window sliders
        window_layout.addWidget(QLabel("Window Start:"))
        self.window_start_slider = QSlider(Qt.Horizontal)
        self.window_start_slider.setRange(0, 100)
        self.window_start_slider.setValue(0)
        self.window_start_slider.valueChanged.connect(self.update_window_start_from_slider)
        window_layout.addWidget(self.window_start_slider)
        
        window_layout.addWidget(QLabel("Window End:"))
        self.window_end_slider = QSlider(Qt.Horizontal)
        self.window_end_slider.setRange(0, 100)
        self.window_end_slider.setValue(100)
        self.window_end_slider.valueChanged.connect(self.update_window_end_from_slider)
        window_layout.addWidget(self.window_end_slider)
        
        # Choose window button
        self.choose_window_button = QPushButton("Choose Window")
        self.choose_window_button.clicked.connect(self.choose_window)
        self.choose_window_button.setEnabled(False)
        window_layout.addWidget(self.choose_window_button)
        
        # Current window display
        self.window_display = QLabel("Window: 0.00 - 1.00")
        window_layout.addWidget(self.window_display)
        
        control_layout.addWidget(window_group)
        
        # Visual encoding options
        encoding_group = QGroupBox("Visual Encoding")
        encoding_layout = QGridLayout(encoding_group)
        
        encoding_layout.addWidget(QLabel("Flow Speed Colors:"), 0, 0)
        self.flow_speed_colormap = QComboBox()
        self.flow_speed_colormap.addItems(["viridis", "plasma", "inferno", "magma", "coolwarm"])
        encoding_layout.addWidget(self.flow_speed_colormap, 0, 1)
        
        encoding_layout.addWidget(QLabel("Line Styles:"), 1, 0)
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["solid", "dashed", "dotted", "dashdot"])
        encoding_layout.addWidget(self.line_style_combo, 1, 1)
        
        encoding_layout.addWidget(QLabel("Marker Shapes:"), 2, 0)
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(["o", "s", "^", "v", "D", "p", "*", "h"])
        encoding_layout.addWidget(self.marker_combo, 2, 1)
        
        control_layout.addWidget(encoding_group)
        
        # Plot actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(action_group)
        
        self.plot_traces_button = QPushButton("Plot Selected Traces")
        self.plot_traces_button.clicked.connect(self.plot_selected_traces)
        self.plot_traces_button.setEnabled(False)
        action_layout.addWidget(self.plot_traces_button)
        
        self.plot_overview_button = QPushButton("Generate Overview Plots")
        self.plot_overview_button.clicked.connect(self.generate_all_overview_plots)
        self.plot_overview_button.setEnabled(False)
        action_layout.addWidget(self.plot_overview_button)
        
        self.export_png_button = QPushButton("Export Current Tab PNG")
        self.export_png_button.clicked.connect(self.export_current_tab_png)
        self.export_png_button.setEnabled(False)
        action_layout.addWidget(self.export_png_button)
        
        self.export_pdf_button = QPushButton("Export Current Tab PDF")
        self.export_pdf_button.clicked.connect(self.export_current_tab_pdf)
        self.export_pdf_button.setEnabled(False)
        action_layout.addWidget(self.export_pdf_button)
        
        self.export_csv_button = QPushButton("Export All Data CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setEnabled(False)
        action_layout.addWidget(self.export_csv_button)
        
        control_layout.addWidget(action_group)
        
        # Data info section
        info_group = QGroupBox("Data Information")
        info_layout = QVBoxLayout(info_group)
        
        self.data_info_text = QTextEdit()
        self.data_info_text.setMaximumHeight(150)
        self.data_info_text.setReadOnly(True)
        info_layout.addWidget(self.data_info_text)
        
        control_layout.addWidget(info_group)
        
        control_layout.addStretch()
        parent.addWidget(control_widget)
        
    def create_tabbed_plot_panel(self, parent):
        """Create the tabbed plot panel with matplotlib canvases"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        plot_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_traces_tab()
        self.create_mean_force_tab()
        self.create_peak_location_tab()
        self.create_vector_tab()
        
        parent.addWidget(plot_widget)
        
    def create_traces_tab(self):
        """Create the trial traces tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create matplotlib figure for traces
        self.traces_figure = Figure(figsize=(14, 10))
        self.traces_canvas = FigureCanvas(self.traces_figure)
        layout.addWidget(self.traces_canvas)
        
        self.tab_widget.addTab(tab, "Trial Traces")
        
    def create_mean_force_tab(self):
        """Create the mean force tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create matplotlib figure for mean force
        self.mean_force_figure = Figure(figsize=(12, 8))
        self.mean_force_canvas = FigureCanvas(self.mean_force_figure)
        layout.addWidget(self.mean_force_canvas)
        
        self.tab_widget.addTab(tab, "Mean Force")
        
    def create_peak_location_tab(self):
        """Create the peak location tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create matplotlib figure for peak location
        self.peak_location_figure = Figure(figsize=(12, 8))
        self.peak_location_canvas = FigureCanvas(self.peak_location_figure)
        layout.addWidget(self.peak_location_canvas)
        
        self.tab_widget.addTab(tab, "Peak Location")
        
    def create_vector_tab(self):
        """Create the vector tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create matplotlib figure for vector plot
        self.vector_figure = Figure(figsize=(12, 8))
        self.vector_canvas = FigureCanvas(self.vector_figure)
        layout.addWidget(self.vector_canvas)
        
        self.tab_widget.addTab(tab, "Vector Plot")
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
    def auto_load_data(self):
        """Automatically load the mean traces data"""
        # Look for the TrialTraces_Complete file
        possible_paths = [
            "data/processed/2025-01-27_ProcessedData/TrialTraces_Complete_2025-01-27.h5",
            "data/processed/TrialTraces_Complete_2025-01-27.h5",
            "TrialTraces_Complete_2025-01-27.h5"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.trial_traces_file = path
                self.load_trial_traces_data()
                return
                
        # If not found, show error
        QMessageBox.warning(self, "Data Not Found", 
                           "Could not find TrialTraces_Complete_2025-01-27.h5 file.\n"
                           "Please ensure the processed data is available.")
        self.statusBar().showMessage("Data file not found")
        
    def load_trial_traces_data(self):
        """Load the trial traces data from HDF5 file"""
        try:
            with h5py.File(self.trial_traces_file, 'r') as f:
                self.data = {
                    'experiments': {},
                    'time_vector': None
                }
                
                # Load all experiments
                for exp_key in f['experiments'].keys():
                    exp_group = f['experiments'][exp_key]
                    
                    # Load parameters
                    params = {}
                    for param_key in exp_group['parameters'].keys():
                        params[param_key] = exp_group['parameters'][param_key][()]
                    
                    # Load mean traces
                    thrust_mean = np.array(exp_group['thrust']['mean_trace'])
                    lift_mean = np.array(exp_group['lift']['mean_trace'])
                    
                    # Load time vector (same for all experiments)
                    if self.data['time_vector'] is None:
                        self.data['time_vector'] = np.array(exp_group['time_vector'])
                    
                    # Store experiment data
                    self.data['experiments'][exp_key] = {
                        'parameters': params,
                        'thrust_mean': thrust_mean,
                        'lift_mean': lift_mean,
                        'time_vector': np.array(exp_group['time_vector'])
                    }
                
                # Populate experiment list
                self.populate_experiment_list()
                
                # Update UI
                self.data_path_label.setText(f"Loaded: {len(self.data['experiments'])} experiments")
                self.plot_traces_button.setEnabled(True)
                self.plot_overview_button.setEnabled(True)
                self.export_png_button.setEnabled(True)
                self.export_pdf_button.setEnabled(True)
                self.export_csv_button.setEnabled(True)
                
                # Update data info
                self.update_data_info()
                
                self.statusBar().showMessage(f"Loaded {len(self.data['experiments'])} experiments from mean traces")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load trial traces data:\n{str(e)}")
            self.statusBar().showMessage("Failed to load data")
            
    def populate_experiment_list(self):
        """Populate the experiment selection list"""
        self.experiment_list.clear()
        
        for exp_key, exp_data in self.data['experiments'].items():
            params = exp_data['parameters']
            
            # Create display text with key parameters
            display_text = f"{exp_key}: "
            param_parts = []
            for key, value in params.items():
                if isinstance(value, (int, float)):
                    param_parts.append(f"{key}={value:.2f}")
                else:
                    param_parts.append(f"{key}={value}")
            
            display_text += ", ".join(param_parts)
            
            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, exp_key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.experiment_list.addItem(item)
            
    def select_all_experiments(self):
        """Select all experiments"""
        for i in range(self.experiment_list.count()):
            item = self.experiment_list.item(i)
            item.setCheckState(Qt.Checked)
            
    def select_none_experiments(self):
        """Select no experiments"""
        for i in range(self.experiment_list.count()):
            item = self.experiment_list.item(i)
            item.setCheckState(Qt.Unchecked)
            
    def on_experiment_selection_changed(self):
        """Handle experiment selection changes"""
        self.selected_experiments.clear()
        
        for i in range(self.experiment_list.count()):
            item = self.experiment_list.item(i)
            if item.checkState() == Qt.Checked:
                exp_key = item.data(Qt.UserRole)
                self.selected_experiments.add(exp_key)
                
        # Update status
        self.statusBar().showMessage(f"Selected {len(self.selected_experiments)} experiments")
        
    def toggle_window_finder(self, enabled):
        """Toggle window finder mode"""
        self.window_finder_enabled = enabled
        self.choose_window_button.setEnabled(enabled)
        
        if enabled:
            self.statusBar().showMessage("Window finder enabled - adjust sliders to set window")
        else:
            self.statusBar().showMessage("Window finder disabled")
            
    def update_window_start_from_slider(self, value):
        """Update window start from slider"""
        self.window_start = value / 100.0
        self.update_window_display()
        if self.window_finder_enabled:
            self.update_window_lines()
            
    def update_window_end_from_slider(self, value):
        """Update window end from slider"""
        self.window_end = value / 100.0
        self.update_window_display()
        if self.window_finder_enabled:
            self.update_window_lines()
            
    def update_window_display(self):
        """Update the window display label"""
        self.window_display.setText(f"Window: {self.window_start:.2f} - {self.window_end:.2f}")
        
    def choose_window(self):
        """Choose the current window for overview metrics"""
        if self.window_start >= self.window_end:
            QMessageBox.warning(self, "Invalid Window", "Window start must be less than window end")
            return
            
        self.statusBar().showMessage(f"Window set to {self.window_start:.2f} - {self.window_end:.2f}")
        self.update_data_info()
        
    def update_window_lines(self):
        """Update the vertical lines on the traces plot"""
        if not self.window_finder_enabled or not hasattr(self, 'traces_figure'):
            return
            
        # Clear existing lines
        if self.window_lines:
            for line in self.window_lines:
                line.remove()
            self.window_lines = None
            
        # Add new lines if traces are plotted
        if self.traces_figure.get_axes():
            ax = self.traces_figure.get_axes()[0]
            xlim = ax.get_xlim()
            
            # Convert normalized phase to actual time
            time_vector = self.data['time_vector']
            time_norm = (time_vector - time_vector.min()) / (time_vector.max() - time_vector.min())
            
            start_time = np.interp(self.window_start, time_norm, time_vector)
            end_time = np.interp(self.window_end, time_norm, time_vector)
            
            # Draw vertical lines
            line1 = ax.axvline(start_time, color='red', linestyle='--', linewidth=2, alpha=0.8)
            line2 = ax.axvline(end_time, color='red', linestyle='--', linewidth=2, alpha=0.8)
            
            self.window_lines = [line1, line2]
            self.traces_canvas.draw()
            
    def plot_selected_traces(self):
        """Plot the selected experiment traces"""
        if not self.selected_experiments:
            QMessageBox.warning(self, "No Selection", "Please select at least one experiment")
            return
            
        try:
            self.traces_figure.clear()
            ax = self.traces_figure.add_subplot(1, 1, 1)
            
            colors = plt.cm.tab10(np.linspace(0, 1, len(self.selected_experiments)))
            
            for i, exp_key in enumerate(self.selected_experiments):
                if exp_key in self.data['experiments']:
                    exp_data = self.data['experiments'][exp_key]
                    time_vector = exp_data['time_vector']
                    thrust_trace = exp_data['thrust_mean']
                    lift_trace = exp_data['lift_mean']
                    
                    # Plot thrust and lift traces
                    ax.plot(time_vector, thrust_trace, color=colors[i], 
                           label=f'{exp_key} Thrust', alpha=0.7)
                    ax.plot(time_vector, lift_trace, color=colors[i], 
                           linestyle='--', label=f'{exp_key} Lift', alpha=0.7)
            
            ax.set_xlabel('Time')
            ax.set_ylabel('Force')
            ax.set_title('Selected Experiment Traces')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
            
            self.traces_figure.tight_layout()
            self.traces_canvas.draw()
            
            # Update window lines if window finder is enabled
            if self.window_finder_enabled:
                self.update_window_lines()
                
            self.statusBar().showMessage(f"Plotted {len(self.selected_experiments)} experiments")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot traces:\n{str(e)}")
            
    def generate_all_overview_plots(self):
        """Generate all overview plots using selected experiments"""
        if not self.selected_experiments:
            QMessageBox.warning(self, "No Selection", "Please select at least one experiment")
            return
            
        try:
            # Process data for plotting (only selected experiments)
            plot_data = self.process_data_for_plotting()
            
            # Generate plots for each tab
            self.generate_mean_force_plot(plot_data)
            self.generate_peak_location_plot(plot_data)
            self.generate_vector_plot(plot_data)
            
            self.statusBar().showMessage("All overview plots generated successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate overview plots:\n{str(e)}")
            
    def process_data_for_plotting(self):
        """Process the loaded mean traces data for plotting (selected experiments only)"""
        plot_data = {
            'twist': [],
            'sweep': [],
            'flow_speed': [],
            'stroke_period': [],
            'phase_overlap': [],
            'thrust_mean': [],
            'lift_mean': [],
            'thrust_peak_location': [],
            'lift_peak_location': [],
            'thrust_peak_value': [],
            'lift_peak_value': []
        }
        
        # Extract parameters and calculate metrics from selected experiments only
        for exp_key in self.selected_experiments:
            if exp_key not in self.data['experiments']:
                continue
                
            exp_data = self.data['experiments'][exp_key]
            params = exp_data['parameters']
            
            # Extract parameters (adapt based on your actual parameter names)
            plot_data['twist'].append(params.get('twist', 0.0))
            plot_data['sweep'].append(params.get('sweep', 0.0))
            plot_data['flow_speed'].append(params.get('flow_speed', 0.0))
            plot_data['stroke_period'].append(params.get('stroke_period', 0.0))
            plot_data['phase_overlap'].append(params.get('phase_overlap', 0.0))
            
            # Get mean traces
            thrust_trace = exp_data['thrust_mean']
            lift_trace = exp_data['lift_mean']
            time_vector = exp_data['time_vector']
            
            # Normalize time vector to 0-1 phase
            time_norm = (time_vector - time_vector.min()) / (time_vector.max() - time_vector.min())
            
            # Apply evaluation window
            window_mask = (time_norm >= self.window_start) & (time_norm <= self.window_end)
            thrust_windowed = thrust_trace[window_mask]
            lift_windowed = lift_trace[window_mask]
            time_windowed = time_norm[window_mask]
            
            # Calculate mean forces within window
            plot_data['thrust_mean'].append(np.mean(thrust_windowed))
            plot_data['lift_mean'].append(np.mean(lift_windowed))
            
            # Calculate peak locations and values within window
            thrust_peak_idx = np.argmax(np.abs(thrust_windowed))
            lift_peak_idx = np.argmax(np.abs(lift_windowed))
            
            plot_data['thrust_peak_location'].append(time_windowed[thrust_peak_idx])
            plot_data['lift_peak_location'].append(time_windowed[lift_peak_idx])
            plot_data['thrust_peak_value'].append(thrust_windowed[thrust_peak_idx])
            plot_data['lift_peak_value'].append(lift_windowed[lift_peak_idx])
                
        # Convert to numpy arrays
        for key in plot_data.keys():
            plot_data[key] = np.array(plot_data[key])
            
        return plot_data
        
    def generate_mean_force_plot(self, plot_data):
        """Generate mean force plot with lift and thrust channels"""
        self.mean_force_figure.clear()
        
        # Create subplots for lift and thrust
        ax1 = self.mean_force_figure.add_subplot(1, 2, 1)
        ax2 = self.mean_force_figure.add_subplot(1, 2, 2)
        
        # Plot mean lift
        self.plot_mean_force_channel(ax1, plot_data, 'lift', 'Mean Lift')
        
        # Plot mean thrust
        self.plot_mean_force_channel(ax2, plot_data, 'thrust', 'Mean Thrust')
        
        self.mean_force_figure.tight_layout()
        self.mean_force_canvas.draw()
        
    def generate_peak_location_plot(self, plot_data):
        """Generate peak location plot with lift and thrust channels"""
        self.peak_location_figure.clear()
        
        # Create subplots for lift and thrust
        ax1 = self.peak_location_figure.add_subplot(1, 2, 1)
        ax2 = self.peak_location_figure.add_subplot(1, 2, 2)
        
        # Plot peak lift location
        self.plot_peak_location_channel(ax1, plot_data, 'lift', 'Peak Lift Location')
        
        # Plot peak thrust location
        self.plot_peak_location_channel(ax2, plot_data, 'thrust', 'Peak Thrust Location')
        
        self.peak_location_figure.tight_layout()
        self.peak_location_canvas.draw()
        
    def generate_vector_plot(self, plot_data):
        """Generate vector plot with thrust on X-axis and lift on Y-axis"""
        self.vector_figure.clear()
        
        ax = self.vector_figure.add_subplot(1, 1, 1)
        
        # Plot vectors as arrows
        self.plot_force_vectors(ax, plot_data)
        
        self.vector_figure.tight_layout()
        self.vector_canvas.draw()
        
    def plot_mean_force_channel(self, ax, plot_data, channel, title):
        """Plot mean force for a specific channel (lift or thrust)"""
        ax.set_title(title)
        ax.set_xlabel('Twist')
        ax.set_ylabel('Mean Force')
        
        if len(plot_data['twist']) > 0:
            # Use real mean force data
            if channel == 'thrust':
                mean_forces = plot_data['thrust_mean']
            else:  # lift
                mean_forces = plot_data['lift_mean']
                
            scatter = ax.scatter(plot_data['twist'], mean_forces, 
                               c=plot_data['flow_speed'], 
                               cmap=self.flow_speed_colormap.currentText(),
                               s=50, alpha=0.7)
            ax.grid(True, alpha=0.3)
            
            # Add colorbar
            cbar = self.mean_force_figure.colorbar(scatter, ax=ax)
            cbar.set_label('Flow Speed')
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center')
                   
    def plot_peak_location_channel(self, ax, plot_data, channel, title):
        """Plot peak location for a specific channel (lift or thrust)"""
        ax.set_title(title)
        ax.set_xlabel('Twist')
        ax.set_ylabel('Peak Location (Normalized Phase)')
        
        if len(plot_data['twist']) > 0:
            # Use real peak location data
            if channel == 'thrust':
                peak_locations = plot_data['thrust_peak_location']
            else:  # lift
                peak_locations = plot_data['lift_peak_location']
                
            scatter = ax.scatter(plot_data['twist'], peak_locations, 
                               c=plot_data['flow_speed'], 
                               cmap=self.flow_speed_colormap.currentText(),
                               s=50, alpha=0.7)
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.3)
            
            # Add colorbar
            cbar = self.peak_location_figure.colorbar(scatter, ax=ax)
            cbar.set_label('Flow Speed')
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center')
                   
    def plot_force_vectors(self, ax, plot_data):
        """Plot force vectors with thrust on X-axis and lift on Y-axis"""
        ax.set_title('Force Vectors')
        ax.set_xlabel('Thrust')
        ax.set_ylabel('Lift')
        
        if len(plot_data['twist']) > 0:
            # Use real mean force data
            thrust_values = plot_data['thrust_mean']
            lift_values = plot_data['lift_mean']
            
            # Plot as arrows (from origin to force point)
            for i in range(len(thrust_values)):
                ax.arrow(0, 0, thrust_values[i], lift_values[i], 
                        head_width=0.05, head_length=0.05, fc='blue', ec='blue', alpha=0.6)
            
            # Also plot as scatter for better visibility
            scatter = ax.scatter(thrust_values, lift_values, 
                               c=plot_data['flow_speed'], 
                               cmap=self.flow_speed_colormap.currentText(),
                               s=50, alpha=0.7)
            
            # Add colorbar
            cbar = self.vector_figure.colorbar(scatter, ax=ax)
            cbar.set_label('Flow Speed')
            
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center')
                   
    def update_data_info(self):
        """Update the data information display"""
        if not self.data:
            return
            
        info_text = "Data Summary:\n"
        info_text += f"Total Experiments: {len(self.data['experiments'])}\n"
        info_text += f"Selected Experiments: {len(self.selected_experiments)}\n"
        
        if self.data['experiments']:
            # Get parameter ranges from first experiment
            first_exp = list(self.data['experiments'].values())[0]
            params = first_exp['parameters']
            
            info_text += "\nParameter Ranges:\n"
            for key in params.keys():
                values = [exp['parameters'][key] for exp in self.data['experiments'].values()]
                if isinstance(values[0], (int, float)):
                    info_text += f"  {key}: {min(values):.2f} - {max(values):.2f}\n"
                else:
                    info_text += f"  {key}: {len(set(values))} unique values\n"
            
            info_text += f"\nTime Vector Length: {len(self.data['time_vector'])}\n"
            info_text += f"Evaluation Window: {self.window_start:.2f} - {self.window_end:.2f}\n"
        
        self.data_info_text.setText(info_text)
        
    def export_current_tab_png(self):
        """Export current tab plot as PNG"""
        current_tab = self.tab_widget.currentIndex()
        current_figure = None
        
        if current_tab == 0:  # Traces
            current_figure = self.traces_figure
            tab_name = "traces"
        elif current_tab == 1:  # Mean Force
            current_figure = self.mean_force_figure
            tab_name = "mean_force"
        elif current_tab == 2:  # Peak Location
            current_figure = self.peak_location_figure
            tab_name = "peak_location"
        elif current_tab == 3:  # Vector
            current_figure = self.vector_figure
            tab_name = "vector"
            
        if not current_figure or not current_figure.get_axes():
            QMessageBox.warning(self, "Warning", "No plots to export")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", f"full_stroke_{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG files (*.png)"
        )
        
        if filepath:
            current_figure.savefig(filepath, dpi=300, bbox_inches='tight')
            self.statusBar().showMessage(f"Exported to {filepath}")
            
    def export_current_tab_pdf(self):
        """Export current tab plot as PDF"""
        current_tab = self.tab_widget.currentIndex()
        current_figure = None
        
        if current_tab == 0:  # Traces
            current_figure = self.traces_figure
            tab_name = "traces"
        elif current_tab == 1:  # Mean Force
            current_figure = self.mean_force_figure
            tab_name = "mean_force"
        elif current_tab == 2:  # Peak Location
            current_figure = self.peak_location_figure
            tab_name = "peak_location"
        elif current_tab == 3:  # Vector
            current_figure = self.vector_figure
            tab_name = "vector"
            
        if not current_figure or not current_figure.get_axes():
            QMessageBox.warning(self, "Warning", "No plots to export")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"full_stroke_{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF files (*.pdf)"
        )
        
        if filepath:
            current_figure.savefig(filepath, bbox_inches='tight')
            self.statusBar().showMessage(f"Exported to {filepath}")
            
    def export_csv(self):
        """Export current plot data as CSV"""
        if not self.data or not self.selected_experiments:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"full_stroke_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV files (*.csv)"
        )
        
        if filepath:
            # Create a DataFrame with the processed data
            plot_data = self.process_data_for_plotting()
            df = pd.DataFrame(plot_data)
            df.to_csv(filepath, index=False)
            self.statusBar().showMessage(f"Exported to {filepath}")
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Combined Full-Stroke Analysis GUI\n\n"
                         "Interactive tool for visualizing full-stroke experimental data\n"
                         "with trial traces plotting and overview metrics analysis.")
        
    def closeEvent(self, event):
        """Handle application close event"""
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Combined Full-Stroke Analysis GUI")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = CombinedFullStrokeGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
