#!/usr/bin/env python3
"""
Paddle-Stroke Overview Metrics GUI

Interactive GUI for visualizing paddle-stroke experimental data with the following encodings:
- X-axis: twist angle
- Columns: sweep angle  
- Color: flow speed
- Line style: stroke period

Metrics per panel family:
- Trial-mean thrust, trial-mean lift, resultant magnitude
- Peak thrust and peak lift with peak timing markers (normalized trial time)
- Trial-mean resultant angle

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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QComboBox, QCheckBox,
                             QFileDialog, QMessageBox, QProgressBar, QGroupBox,
                             QGridLayout, QSpinBox, QDoubleSpinBox, QTabWidget,
                             QTextEdit, QSplitter, QSlider, QLineEdit, QListWidget,
                             QListWidgetItem, QScrollArea, QFrame, QRadioButton, 
                             QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import json
from datetime import datetime

class DataLoader(QThread):
    """Thread for loading HDF5 data without blocking the GUI"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
    
    def run(self):
        try:
            self.progress.emit(10)
            with h5py.File(self.filepath, 'r') as f:
                # Load experiment data
                self.progress.emit(30)
                trial_data = {}
                for exp_key in f.keys():
                    if exp_key.startswith('exp_'):
                        trial_data[exp_key] = {}
                        exp_group = f[exp_key]
                        for data_key in exp_group.keys():
                            if data_key == 'parameters':
                                # Parameters are stored as attributes
                                trial_data[exp_key][data_key] = {}
                                param_group = exp_group[data_key]
                                for attr_name in param_group.attrs:
                                    trial_data[exp_key][data_key][attr_name] = param_group.attrs[attr_name]
                            elif data_key in ['thrust', 'lift']:
                                # Force data groups
                                trial_data[exp_key][data_key] = {}
                                force_group = exp_group[data_key]
                                for force_key in force_group.keys():
                                    trial_data[exp_key][data_key][force_key] = np.array(force_group[force_key])
                            else:
                                # Other data (time_vector, timing_info, etc.)
                                trial_data[exp_key][data_key] = np.array(exp_group[data_key])
                
                self.progress.emit(60)
                # Load metadata
                metadata = {}
                if 'metadata' in f:
                    meta_group = f['metadata']
                    for key in meta_group.keys():
                        metadata[key] = np.array(meta_group[key])
                
                self.progress.emit(90)
                # Load experiment parameters
                experiment_params = {}
                if 'experiment_parameters' in f:
                    exp_group = f['experiment_parameters']
                    for key in exp_group.keys():
                        experiment_params[key] = np.array(exp_group[key])
                
                self.progress.emit(100)
                self.finished.emit({
                    'trial_data': trial_data,
                    'metadata': metadata,
                    'experiment_parameters': experiment_params
                })
                
        except Exception as e:
            self.error.emit(str(e))

class PaddleStrokeOverviewGUI(QMainWindow):
    """Main GUI window for Full-Stroke Overview Metrics"""
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.current_plot_data = None
        self.trial_traces_file = None
        self.param_index = {            # unique values (normalized)
            'period': set(),
            'flow': set(),
            'sweep': set(),
            'twist': set(),
        }
        self.dataset_rows = []
        
        # Baseline experimental parameters
        self.baseline_params = {
            'flow': 0.1,
            'period': 2.25,
            'sweep': 80.0,
            'twist': 0.0
        }
        self.baseline_color = '#FF0000'  # Red
        self.baseline_line_style = '--'
        
        # Custom twist color mapping (default color scheme)
        self.custom_twist_colors = {
            0: '#1f77b4',   # blue
            15: '#ff7f0e',  # orange
            30: '#2ca02c',  # green
            45: '#d62728',  # red
            60: '#9467bd',  # purple
            75: '#8c564b',  # brown
            90: '#e377c2'   # pink
        }
        
        # Full Stroke normalization windows (used for normalizing to [0,1])
        # These are the reference windows from Full Stroke analysis
        self.full_stroke_windows = {
            1.75: {'start': 0.70, 'end': 1.75},  # 1.75s period: 1.05s duration
            2.25: {'start': 0.90, 'end': 2.25}   # 2.25s period: 1.35s duration
        }
        
        # Paddle stroke trimming windows (in paddle stroke's own time coordinates)
        # These define where valid paddle stroke data exists (trimming artifacts)
        # Paddle stroke data starts at 0 in its own coordinate system
        self.paddle_stroke_windows = {
            1.75: {'start': 0.0, 'end': 0.8},  # Default: use first 0.8s, user can adjust
            2.25: {'start': 0.0, 'end': 0.8}   # Default: use first 0.8s, user can adjust
        }
        
        self.init_ui()
        # Ensure data loads at startup
        self.auto_load_data()

    def _param_map(self, params):
        """Normalize raw HDF5 parameters to canonical terms for Paddle stroke data."""
        flow   = params.get('flow', params.get('flow_speed', 0.0))
        period = params.get('period', params.get('stroke_period', 0.0))
        sweep_raw  = params.get('sweep', params.get('yaw_amplitude', 0.0))
        twist_raw  = params.get('twist', params.get('roll_angle', 0.0))
        # No phase overlap for Paddle stroke data
        sweep = float(abs(sweep_raw))
        twist = float(abs(twist_raw))
        return {
            'flow': float(flow),
            'stroke_period': float(period),
            'sweep': sweep,
            'twist': twist
        }
        
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Paddle-Stroke Overview Metrics GUI")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create plot panel (full width)
        self.create_tabbed_plot_panel(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready - Auto-loading mean traces data...")
        
    def auto_load_data(self):
        """Automatically load the Paddle stroke processed data"""
        # Look for the paddle stroke processed file
        possible_paths = [
            "data/processed/Paddle/PaddleStroke_Processed_2025-01-27.h5",
            "PaddleStroke_Processed_2025-01-27.h5"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.trial_traces_file = path
                self.load_trial_traces_data()
                return
                
        # If not found, show error
        QMessageBox.warning(self, "Data Not Found", 
                           "Could not find PaddleStroke_Processed_2025-01-27.h5 file.\n"
                           "Please run the Paddle stroke trial processing script first.")
        self.statusBar().showMessage("Data file not found")
        
    def load_trial_traces_data(self):
        """Load the Paddle stroke processed data from HDF5 file"""
        try:
            with h5py.File(self.trial_traces_file, 'r') as f:
                self.data = {
                    'experiments': {}
                }
                
                # Load all groups (Paddle stroke structure: group_000, group_001, etc.)
                for group_key in f.keys():
                    if group_key.startswith('group_'):
                        group = f[group_key]
                        
                        # Load parameters (stored as attributes)
                        params = {
                            'period': group.attrs['period'],
                            'sweep': group.attrs['sweep'],  # Paddle uses 'sweep' instead of 'yaw_amplitude'
                            'twist': group.attrs['twist'],  # Paddle uses 'twist' instead of 'roll_angle'
                            'flow': group.attrs['flow']     # Paddle uses 'flow' instead of 'flow_speed'
                        }
                        
                        # Load mean traces
                        thrust_mean = np.array(group['mean_thrust'])
                        lift_mean = np.array(group['mean_lift'])
                        
                        # Create time vector for this specific experiment (assuming 500 Hz sampling rate)
                        trial_length = len(thrust_mean)
                        time_vector = np.arange(trial_length) / 500.0
                        
                        # Store experiment data
                        self.data['experiments'][group_key] = {
                            'parameters': params,
                            'thrust_mean': thrust_mean,
                            'lift_mean': lift_mean,
                            'time_vector': time_vector
                        }
                
                # Populate parameter index for dataset selectors
                self.populate_parameter_index()
                
                # Seed defaults for dataset selectors
                self._seed_defaults()
                
                # Ensure tab controls reflect the now-loaded data
                try:
                    self.update_parameter_controls()
                except Exception:
                    pass
                try:
                    self.update_mean_force_parameter_controls()
                except Exception:
                    pass

                # Force UI refresh
                self.update()
                
                # Update UI
                self.plot_button.setEnabled(True)
                # Overview buttons removed - functionality moved to individual tabs
                
                # Populate normalization tab dropdowns
                try:
                    self.populate_paddle_norm_parameters()
                except Exception:
                    pass
                
                # Update data info
                self.update_data_info()
                
                self.statusBar().showMessage(f"Loaded {len(self.data['experiments'])} experiments from mean traces")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load trial traces data:\n{str(e)}")
            self.statusBar().showMessage("Failed to load data")
            
    def populate_parameter_index(self):
        """Populate parameter index using normalized parameters for Power stroke data."""
        # Clear existing parameter index (normalized keys)
        self.param_index = {
            'period': set(),
            'flow': set(),
            'sweep': set(),
            'twist': set(),
        }
        
        # Extract normalized parameters from loaded data
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data['parameters'])
            self.param_index['period'].add(m['stroke_period'])
            self.param_index['flow'].add(m['flow'])
            self.param_index['sweep'].add(m['sweep'])
            self.param_index['twist'].add(m['twist'])
        
        # Convert sets to sorted lists
        for key in self.param_index:
            self.param_index[key] = sorted(list(self.param_index[key]))

        # Build a consistent twist color palette used across tabs
        try:
            self.twist_color_map = self._build_twist_color_map()
        except Exception:
            self.twist_color_map = {}

        # Populate master combos when available
        try:
            if hasattr(self, 'master_flow'):
                self.master_flow.clear(); self.master_flow.addItems([str(v) for v in self.param_index.get('flow', [])])
            if hasattr(self, 'master_period'):
                per = [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) for v in self.param_index.get('period', [])]
                self.master_period.clear(); self.master_period.addItems(per)
            if hasattr(self, 'master_yaw'):
                self.master_yaw.clear(); self.master_yaw.addItems([str(int(v)) for v in self.param_index.get('sweep', [])])
            if hasattr(self, 'master_roll'):
                self.master_roll.clear(); self.master_roll.addItems([str(int(v)) for v in self.param_index.get('twist', [])])
            # No phase overlap for Power stroke data
        except Exception:
            pass

    def _build_twist_color_map(self):
        """Create a categorical color map for twist values (consistent across app)."""
        twists = self.param_index.get('twist', [])
        
        # Use custom twist colors if available, otherwise fall back to palette
        color_map = {}
        for tw in twists:
            if tw in self.custom_twist_colors:
                color_map[tw] = self.custom_twist_colors[tw]
            else:
                # Fall back to palette for twists not in custom colors
                choice = getattr(self, 'overview_palette_choice', 'Default')
                if choice == 'Custom' and hasattr(self, 'overview_custom_colors') and self.overview_custom_colors:
                    palette = list(self.overview_custom_colors)
                elif choice == 'CB friendly':
                    palette = ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#999999']
                else:
                    palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                
                # Find index of this twist in the sorted list
                sorted_twists = sorted(twists)
                idx = sorted_twists.index(tw)
                color_map[tw] = palette[idx % len(palette)]
        
        return color_map

    def create_overview_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Palette controls
        palette_group = QGroupBox("Overview Color Palette (Mean/Peak/Vector)")
        palette_layout = QGridLayout(palette_group)
        palette_layout.addWidget(QLabel("Palette"), 0, 0)
        self.overview_palette_select = QComboBox()
        self.overview_palette_select.addItems(['Default', 'CB friendly', 'Custom'])
        self.overview_palette_choice = 'Default'
        self.overview_palette_select.currentTextChanged.connect(self._on_palette_selection_changed)
        palette_layout.addWidget(self.overview_palette_select, 0, 1)
        # Custom colors (10 hex boxes)
        self.overview_custom_color_edits = []
        for i in range(10):
            edit = QLineEdit()
            edit.setPlaceholderText('#RRGGBB')
            edit.setMaximumWidth(90)
            edit.setEnabled(False)
            self.overview_custom_color_edits.append(edit)
            r = 1 + i // 5
            c = i % 5
            palette_layout.addWidget(edit, r, c)
        apply_btn = QPushButton("Apply Palette")
        apply_btn.clicked.connect(self._apply_overview_palette)
        palette_layout.addWidget(apply_btn, 3, 5)
        layout.addWidget(palette_group)

        # Baseline Experimental Parameters
        baseline_group = QGroupBox("Baseline Experimental Parameters")
        baseline_layout = QGridLayout(baseline_group)
        
        # Flow parameter
        baseline_layout.addWidget(QLabel("Flow:"), 0, 0)
        self.baseline_flow = QDoubleSpinBox()
        self.baseline_flow.setRange(0.0, 2.0)
        self.baseline_flow.setValue(0.1)
        self.baseline_flow.setDecimals(2)
        self.baseline_flow.setSingleStep(0.1)
        self.baseline_flow.valueChanged.connect(self._update_baseline_params)
        baseline_layout.addWidget(self.baseline_flow, 0, 1)
        
        # Period parameter
        baseline_layout.addWidget(QLabel("Period:"), 0, 2)
        self.baseline_period = QDoubleSpinBox()
        self.baseline_period.setRange(1.0, 3.0)
        self.baseline_period.setValue(2.25)
        self.baseline_period.setDecimals(2)
        self.baseline_period.setSingleStep(0.25)
        self.baseline_period.valueChanged.connect(self._update_baseline_params)
        baseline_layout.addWidget(self.baseline_period, 0, 3)
        
        # Sweep parameter
        baseline_layout.addWidget(QLabel("Sweep:"), 1, 0)
        self.baseline_sweep = QDoubleSpinBox()
        self.baseline_sweep.setRange(0.0, 90.0)
        self.baseline_sweep.setValue(80.0)
        self.baseline_sweep.setDecimals(0)
        self.baseline_sweep.setSingleStep(15.0)
        self.baseline_sweep.valueChanged.connect(self._update_baseline_params)
        baseline_layout.addWidget(self.baseline_sweep, 1, 1)
        
        # Twist parameter
        baseline_layout.addWidget(QLabel("Twist:"), 1, 2)
        self.baseline_twist = QDoubleSpinBox()
        self.baseline_twist.setRange(0.0, 90.0)
        self.baseline_twist.setValue(0.0)
        self.baseline_twist.setDecimals(0)
        self.baseline_twist.setSingleStep(15.0)
        self.baseline_twist.valueChanged.connect(self._update_baseline_params)
        baseline_layout.addWidget(self.baseline_twist, 1, 3)
        
        # Baseline color
        baseline_layout.addWidget(QLabel("Color:"), 2, 0)
        self.baseline_color_edit = QLineEdit()
        self.baseline_color_edit.setText("#FF0000")
        self.baseline_color_edit.setPlaceholderText("#RRGGBB")
        self.baseline_color_edit.textChanged.connect(self._update_baseline_color)
        baseline_layout.addWidget(self.baseline_color_edit, 2, 1)
        
        # Baseline line style
        baseline_layout.addWidget(QLabel("Line Style:"), 2, 2)
        self.baseline_linestyle_combo = QComboBox()
        self.baseline_linestyle_combo.addItems(['-', '--', '-.', ':', 'None'])
        self.baseline_linestyle_combo.setCurrentText('--')
        self.baseline_linestyle_combo.currentTextChanged.connect(self._update_baseline_linestyle)
        baseline_layout.addWidget(self.baseline_linestyle_combo, 2, 3)
        
        # Info label
        info_label = QLabel("Baseline experiments will be highlighted with the specified color and line style.")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        baseline_layout.addWidget(info_label, 3, 0, 1, 4)
        
        # Update baseline settings button
        update_baseline_btn = QPushButton("Update Baseline Settings")
        update_baseline_btn.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        update_baseline_btn.clicked.connect(self._update_baseline_settings)
        baseline_layout.addWidget(update_baseline_btn, 4, 0, 1, 4)
        
        layout.addWidget(baseline_group)

        # Twist Color Mapping (Override Palette)
        twist_color_group = QGroupBox("Twist Color Mapping (Override Palette)")
        twist_color_layout = QGridLayout(twist_color_group)
        
        twist_angles = [0, 15, 30, 45, 60, 75, 90]
        self.twist_color_edits = {}
        
        for i, angle in enumerate(twist_angles):
            row = i // 4
            col = (i % 4) * 2
            
            twist_color_layout.addWidget(QLabel(f"{angle}°:"), row, col)
            edit = QLineEdit()
            edit.setText(self.custom_twist_colors[angle])
            edit.setPlaceholderText('#RRGGBB')
            edit.setMaximumWidth(90)
            edit.textChanged.connect(lambda text, a=angle: self._update_twist_color(a, text))
            self.twist_color_edits[angle] = edit
            twist_color_layout.addWidget(edit, row, col + 1)
        
        # Apply and Reset buttons
        apply_twist_btn = QPushButton("Apply Twist Colors")
        apply_twist_btn.clicked.connect(self._apply_twist_colors)
        twist_color_layout.addWidget(apply_twist_btn, 2, 6)
        
        reset_twist_btn = QPushButton("Reset to Palette Defaults")
        reset_twist_btn.clicked.connect(self._reset_twist_colors)
        twist_color_layout.addWidget(reset_twist_btn, 2, 7)
        
        layout.addWidget(twist_color_group)

        # Publish all overview plots
        puball_group = QGroupBox("Publish All Overview Plots")
        puball_layout = QHBoxLayout(puball_group)
        self.publish_all_button = QPushButton("Publish All (Mean/Peak/Vector)")
        self.publish_all_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        self.publish_all_button.clicked.connect(self.publish_all_overview_plots)
        puball_layout.addWidget(self.publish_all_button)
        puball_layout.addStretch()
        layout.addWidget(puball_group)

        self.tab_widget.addTab(tab, "Overview Settings")

    def _on_palette_selection_changed(self, text):
        self.overview_palette_choice = text
        enable = (text == 'Custom')
        for e in getattr(self, 'overview_custom_color_edits', []):
            e.setEnabled(enable)

    def _apply_overview_palette(self):
        if getattr(self, 'overview_palette_choice', 'Default') == 'Custom':
            colors = []
            for e in getattr(self, 'overview_custom_color_edits', []):
                c = e.text().strip()
                if c:
                    if not c.startswith('#'):
                        c = '#' + c
            colors.append(c)
            if not colors:
                colors = ['#1f77b4']
            self.overview_custom_colors = colors
        # Rebuild twist color map
        try:
            self.twist_color_map = self._build_twist_color_map()
        except Exception:
            pass
        # Redraw existing overview tabs if present
        try:
            if hasattr(self, 'mean_force_canvas'):
                self.plot_mean_force()
        except Exception:
            pass
        try:
            if hasattr(self, 'peak_location_canvas'):
                self.plot_peak_location()
        except Exception:
            pass
        try:
            if hasattr(self, 'vector_canvas'):
                self.plot_vector()
        except Exception:
            pass

    def _update_baseline_params(self):
        """Update baseline parameters from UI controls"""
        self.baseline_params = {
            'flow': self.baseline_flow.value(),
            'period': self.baseline_period.value(),
            'sweep': self.baseline_sweep.value(),
            'twist': self.baseline_twist.value()
        }
        
    def _update_baseline_color(self, text):
        """Update baseline color"""
        self.baseline_color = text.strip()
        
    def _update_baseline_linestyle(self, text):
        """Update baseline line style"""
        self.baseline_line_style = text
        
    def _update_baseline_settings(self):
        """Update baseline settings and refresh all plots"""
        # Update baseline parameters from UI controls
        self._update_baseline_params()
        self._update_baseline_color(self.baseline_color_edit.text())
        self._update_baseline_linestyle(self.baseline_linestyle_combo.currentText())
        
        # Refresh all overview plots if they exist
        try:
            if hasattr(self, 'mean_force_canvas') and self.mean_force_canvas:
                self.plot_mean_force()
        except Exception as e:
            print(f"Error refreshing mean force plot: {e}")
            
        try:
            if hasattr(self, 'peak_location_canvas') and self.peak_location_canvas:
                self.plot_peak_location()
        except Exception as e:
            print(f"Error refreshing peak location plot: {e}")
            
        try:
            if hasattr(self, 'vector_canvas') and self.vector_canvas:
                self.plot_vector()
        except Exception as e:
            print(f"Error refreshing vector plot: {e}")
        
        # Also refresh trial traces if they exist
        try:
            if hasattr(self, 'trial_trace_canvas') and self.trial_trace_canvas:
                self.plot_trial_trace()
        except Exception as e:
            print(f"Error refreshing trial trace plot: {e}")
            
        print(f"Baseline settings updated: Flow={self.baseline_params['flow']}, "
              f"Period={self.baseline_params['period']}, Sweep={self.baseline_params['sweep']}, "
              f"Twist={self.baseline_params['twist']}, Color={self.baseline_color}, "
              f"LineStyle={self.baseline_line_style}")
        
    def _update_twist_color(self, twist, color):
        """Update twist color (no immediate action, just store)"""
        self.custom_twist_colors[twist] = color.strip()
        
    def _apply_twist_colors(self):
        """Apply custom twist colors and rebuild color map"""
        # Update custom colors from UI
        for angle, edit in self.twist_color_edits.items():
            color = edit.text().strip()
            if color:
                if not color.startswith('#'):
                    color = '#' + color
                self.custom_twist_colors[angle] = color
        
        # Rebuild twist color map
        try:
            self.twist_color_map = self._build_twist_color_map()
        except Exception:
            pass
        
        # Redraw existing plots
        try:
            if hasattr(self, 'mean_force_canvas'):
                self.plot_mean_force()
        except Exception:
            pass
        try:
            if hasattr(self, 'peak_location_canvas'):
                self.plot_peak_location()
        except Exception:
            pass
        try:
            if hasattr(self, 'vector_canvas'):
                self.plot_vector()
        except Exception:
            pass
        
    def _reset_twist_colors(self):
        """Reset twist colors to palette defaults"""
        # Reset to default color scheme
        self.custom_twist_colors = {
            0: '#1f77b4',   # blue
            15: '#ff7f0e',  # orange
            30: '#2ca02c',  # green
            45: '#d62728',  # red
            60: '#9467bd',  # purple
            75: '#8c564b',  # brown
            90: '#e377c2'   # pink
        }
        
        # Update UI
        for angle, edit in self.twist_color_edits.items():
            edit.setText(self.custom_twist_colors[angle])
        
        # Rebuild color map and redraw
        self._apply_twist_colors()
        
    def _is_baseline_experiment(self, flow, period, sweep, twist):
        """Check if experiment parameters match baseline (with tolerance)"""
        return (abs(flow - self.baseline_params['flow']) < 0.01 and
                abs(period - self.baseline_params['period']) < 0.1 and
                abs(sweep - self.baseline_params['sweep']) < 1.0 and
                abs(twist - self.baseline_params['twist']) < 1.0)

    def publish_all_overview_plots(self):
        outdir = os.path.join(os.getcwd(), f"Paddle_Stroke_Figures_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        try:
            os.makedirs(outdir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create output directory: {e}")
            return

        # Save current selections to restore later
        try:
            mean_sel = 0 if self.mean_force_flow_radio.isChecked() else 1 if self.mean_force_sweep_radio.isChecked() else 2
            mean_channel = self.mean_force_channel.currentText()
        except Exception:
            mean_sel = None; mean_channel = None
        try:
            peak_sel = 0 if self.peak_flow_radio.isChecked() else 1 if self.peak_sweep_radio.isChecked() else 2
            peak_channel = self.peak_location_channel.currentText()
        except Exception:
            peak_sel = None; peak_channel = None
        try:
            vec_sel = 0 if self.vec_flow_radio.isChecked() else 1 if self.vec_sweep_radio.isChecked() else 2
        except Exception:
            vec_sel = None

        variable_types = [('Flow', 0), ('Sweep', 1)]
        channels = [('Thrust', 'thrust'), ('Lift', 'lift')]

        # Mean plots
        for vname, vidx in variable_types:
            try:
                [self.mean_force_flow_radio, self.mean_force_sweep_radio][vidx].setChecked(True)
                self.update_mean_force_parameter_controls()
                for cname, _ in channels:
                    self.mean_force_channel.setCurrentText(cname)
                    self.plot_mean_force()
                    wpx = int(float(self.mf_pub_w.text())); hpx = int(float(self.mf_pub_h.text()))
                    self.mean_force_figure.set_size_inches(wpx/100.0, hpx/100.0)
                    fname = os.path.join(outdir, f"Mean_{cname}_{vname}.png")
                    self.mean_force_figure.savefig(fname, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            except Exception:
                continue

        # Peak plots
        for vname, vidx in variable_types:
            try:
                [self.peak_flow_radio, self.peak_sweep_radio][vidx].setChecked(True)
                self.update_peak_parameter_controls()
                for cname, _ in channels:
                    self.peak_location_channel.setCurrentText(cname)
                    self.plot_peak_location()
                    wpx = int(float(self.pk_pub_w.text())); hpx = int(float(self.pk_pub_h.text()))
                    self.peak_location_figure.set_size_inches(wpx/100.0, hpx/100.0)
                    fname = os.path.join(outdir, f"Peak_{cname}_{vname}.png")
                    self.peak_location_figure.savefig(fname, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            except Exception:
                continue

        # Vector plots
        for vname, vidx in variable_types:
            try:
                [self.vec_flow_radio, self.vec_sweep_radio][vidx].setChecked(True)
                self.update_vec_parameter_controls()
                self.plot_vector()
                wpx = int(float(self.vec_pub_w.text())); hpx = int(float(self.vec_pub_h.text()))
                self.vector_figure.set_size_inches(wpx/100.0, hpx/100.0)
                fname = os.path.join(outdir, f"Vector_{vname}.png")
                self.vector_figure.savefig(fname, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            except Exception:
                continue

        # Restore selections
        try:
            if mean_sel is not None:
                [self.mean_force_flow_radio, self.mean_force_sweep_radio, self.mean_force_overlap_radio][mean_sel].setChecked(True)
                if mean_channel:
                    self.mean_force_channel.setCurrentText(mean_channel)
        except Exception:
            pass
        try:
            if peak_sel is not None:
                [self.peak_flow_radio, self.peak_sweep_radio, self.peak_overlap_radio][peak_sel].setChecked(True)
                if peak_channel:
                    self.peak_location_channel.setCurrentText(peak_channel)
        except Exception:
            pass
        try:
            if vec_sel is not None:
                [self.vec_flow_radio, self.vec_sweep_radio, self.vec_overlap_radio][vec_sel].setChecked(True)
        except Exception:
            pass
        self.statusBar().showMessage(f"Published overview plots to {outdir}")

    def _normalize_time_vector(self, time_vector: np.ndarray, period: float) -> np.ndarray:
        """
        Normalize absolute time to [0, 1] using FULL STROKE windows.
        This ensures all GUIs use the same normalized scale.
        
        Args:
            time_vector: Absolute time values in seconds
            period: Stroke period (1.75 or 2.25)
            
        Returns:
            Normalized time in [0, 1] range based on full stroke window
        """
        t = np.asarray(time_vector, dtype=float)
        
        # Get the FULL STROKE window for this period
        if abs(period - 1.75) < 0.1:
            window = self.full_stroke_windows[1.75]
        elif abs(period - 2.25) < 0.1:
            window = self.full_stroke_windows[2.25]
        else:
            # Fallback: use closest period window
            if period < 2.0:
                window = self.full_stroke_windows[1.75]
            else:
                window = self.full_stroke_windows[2.25]
        
        start_time = window['start']
        end_time = window['end']
        duration = end_time - start_time
        
        # Normalize: map full stroke [start_time, end_time] to [0, 1]
        if duration > 0:
            t_norm = (t - start_time) / duration
        else:
            t_norm = t * 0.0  # Return zeros if duration is invalid
            
        return t_norm
    
    def _get_paddle_stroke_mask(self, time_absolute: np.ndarray, period: float) -> np.ndarray:
        """
        Get mask for paddle stroke portion using absolute time values from paddle stroke data.
        
        Args:
            time_absolute: Absolute time values in seconds (from paddle stroke data)
            period: Stroke period (1.75 or 2.25)
            
        Returns:
            Boolean mask for valid paddle stroke region (trimming artifacts)
        """
        # Get paddle stroke trimming window
        if abs(period - 1.75) < 0.1:
            paddle_window = self.paddle_stroke_windows[1.75]
        elif abs(period - 2.25) < 0.1:
            paddle_window = self.paddle_stroke_windows[2.25]
        else:
            if period < 2.0:
                paddle_window = self.paddle_stroke_windows[1.75]
            else:
                paddle_window = self.paddle_stroke_windows[2.25]
        
        # Create mask for valid paddle stroke region (trimming artifacts at start/end)
        mask = (time_absolute >= paddle_window['start']) & (time_absolute <= paddle_window['end'])
        return mask
            
    def _seed_defaults(self):
        """Seed default values for dataset selectors (from original GUI)"""
        if not self.param_index:
            return
            
        # Populate dropdowns with available parameter values (normalized)
        for i, row in enumerate(self.dataset_rows):
            # Flow dropdown
            flow_values = [str(v) for v in sorted(self.param_index.get('flow', []))]
            row['flow'].clear()
            row['flow'].addItems(flow_values)
            
            # Period dropdown
            period_values = [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) for v in sorted(self.param_index.get('period', []))]
            row['period'].clear()
            row['period'].addItems(period_values)
            
            # Sweep dropdown (absolute)
            yaw_values = [str(int(v)) for v in sorted(self.param_index.get('sweep', []))]
            row['yaw'].clear()
            row['yaw'].addItems(yaw_values)
            
            # Twist dropdown (absolute)
            roll_values = [str(int(v)) for v in sorted(self.param_index.get('twist', []))]
            row['roll'].clear()
            row['roll'].addItems(roll_values)
            
            # No phase overlap for Power stroke data
        
        # Default values for seeding per requirements
        default_flow = str(self.param_index['flow'][0]) if self.param_index['flow'] else '0.1'
        default_period = '2.25'
        # Twist values 0:15:90 for rows 0..6, then repeat/clip
        twist_series = [str(int(v)) for v in range(0, 91, 15)]  # 0,15,...,90
        # Sweep fixed to 80 by default
        default_yaw_value = '80'
        
        default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        for i, row in enumerate(self.dataset_rows):
            # Set default selections
            if flow_values:
                row['flow'].setCurrentText(default_flow)
            if period_values:
                row['period'].setCurrentText(default_period)
            if roll_values:
                row['roll'].setCurrentText(twist_series[i] if i < len(twist_series) else twist_series[-1])
            # No phase overlap for Power stroke data
            if yaw_values:
                row['yaw'].setCurrentText(default_yaw_value)
            # Include first 7 by default
            row['include'].setChecked(i < 7)
                
            # Set style defaults
            row['color'].setText(default_colors[i % len(default_colors)])
            row['lw'].setText('2.0')
            row['alpha'].setText('0.2')
            
            # Default legend label
            row['legend_auto'].setChecked(True)
            self._update_row_auto_label(row)
            
    def populate_parameter_filters(self):
        """Populate the parameter filter dropdowns"""
        # Clear existing items
        self.flow_combo.clear()
        self.period_combo.clear()
        self.yaw_combo.clear()
        
        # Add "All" option
        self.flow_combo.addItem("All")
        self.period_combo.addItem("All")
        self.yaw_combo.addItem("All")
        
        # Collect unique parameter values
        flow_values = set()
        period_values = set()
        yaw_values = set()
        
        for exp_data in self.data['experiments'].values():
            params = exp_data['parameters']
            if 'flow_speed' in params:
                flow_values.add(params['flow_speed'])
            if 'stroke_period' in params:
                period_values.add(params['stroke_period'])
            if 'twist' in params:
                yaw_values.add(params['twist'])
        
        # Add sorted values to dropdowns
        for value in sorted(flow_values):
            self.flow_combo.addItem(f"{value:.2f}")
        for value in sorted(period_values):
            self.period_combo.addItem(f"{value:.2f}")
        for value in sorted(yaw_values):
            self.yaw_combo.addItem(f"{value:.2f}")
            
            
        
    # Window finder removed – timeline is fixed to normalized [0,1]
        
    def _build_selector_row(self, parent_layout, idx):
        """Build a dataset selector row (from original GUI)"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(4, 2, 4, 2)
        row_layout.setSpacing(12)
        
        # Include checkbox
        include_var = QCheckBox(f"Include {idx+1}")
        include_var.setChecked(idx == 0)  # First one checked by default
        row_layout.addWidget(include_var)
        
        # Flow selector
        row_layout.addWidget(QLabel("Flow"))
        flow_var = QComboBox()
        flow_var.setMinimumWidth(80)
        # Will be populated after data loading
        row_layout.addWidget(flow_var)
        
        # Period selector
        row_layout.addWidget(QLabel("Period"))
        period_var = QComboBox()
        period_var.setMinimumWidth(80)
        # Will be populated after data loading
        row_layout.addWidget(period_var)
        
        # Sweep selector
        row_layout.addWidget(QLabel("Sweep"))
        yaw_var = QComboBox()
        yaw_var.setMinimumWidth(80)
        # Will be populated after data loading
        row_layout.addWidget(yaw_var)
        
        # Twist selector
        row_layout.addWidget(QLabel("Twist"))
        roll_var = QComboBox()
        roll_var.setMinimumWidth(80)
        # Will be populated after data loading
        row_layout.addWidget(roll_var)
        
        # No phase overlap for Power stroke data
        
        # Color selector
        row_layout.addWidget(QLabel("Color"))
        color_var = QLineEdit()
        default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        color_var.setText(default_colors[idx % len(default_colors)])
        color_var.setMaximumWidth(90)
        row_layout.addWidget(color_var)
        
        # Line width
        row_layout.addWidget(QLabel("LW"))
        lw_var = QLineEdit("2.0")
        lw_var.setMaximumWidth(50)
        row_layout.addWidget(lw_var)
        
        # Variance checkbox
        var_var = QCheckBox("Variance")
        row_layout.addWidget(var_var)
        
        # Alpha
        row_layout.addWidget(QLabel("Alpha"))
        alpha_var = QLineEdit("0.2")
        alpha_var.setMaximumWidth(50)
        row_layout.addWidget(alpha_var)
        
        # Legend checkbox
        legend_on_var = QCheckBox("Legend")
        legend_on_var.setChecked(True)
        row_layout.addWidget(legend_on_var)
        
        # Legend auto checkbox
        legend_auto_var = QCheckBox("Auto")
        legend_auto_var.setChecked(True)
        row_layout.addWidget(legend_auto_var)
        
        # Legend label
        legend_label_var = QLineEdit()
        legend_label_var.setMaximumWidth(150)
        row_layout.addWidget(legend_label_var)
        
        parent_layout.addWidget(row_widget)
        
        row = {
            'include': include_var,
            'flow': flow_var,
            'period': period_var,
            'yaw': yaw_var,
            'roll': roll_var,
            'color': color_var,
            'lw': lw_var,
            'variance': var_var,
            'alpha': alpha_var,
            'legend_on': legend_on_var,
            'legend_auto': legend_auto_var,
            'legend_label': legend_label_var,
        }
        # Wire changes to keep auto legend up to date
        self._wire_row_signals(row)
        return row

    def _compute_row_auto_label(self, row) -> str:
        try:
            flow = row['flow'].currentText().strip()
        except Exception:
            flow = ''
        try:
            period = row['period'].currentText().strip()
        except Exception:
            period = ''
        try:
            yaw = row['yaw'].currentText().strip()
        except Exception:
            yaw = ''
        try:
            roll = row['roll'].currentText().strip()
        except Exception:
            roll = ''
        # No phase overlap for Power stroke data
        parts = [
            f"flow={flow}" if flow != '' else None,
            f"P={period}" if period != '' else None,
            f"sweep={yaw}" if yaw != '' else None,
            f"twist={roll}" if roll != '' else None,
        ]
        return ", ".join([p for p in parts if p])

    def _update_row_auto_label(self, row):
        try:
            if row['legend_auto'].isChecked():
                row['legend_label'].setText(self._compute_row_auto_label(row))
                row['legend_label'].setEnabled(False)
            else:
                row['legend_label'].setEnabled(True)
        except Exception:
            pass

    def _apply_master_to_rows(self, key_name: str):
        # Apply master value to all rows if the corresponding Fixed is checked
        try:
            fixed_attr = {
                'flow': 'master_flow_fixed',
                'period': 'master_period_fixed',
                'yaw': 'master_yaw_fixed',
                'roll': 'master_roll_fixed',
            }[key_name]
            combo_attr = {
                'flow': 'master_flow',
                'period': 'master_period',
                'yaw': 'master_yaw',
                'roll': 'master_roll',
            }[key_name]
        except KeyError:
            return
        fixed_cb = getattr(self, fixed_attr, None)
        master_combo = getattr(self, combo_attr, None)
        if fixed_cb is None or master_combo is None:
            return
        if not fixed_cb.isChecked():
            return
        val = master_combo.currentText()
        for row in self.dataset_rows:
            try:
                row[key_name].setCurrentText(val)
                # keep legend auto label in sync
                self._update_row_auto_label(row)
            except Exception:
                continue

    def _wire_row_signals(self, row):
        # When any selector changes and auto is on, update label
        for key in ['flow', 'period', 'yaw', 'roll']:
            try:
                row[key].currentIndexChanged.connect(lambda _=None, r=row: self._update_row_auto_label(r))
            except Exception:
                pass
        try:
            row['legend_auto'].toggled.connect(lambda _=None, r=row: self._update_row_auto_label(r))
        except Exception:
            pass
        
        
    def create_tabbed_plot_panel(self, parent):
        """Create the tabbed plot panel with matplotlib canvases"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        parent.addWidget(self.tab_widget)
        
        # Create tabs (normalization first!)
        self.create_paddle_normalization_tab()
        self.create_overview_settings_tab()
        self.create_traces_tab()
        self.create_mean_overview_tab()
        self.create_mean_force_tab()
        self.create_peak_location_tab()
        self.create_vector_tab()
        
    def create_paddle_normalization_tab(self):
        """Create normalization tab for Paddle Stroke boundary selection"""
        norm_widget = QWidget()
        norm_layout = QHBoxLayout(norm_widget)
        
        # Left panel: Settings
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_panel.setMaximumWidth(500)
        
        title_label = QLabel("Paddle Stroke Normalization")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        left_layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Define Paddle Stroke boundaries (absolute time in seconds).\n"
            "Plot traces to visualize and trim artifacts at start/end."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; margin-bottom: 5px; font-size: 10px;")
        left_layout.addWidget(desc_label)
        
        # Window settings
        settings_frame = QGroupBox("Paddle Stroke Time Windows")
        settings_layout = QVBoxLayout(settings_frame)
        
        # Period 1.75s
        period_175_frame = QGroupBox("Period 1.75s")
        period_175_layout = QGridLayout(period_175_frame)
        period_175_layout.addWidget(QLabel("Start (s):"), 0, 0)
        self.paddle_175_start = QDoubleSpinBox()
        self.paddle_175_start.setRange(0.0, 10.0)
        self.paddle_175_start.setSingleStep(0.05)
        self.paddle_175_start.setDecimals(2)
        self.paddle_175_start.setValue(self.paddle_stroke_windows[1.75]['start'])
        period_175_layout.addWidget(self.paddle_175_start, 0, 1)
        
        period_175_layout.addWidget(QLabel("End (s):"), 0, 2)
        self.paddle_175_end = QDoubleSpinBox()
        self.paddle_175_end.setRange(0.0, 10.0)
        self.paddle_175_end.setSingleStep(0.05)
        self.paddle_175_end.setDecimals(2)
        self.paddle_175_end.setValue(self.paddle_stroke_windows[1.75]['end'])
        period_175_layout.addWidget(self.paddle_175_end, 0, 3)
        
        period_175_layout.addWidget(QLabel("Duration:"), 0, 4)
        self.paddle_175_duration = QLabel()
        self.paddle_175_duration.setStyleSheet("font-weight: bold; color: #0078d4;")
        period_175_layout.addWidget(self.paddle_175_duration, 0, 5)
        settings_layout.addWidget(period_175_frame)
        
        # Period 2.25s
        period_225_frame = QGroupBox("Period 2.25s")
        period_225_layout = QGridLayout(period_225_frame)
        period_225_layout.addWidget(QLabel("Start (s):"), 0, 0)
        self.paddle_225_start = QDoubleSpinBox()
        self.paddle_225_start.setRange(0.0, 10.0)
        self.paddle_225_start.setSingleStep(0.05)
        self.paddle_225_start.setDecimals(2)
        self.paddle_225_start.setValue(self.paddle_stroke_windows[2.25]['start'])
        period_225_layout.addWidget(self.paddle_225_start, 0, 1)
        
        period_225_layout.addWidget(QLabel("End (s):"), 0, 2)
        self.paddle_225_end = QDoubleSpinBox()
        self.paddle_225_end.setRange(0.0, 10.0)
        self.paddle_225_end.setSingleStep(0.05)
        self.paddle_225_end.setDecimals(2)
        self.paddle_225_end.setValue(self.paddle_stroke_windows[2.25]['end'])
        period_225_layout.addWidget(self.paddle_225_end, 0, 3)
        
        period_225_layout.addWidget(QLabel("Duration:"), 0, 4)
        self.paddle_225_duration = QLabel()
        self.paddle_225_duration.setStyleSheet("font-weight: bold; color: #0078d4;")
        period_225_layout.addWidget(self.paddle_225_duration, 0, 5)
        settings_layout.addWidget(period_225_frame)
        
        left_layout.addWidget(settings_frame)
        
        # Trace selection
        trace_sel_frame = QGroupBox("Trace Selection")
        trace_sel_layout = QVBoxLayout(trace_sel_frame)
        
        chan_layout = QHBoxLayout()
        chan_layout.addWidget(QLabel("Channel:"))
        self.paddle_norm_channel = QComboBox()
        self.paddle_norm_channel.addItems(["thrust", "lift"])
        chan_layout.addWidget(self.paddle_norm_channel)
        chan_layout.addStretch()
        trace_sel_layout.addLayout(chan_layout)
        
        param_layout = QGridLayout()
        param_layout.addWidget(QLabel("Flow:"), 0, 0)
        self.paddle_norm_flow = QComboBox()
        param_layout.addWidget(self.paddle_norm_flow, 0, 1)
        
        param_layout.addWidget(QLabel("Period:"), 1, 0)
        self.paddle_norm_period = QComboBox()
        param_layout.addWidget(self.paddle_norm_period, 1, 1)
        
        param_layout.addWidget(QLabel("Sweep:"), 2, 0)
        self.paddle_norm_sweep = QComboBox()
        param_layout.addWidget(self.paddle_norm_sweep, 2, 1)
        
        param_layout.addWidget(QLabel("Twist:"), 3, 0)
        self.paddle_norm_twist = QComboBox()
        param_layout.addWidget(self.paddle_norm_twist, 3, 1)
        trace_sel_layout.addLayout(param_layout)
        
        plot_button = QPushButton("Plot Traces (Absolute Time)")
        plot_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px; }")
        plot_button.clicked.connect(self.plot_paddle_normalization_traces)
        trace_sel_layout.addWidget(plot_button)
        
        left_layout.addWidget(trace_sel_frame)
        
        # Apply button
        apply_button = QPushButton("Apply Settings & Refresh Plot")
        apply_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; padding: 8px; }")
        apply_button.clicked.connect(self.apply_paddle_normalization)
        left_layout.addWidget(apply_button)
        
        left_layout.addStretch()
        
        # Right panel: Plot
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        plot_title = QLabel("Paddle Stroke Trace Visualization (Absolute Time)")
        plot_title.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(plot_title)
        
        self.paddle_norm_figure = Figure(figsize=(10, 6), dpi=100)
        self.paddle_norm_ax = self.paddle_norm_figure.add_subplot(111)
        self.paddle_norm_ax.grid(True, alpha=0.3)
        self.paddle_norm_ax.set_xlabel('Absolute Time (seconds)', fontsize=11)
        self.paddle_norm_ax.set_ylabel('Force (scaled)', fontsize=11)
        self.paddle_norm_canvas = FigureCanvas(self.paddle_norm_figure)
        right_layout.addWidget(self.paddle_norm_canvas)
        
        norm_layout.addWidget(left_panel)
        norm_layout.addWidget(right_panel)
        
        self.tab_widget.addTab(norm_widget, "Normalization")
        
        # Connect updates
        self.paddle_175_start.valueChanged.connect(self.update_paddle_norm_display)
        self.paddle_175_end.valueChanged.connect(self.update_paddle_norm_display)
        self.paddle_225_start.valueChanged.connect(self.update_paddle_norm_display)
        self.paddle_225_end.valueChanged.connect(self.update_paddle_norm_display)
        
        self.update_paddle_norm_display()
        
    def populate_paddle_norm_parameters(self):
        """Populate normalization tab parameter dropdowns"""
        if not self.param_index:
            return
            
        # Populate flow
        flow_values = ['All'] + [str(v) for v in sorted(self.param_index.get('flow', []))]
        self.paddle_norm_flow.clear()
        self.paddle_norm_flow.addItems(flow_values)
        
        # Populate period
        period_values = ['All'] + [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) 
                                     for v in sorted(self.param_index.get('period', []))]
        self.paddle_norm_period.clear()
        self.paddle_norm_period.addItems(period_values)
        
        # Populate sweep
        sweep_values = ['All'] + [str(int(v)) for v in sorted(self.param_index.get('sweep', []))]
        self.paddle_norm_sweep.clear()
        self.paddle_norm_sweep.addItems(sweep_values)
        
        # Populate twist
        twist_values = ['All'] + [str(int(v)) for v in sorted(self.param_index.get('twist', []))]
        self.paddle_norm_twist.clear()
        self.paddle_norm_twist.addItems(twist_values)
    
    def update_paddle_norm_display(self):
        """Update paddle stroke normalization display"""
        dur_175 = self.paddle_175_end.value() - self.paddle_175_start.value()
        dur_225 = self.paddle_225_end.value() - self.paddle_225_start.value()
        self.paddle_175_duration.setText(f"{dur_175:.2f} s")
        self.paddle_225_duration.setText(f"{dur_225:.2f} s")
        
    def apply_paddle_normalization(self):
        """Apply paddle stroke normalization settings"""
        self.paddle_stroke_windows[1.75]['start'] = self.paddle_175_start.value()
        self.paddle_stroke_windows[1.75]['end'] = self.paddle_175_end.value()
        self.paddle_stroke_windows[2.25]['start'] = self.paddle_225_start.value()
        self.paddle_stroke_windows[2.25]['end'] = self.paddle_225_end.value()
        self.plot_paddle_normalization_traces()
        self.statusBar().showMessage("Paddle stroke normalization applied")
        
    def plot_paddle_normalization_traces(self):
        """Plot paddle stroke traces with absolute time"""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return
            
        self.paddle_norm_ax.clear()
        self.paddle_norm_ax.grid(True, alpha=0.3)
        
        channel = self.paddle_norm_channel.currentText()
        flow_filter = self.paddle_norm_flow.currentText()
        period_filter = self.paddle_norm_period.currentText()
        sweep_filter = self.paddle_norm_sweep.currentText()
        twist_filter = self.paddle_norm_twist.currentText()
        
        plotted_count = 0
        colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
        for exp_key, exp_data in self.data['experiments'].items():
            params = exp_data['parameters']
            m = self._param_map(params)
            
            # Apply all filters
            if flow_filter != 'All' and abs(m['flow'] - float(flow_filter)) > 1e-6:
                continue
            if period_filter != 'All' and abs(m['stroke_period'] - float(period_filter)) > 1e-6:
                continue
            if sweep_filter != 'All' and abs(m['sweep'] - float(sweep_filter)) > 1e-6:
                continue
            if twist_filter != 'All' and abs(m['twist'] - float(twist_filter)) > 1e-6:
                continue
                
            t_abs = np.asarray(exp_data['time_vector'])
            if channel == 'thrust':
                force = np.asarray(exp_data['thrust_mean'])
            else:
                force = np.asarray(exp_data['lift_mean'])
                
            if len(t_abs) == 0 or len(force) == 0:
                continue
                
            color = colors[plotted_count % len(colors)]
            label = f"F={m['flow']}, P={m['stroke_period']}, S={int(m['sweep'])}, T={int(m['twist'])}"
            self.paddle_norm_ax.plot(t_abs, force, linewidth=1.5, alpha=0.7, color=color, label=label)
            plotted_count += 1
            
            if plotted_count >= 5:
                break
        
        if plotted_count > 0:
            # Show paddle stroke boundaries
            if period_filter != 'All':
                period = float(period_filter)
                if abs(period - 1.75) < 0.1:
                    window = self.paddle_stroke_windows[1.75]
                else:
                    window = self.paddle_stroke_windows[2.25]
                    
                self.paddle_norm_ax.axvline(x=window['start'], color='blue', linestyle='--', linewidth=2, label=f"Paddle start ({window['start']:.2f}s)")
                self.paddle_norm_ax.axvline(x=window['end'], color='blue', linestyle='--', linewidth=2, label=f"Paddle end ({window['end']:.2f}s)")
                self.paddle_norm_ax.axvspan(window['start'], window['end'], alpha=0.1, color='blue')
            
            self.paddle_norm_ax.legend(loc='best', fontsize=8)
            
        self.paddle_norm_ax.set_xlabel('Absolute Time (seconds)', fontsize=11)
        self.paddle_norm_ax.set_ylabel(f'{channel.capitalize()} Force', fontsize=11)
        self.paddle_norm_ax.set_title('Paddle Stroke Boundary Selection', fontsize=12, fontweight='bold')
        self.paddle_norm_canvas.draw()
        
    def create_traces_tab(self):
        """Create the traces tab with EXACT original GUI structure"""
        traces_widget = QWidget()
        traces_layout = QVBoxLayout(traces_widget)
        
        # Top controls frame (EXACT copy from original)
        ctrl_frame = QFrame()
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(10, 8, 10, 8)
        
        # Channel selection (EXACT copy)
        chan_frame = QGroupBox("Channel")
        chan_layout = QHBoxLayout(chan_frame)
        chan_layout.addWidget(QLabel("Channel:"))
        
        self.channel_var = QComboBox()
        self.channel_var.addItems(["thrust", "lift"])
        self.channel_var.setCurrentText("thrust")
        chan_layout.addWidget(self.channel_var)
        
        ctrl_layout.addWidget(chan_frame)
        
        # Axis controls (EXACT copy)
        axis_frame = QGroupBox("Axis Controls")
        axis_layout = QGridLayout(axis_frame)
        
        self.xmin_var = QLineEdit("0.0")
        self.xmax_var = QLineEdit("1.0")
        self.xstep_var = QLineEdit("0.1")
        self.ymin_var = QLineEdit("-5.0")
        self.ymax_var = QLineEdit("5.0")
        self.ystep_var = QLineEdit("1.0")
        
        axis_layout.addWidget(QLabel("X min"), 0, 0)
        axis_layout.addWidget(self.xmin_var, 0, 1)
        axis_layout.addWidget(QLabel("X max"), 0, 2)
        axis_layout.addWidget(self.xmax_var, 0, 3)
        axis_layout.addWidget(QLabel("X step"), 0, 4)
        axis_layout.addWidget(self.xstep_var, 0, 5)
        
        axis_layout.addWidget(QLabel("Y min"), 1, 0)
        axis_layout.addWidget(self.ymin_var, 1, 1)
        axis_layout.addWidget(QLabel("Y max"), 1, 2)
        axis_layout.addWidget(self.ymax_var, 1, 3)
        axis_layout.addWidget(QLabel("Y step"), 1, 4)
        axis_layout.addWidget(self.ystep_var, 1, 5)
        
        ctrl_layout.addWidget(axis_frame)
        
        # Labels/Titles group (EXACT copy)
        labels_frame = QGroupBox("Labels/Titles")
        labels_layout = QGridLayout(labels_frame)
        
        font_choices = ['Default', 'DejaVu Sans', 'Arial', 'Calibri', 'Times New Roman', 'Helvetica']
        
        # Title controls
        self.title_on_var = QCheckBox("Title")
        self.title_on_var.setChecked(True)
        self.title_text_var = QLineEdit("Mean Trial Traces")
        self.title_font_var = QComboBox()
        self.title_font_var.addItems(font_choices)
        self.title_font_var.setCurrentText('Default')
        self.title_fs_var = QLineEdit("14")
        
        labels_layout.addWidget(self.title_on_var, 0, 0)
        labels_layout.addWidget(self.title_text_var, 0, 1)
        labels_layout.addWidget(self.title_font_var, 0, 2)
        labels_layout.addWidget(self.title_fs_var, 0, 3)
        
        # X label controls
        self.xlabel_on_var = QCheckBox("X Label")
        self.xlabel_on_var.setChecked(True)
        self.xlabel_text_var = QLineEdit("Time (s)")
        self.xlabel_font_var = QComboBox()
        self.xlabel_font_var.addItems(font_choices)
        self.xlabel_font_var.setCurrentText('Default')
        self.xlabel_fs_var = QLineEdit("12")
        
        labels_layout.addWidget(self.xlabel_on_var, 1, 0)
        labels_layout.addWidget(self.xlabel_text_var, 1, 1)
        labels_layout.addWidget(self.xlabel_font_var, 1, 2)
        labels_layout.addWidget(self.xlabel_fs_var, 1, 3)
        
        # Y label controls
        self.ylabel_on_var = QCheckBox("Y Label")
        self.ylabel_on_var.setChecked(True)
        self.ylabel_text_var = QLineEdit("Force (scaled)")
        self.ylabel_font_var = QComboBox()
        self.ylabel_font_var.addItems(font_choices)
        self.ylabel_font_var.setCurrentText('Default')
        self.ylabel_fs_var = QLineEdit("12")
        
        labels_layout.addWidget(self.ylabel_on_var, 2, 0)
        labels_layout.addWidget(self.ylabel_text_var, 2, 1)
        labels_layout.addWidget(self.ylabel_font_var, 2, 2)
        labels_layout.addWidget(self.ylabel_fs_var, 2, 3)
        
        ctrl_layout.addWidget(labels_frame)
        
        # Font controls (EXACT copy)
        font_frame = QGroupBox("Fonts")
        font_layout = QGridLayout(font_frame)
        
        self.axis_fs_var = QLineEdit("12")
        self.legend_fs_var = QLineEdit("10")
        self.legend_loc_var = QComboBox()
        legend_opts = ['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
        self.legend_loc_var.addItems(legend_opts)
        self.legend_loc_var.setCurrentText('best')
        self.legend_on_var = QCheckBox("Show Legend")
        self.legend_on_var.setChecked(True)
        
        font_layout.addWidget(QLabel("Title FS"), 0, 0)
        font_layout.addWidget(self.title_fs_var, 0, 1)
        font_layout.addWidget(QLabel("Axis FS"), 0, 2)
        font_layout.addWidget(self.axis_fs_var, 0, 3)
        font_layout.addWidget(QLabel("Legend FS"), 0, 4)
        font_layout.addWidget(self.legend_fs_var, 0, 5)
        
        font_layout.addWidget(QLabel("Legend Loc"), 1, 0)
        font_layout.addWidget(self.legend_loc_var, 1, 1, 1, 3)
        font_layout.addWidget(self.legend_on_var, 1, 4, 1, 2)
        
        ctrl_layout.addWidget(font_frame)
        
        # Color scheme controls (EXACT copy)
        color_frame = QGroupBox("Colors")
        color_layout = QHBoxLayout(color_frame)
        color_layout.addWidget(QLabel("Scheme"))
        self.color_scheme_var = QComboBox()
        self.color_scheme_var.addItems(['Default','CB friendly','Custom'])
        self.color_scheme_var.setCurrentText('Default')
        color_layout.addWidget(self.color_scheme_var)
        
        ctrl_layout.addWidget(color_frame)
        
        # Publish controls (EXACT copy)
        pub_frame = QGroupBox("Publish")
        pub_layout = QGridLayout(pub_frame)
        
        self.pub_w_var = QLineEdit("1200")
        self.pub_h_var = QLineEdit("800")
        self.pub_name_var = QLineEdit("FullStroke_plot.png")
        
        pub_layout.addWidget(QLabel("W(px)"), 0, 0)
        pub_layout.addWidget(self.pub_w_var, 0, 1)
        pub_layout.addWidget(QLabel("H(px)"), 0, 2)
        pub_layout.addWidget(self.pub_h_var, 0, 3)
        pub_layout.addWidget(QLabel("Name"), 1, 0)
        pub_layout.addWidget(self.pub_name_var, 1, 1, 1, 3)
        
        pub_button = QPushButton("Publish")
        pub_button.clicked.connect(self.publish_figure)
        pub_layout.addWidget(pub_button, 0, 4, 2, 1)
        
        ctrl_layout.addWidget(pub_frame)
        
        # Normalization toggle
        norm_toggle_frame = QGroupBox("Normalization Control")
        norm_toggle_layout = QHBoxLayout(norm_toggle_frame)
        
        self.include_norm_window = QCheckBox("Include Normalization Window")
        self.include_norm_window.setChecked(True)  # Default to enabled
        self.include_norm_window.setToolTip("When checked, applies user-defined trimming from Normalization tab. When unchecked, plots full traces.")
        norm_toggle_layout.addWidget(self.include_norm_window)
        norm_toggle_layout.addStretch()
        
        ctrl_layout.addWidget(norm_toggle_frame)
        
        # Plot button (EXACT copy)
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_overlay)
        self.plot_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        ctrl_layout.addWidget(self.plot_button)
        
        traces_layout.addWidget(ctrl_frame)
        
        # Window finder removed – x-axis is fixed normalized [0,1]
        
        # Dataset selectors (up to 10) - EXACT copy
        sel_frame = QGroupBox("Datasets (up to 10)")
        sel_layout = QVBoxLayout(sel_frame)
        
        # Master column controls (apply to all rows when fixed)
        master_frame = QGroupBox("Master Column Controls")
        master_layout = QGridLayout(master_frame)
        # Flow
        self.master_flow_fixed = QCheckBox("Fixed")
        self.master_flow = QComboBox(); self.master_flow.setMinimumWidth(80)
        master_layout.addWidget(QLabel("Flow"), 0, 0)
        master_layout.addWidget(self.master_flow_fixed, 0, 1)
        master_layout.addWidget(self.master_flow, 0, 2)
        # Period
        self.master_period_fixed = QCheckBox("Fixed")
        self.master_period = QComboBox(); self.master_period.setMinimumWidth(80)
        master_layout.addWidget(QLabel("Period"), 0, 3)
        master_layout.addWidget(self.master_period_fixed, 0, 4)
        master_layout.addWidget(self.master_period, 0, 5)
        # Sweep
        self.master_yaw_fixed = QCheckBox("Fixed")
        self.master_yaw = QComboBox(); self.master_yaw.setMinimumWidth(80)
        master_layout.addWidget(QLabel("Sweep"), 0, 6)
        master_layout.addWidget(self.master_yaw_fixed, 0, 7)
        master_layout.addWidget(self.master_yaw, 0, 8)
        # Twist
        self.master_roll_fixed = QCheckBox("Fixed")
        self.master_roll = QComboBox(); self.master_roll.setMinimumWidth(80)
        master_layout.addWidget(QLabel("Twist"), 0, 9)
        master_layout.addWidget(self.master_roll_fixed, 0, 10)
        master_layout.addWidget(self.master_roll, 0, 11)
        # No phase overlap for Power stroke data
        sel_layout.addWidget(master_frame)
        
        # Create scroll area for dataset selectors
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.dataset_rows = []
        for i in range(10):
            row = self._build_selector_row(scroll_layout, i)
            self.dataset_rows.append(row)
            
        scroll_area.setWidget(scroll_widget)
        scroll_area.setMaximumHeight(300)
        sel_layout.addWidget(scroll_area)
        
        traces_layout.addWidget(sel_frame)
        
        
        # Matplotlib Figure (EXACT copy)
        self.traces_figure = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.traces_figure.add_subplot(111)
        self.ax.grid(True, alpha=0.3)
        self.traces_canvas = FigureCanvas(self.traces_figure)
        traces_layout.addWidget(self.traces_canvas)
        
        self.tab_widget.addTab(traces_widget, "Trial Traces")
        
        # Wire master controls behavior
        def _bind_master(fixed_cb, master_combo, key_name):
            try:
                fixed_cb.toggled.connect(lambda _: self._apply_master_to_rows(key_name))
                master_combo.currentIndexChanged.connect(lambda _: self._apply_master_to_rows(key_name))
            except Exception:
                pass
        _bind_master(self.master_flow_fixed, self.master_flow, 'flow')
        _bind_master(self.master_period_fixed, self.master_period, 'period')
        _bind_master(self.master_yaw_fixed, self.master_yaw, 'yaw')
        _bind_master(self.master_roll_fixed, self.master_roll, 'roll')
        # No phase overlap for Power stroke data
        
        
    
        
    def plot_overlay(self):
        """Plot overlay traces (EXACT copy from original GUI)"""
        try:
            # Gather selections in order
            selections = []
            for row in self.dataset_rows:
                if not row['include'].isChecked():
                    continue
                try:
                    # Use master values when the corresponding Fixed is checked
                    flow_text = self.master_flow.currentText() if getattr(self, 'master_flow_fixed', None) and self.master_flow_fixed.isChecked() else row['flow'].currentText()
                    period_text = self.master_period.currentText() if getattr(self, 'master_period_fixed', None) and self.master_period_fixed.isChecked() else row['period'].currentText()
                    yaw_text = self.master_yaw.currentText() if getattr(self, 'master_yaw_fixed', None) and self.master_yaw_fixed.isChecked() else row['yaw'].currentText()
                    roll_text = self.master_roll.currentText() if getattr(self, 'master_roll_fixed', None) and self.master_roll_fixed.isChecked() else row['roll'].currentText()
                    # No phase overlap for Power stroke data

                    flow = float(flow_text)
                    period = float(period_text)
                    yaw = float(yaw_text)   # sweep (absolute)
                    roll = float(roll_text) # twist (absolute)
                except ValueError:
                    continue
                exp_key = self._select_experiment(flow, period, yaw, roll)
                if exp_key is None:
                    continue
                selections.append((exp_key, flow, period, yaw, roll))

            if len(selections) == 0:
                return

            # Clear axes
            self.ax.clear()
            self.ax.grid(True, alpha=0.3)
            # Font sizes
            def _pf(s: str, default: float) -> float:
                try:
                    return float(s)
                except Exception:
                    return default
            title_fs = _pf(self.title_fs_var.text(), 14)
            axis_fs = _pf(self.axis_fs_var.text(), 12)
            legend_fs = _pf(self.legend_fs_var.text(), 10)
            # Font family helper
            def _fontfam(sel: str) -> dict:
                return {'fontfamily': sel} if sel and sel != 'Default' else {}

            # Apply labels based on toggles
            if self.title_on_var.isChecked():
                self.ax.set_title(self.title_text_var.text(), fontsize=title_fs, **_fontfam(self.title_font_var.currentText()))
            else:
                self.ax.set_title('')
            if self.xlabel_on_var.isChecked():
                self.ax.set_xlabel(self.xlabel_text_var.text(), fontsize=_pf(self.xlabel_fs_var.text(), axis_fs), **_fontfam(self.xlabel_font_var.currentText()))
            else:
                self.ax.set_xlabel('')
            if self.ylabel_on_var.isChecked():
                self.ax.set_ylabel(self.ylabel_text_var.text(), fontsize=_pf(self.ylabel_fs_var.text(), axis_fs), **_fontfam(self.ylabel_font_var.currentText()))
            else:
                self.ax.set_ylabel('')
            self.ax.tick_params(labelsize=axis_fs)

            # Plot in reverse so first selection is on top
            for exp_key, flow, period, yaw, roll in reversed(selections):
                if exp_key not in self.data['experiments']:
                    continue
                    
                exp_data = self.data['experiments'][exp_key]
                t_abs = np.asarray(exp_data['time_vector'])
                
                # Check if normalization window should be applied
                if self.include_norm_window.isChecked():
                    # Apply user-defined trimming from normalization tab
                    # Use correct window based on period
                    if abs(period - 1.75) < 0.1:
                        paddle_window = self.paddle_stroke_windows[1.75]
                    elif abs(period - 2.25) < 0.1:
                        paddle_window = self.paddle_stroke_windows[2.25]
                    else:
                        paddle_window = self.paddle_stroke_windows[1.75] if period < 2.0 else self.paddle_stroke_windows[2.25]
                    
                    start_time = paddle_window['start']
                    end_time = paddle_window['end']
                    mask_domain = (t_abs >= start_time) & (t_abs <= end_time)
                    
                    if not np.any(mask_domain):
                        continue
                    
                    # Map trimmed paddle stroke data to [0.4, 1.0] range (last 60% of full period)
                    t_abs_trimmed = t_abs[mask_domain]
                    t = np.linspace(0.4, 1.0, len(t_abs_trimmed))  # Direct mapping to paddle stroke portion
                else:
                    # Use full trace without trimming
                    print(f"DEBUG: Using full paddle stroke trace without normalization window")
                    t = np.linspace(0.4, 1.0, len(t_abs))  # Map full trace to paddle stroke portion
                    mask_domain = np.ones_like(t_abs, dtype=bool)  # No masking
                if self.channel_var.currentText() == 'thrust':
                    y = np.asarray(exp_data['thrust_mean'])[mask_domain]
                    ystd_full = exp_data.get('thrust_std', None)
                    ystd = np.asarray(ystd_full)[mask_domain] if ystd_full is not None else None
                    label = f"T: flow={flow}, P={period}, sweep={int(yaw)}, twist={int(roll)}"
                else:
                    y = np.asarray(exp_data['lift_mean'])[mask_domain]
                    ystd_full = exp_data.get('lift_std', None)
                    ystd = np.asarray(ystd_full)[mask_domain] if ystd_full is not None else None
                    label = f"L: flow={flow}, P={period}, sweep={int(yaw)}, twist={int(roll)}"
                
                # Ensure t and y have the same length
                min_len = min(len(t), len(y))
                t = t[:min_len]
                y = y[:min_len]
                if ystd is not None:
                    ystd = ystd[:min_len]
                mask_domain = mask_domain[:min_len]

                # Styles
                color = None
                lw = 2.0
                alpha = 0.2
                # Find the row that provided this selection to read style settings
                row_index_for_palette = 0
                for ridx, row in enumerate(self.dataset_rows):
                    try:
                        if not row['include'].isChecked():
                            continue
                        if abs(float(row['flow'].currentText()) - flow) > 1e-6:
                            continue
                        if abs(float(row['period'].currentText()) - period) > 1e-6:
                            continue
                        if abs(float(row['yaw'].currentText()) - yaw) > 1e-6:
                            continue
                        if abs(float(row['roll'].currentText()) - roll) > 1e-6:
                            continue
                        # No phase overlap for Power stroke data
                        row_index_for_palette = ridx
                        cval = row['color'].text().strip()
                        if cval and not cval.startswith('#'):
                            cval = '#' + cval
                        try:
                            lw = float(row['lw'].text()) if row['lw'].text() else 2.0
                        except Exception:
                            lw = 2.0
                        try:
                            alpha = float(row['alpha'].text()) if row['alpha'].text() else 0.2
                        except Exception:
                            alpha = 0.2
                        include_var = row['variance'].isChecked()
                        legend_on = row['legend_on'].isChecked()
                        legend_label = row['legend_label'].text().strip()
                        break
                    except Exception:
                        continue
                else:
                    include_var = False
                    legend_on = True
                    legend_label = ''

                # Check if this is a baseline experiment
                is_baseline = self._is_baseline_experiment(flow, period, yaw, roll)
                
                # Determine color by scheme
                scheme = self.color_scheme_var.currentText()
                if is_baseline:
                    # Use baseline color and styling for baseline experiments
                    color = self.baseline_color if self.baseline_color.startswith('#') else '#' + self.baseline_color
                    lw = lw * 2.0  # Make baseline traces thicker
                    alpha = min(alpha * 1.5, 1.0)  # Make baseline traces more opaque
                elif scheme == 'Custom':
                    # Use user-entered color if provided; else fallback to default palette
                    if cval:
                        color = cval
                    else:
                        color = self._palette_color('Default', row_index_for_palette)
                else:
                    color = self._palette_color(scheme, row_index_for_palette)

                # Variance shading (mean ± std)
                if include_var and ystd is not None:
                    self.ax.fill_between(t, y - ystd, y + ystd, color=color, alpha=max(0.0, min(alpha, 1.0)), linewidth=0)

                # Mean line with legend label control
                if is_baseline and legend_on:
                    # Add baseline indicator to legend
                    baseline_suffix = " (Baseline)"
                    if legend_label:
                        plot_label = legend_label + baseline_suffix
                    else:
                        plot_label = f"T: flow={flow}, P={period}, sweep={int(yaw)}, twist={int(roll)}{baseline_suffix}" if self.channel_var.currentText() == 'thrust' else f"L: flow={flow}, P={period}, sweep={int(yaw)}, twist={int(roll)}{baseline_suffix}"
                else:
                    plot_label = legend_label if legend_on and legend_label else '_nolegend_'
                
                # Apply baseline line style if needed
                if is_baseline:
                    line_style = self.baseline_line_style if self.baseline_line_style != 'None' else '-'
                    self.ax.plot(t, y, linewidth=max(0.5, lw), label=plot_label, color=color, linestyle=line_style)
                else:
                    self.ax.plot(t, y, linewidth=max(0.5, lw), label=plot_label, color=color)

            if selections and self.legend_on_var.isChecked():
                loc = self.legend_loc_var.currentText() if self.legend_loc_var.currentText() else 'best'
                self.ax.legend(loc=loc, fontsize=legend_fs)

            # Axes ranges and ticks
            def _parse_float(s: str, default: float) -> float:
                try:
                    return float(s)
                except Exception:
                    return default

            xmin = 0.0
            xmax = 1.0
            ymin = _parse_float(self.ymin_var.text(), -5.0)
            ymax = _parse_float(self.ymax_var.text(), 5.0)
            xstep = _parse_float(self.xstep_var.text(), 0.1)
            ystep = _parse_float(self.ystep_var.text(), 1.0)

            if xmax > xmin:
                self.ax.set_xlim(xmin, xmax)
                if xstep > 0:
                    xticks = np.arange(xmin, xmax + 0.5 * xstep, xstep)
                    self.ax.set_xticks(xticks)
            if ymax > ymin:
                self.ax.set_ylim(ymin, ymax)
                if ystep > 0:
                    yticks = np.arange(ymin, ymax + 0.5 * ystep, ystep)
                    self.ax.set_yticks(yticks)

            self.traces_canvas.draw()
            
            # No window lines; x-axis is normalized 0..1

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot: {e}")
            
    def _palette_color(self, scheme: str, idx: int) -> str:
        """Get color from palette (EXACT copy from original)"""
        if scheme == 'CB friendly':
            palette = [
                '#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442',
                '#0072B2', '#D55E00', '#CC79A7', '#999999'
            ]
        else:  # 'Default'
            palette = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]
        if len(palette) == 0:
            return '#000000'
        return palette[idx % len(palette)]
        
    def publish_figure(self):
        """Publish figure (EXACT copy from original)"""
        try:
            # Parse dimensions
            wpx = int(float(self.pub_w_var.text()))
            hpx = int(float(self.pub_h_var.text()))
            name = self.pub_name_var.text()
            
            # Save figure
            self.traces_figure.set_size_inches(wpx/100.0, hpx/100.0)
            self.traces_figure.savefig(name, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            
            QMessageBox.information(self, "Success", f"Figure saved as {name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish figure: {e}")

    def publish_mean_force_figure(self):
        try:
            wpx = int(float(self.mf_pub_w.text()))
            hpx = int(float(self.mf_pub_h.text()))
            name = self.mf_pub_name.text()
            self.mean_force_figure.set_size_inches(wpx/100.0, hpx/100.0)
            self.mean_force_figure.savefig(name, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            QMessageBox.information(self, "Success", f"Figure saved as {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish figure: {e}")

    def publish_peak_location_figure(self):
        try:
            wpx = int(float(self.pk_pub_w.text()))
            hpx = int(float(self.pk_pub_h.text()))
            name = self.pk_pub_name.text()
            self.peak_location_figure.set_size_inches(wpx/100.0, hpx/100.0)
            self.peak_location_figure.savefig(name, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            QMessageBox.information(self, "Success", f"Figure saved as {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish figure: {e}")

    def publish_vector_figure(self):
        try:
            wpx = int(float(self.vec_pub_w.text()))
            hpx = int(float(self.vec_pub_h.text()))
            name = self.vec_pub_name.text()
            self.vector_figure.set_size_inches(wpx/100.0, hpx/100.0)
            self.vector_figure.savefig(name, dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
            QMessageBox.information(self, "Success", f"Figure saved as {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish figure: {e}")
        
    def create_mean_force_tab(self):
        """Create the mean force tab - decoupled selection (Flow/Sweep/Overlap)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Compact top controls panel
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)

        # Variable Selection (compact horizontal)
        var_frame = QGroupBox("Variable Selection")
        var_layout = QHBoxLayout(var_frame)
        var_layout.setContentsMargins(5, 5, 5, 5)
        
        self.mean_force_variable_group = QButtonGroup()
        self.mean_force_flow_radio = QRadioButton("Flow")
        self.mean_force_sweep_radio = QRadioButton("Sweep")
        
        self.mean_force_variable_group.addButton(self.mean_force_flow_radio, 0)
        self.mean_force_variable_group.addButton(self.mean_force_sweep_radio, 1)
        self.mean_force_flow_radio.setChecked(True)
        
        # Connect radio button changes to update controls
        self.mean_force_variable_group.buttonClicked.connect(self.update_mean_force_parameter_controls)
        
        var_layout.addWidget(self.mean_force_flow_radio)
        var_layout.addWidget(self.mean_force_sweep_radio)
        # No overlap in Power stroke
        top_layout.addWidget(var_frame)
        
        # Fixed Parameters Display (compact)
        mf_fixed_frame = QGroupBox("Fixed Parameters")
        mf_fixed_layout = QHBoxLayout(mf_fixed_frame)
        mf_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.mean_force_fixed_params_label = QLabel("Flow: 0.1 | Sweep: 80° | Period: 2.25s")
        mf_fixed_layout.addWidget(self.mean_force_fixed_params_label)
        top_layout.addWidget(mf_fixed_frame)
        
        # Plot controls (compact horizontal)
        plot_control_frame = QGroupBox("Plot Control Panel")
        plot_control_layout = QHBoxLayout(plot_control_frame)
        plot_control_layout.setContentsMargins(5, 5, 5, 5)
        plot_control_layout.addWidget(QLabel("Channel:"))
        self.mean_force_channel = QComboBox()
        self.mean_force_channel.addItems(["Thrust", "Lift"])
        self.mean_force_channel.setCurrentText("Thrust")
        plot_control_layout.addWidget(self.mean_force_channel)
        self.plot_mean_force_button = QPushButton("Plot Mean Force")
        self.plot_mean_force_button.clicked.connect(self.plot_mean_force)
        self.plot_mean_force_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        plot_control_layout.addWidget(self.plot_mean_force_button)
        top_layout.addWidget(plot_control_frame)
        
        # Twist selection (checkbox row)
        self.mean_twist_box = QGroupBox("Twists")
        self.mean_twist_layout = QHBoxLayout(self.mean_twist_box)
        self.mean_twist_layout.setContentsMargins(5, 5, 5, 5)
        self.mean_twist_checks = {}
        top_layout.addWidget(self.mean_twist_box)
        
        # Variable Parameter Controls (per value marker + toggle)
        self.mean_force_var_controls_frame = QGroupBox("Variable Parameter Controls")
        self.mean_force_var_controls_layout = QHBoxLayout(self.mean_force_var_controls_frame)
        self.mean_force_var_controls_layout.setContentsMargins(5, 5, 5, 5)
        self.mean_force_parameter_controls = {}
        
        # Compact middle controls panel
        middle_panel = QWidget()
        middle_layout = QHBoxLayout(middle_panel)
        middle_layout.setContentsMargins(5, 5, 5, 5)
        middle_layout.setSpacing(10)

        # Publish controls (compact)
        pub_frame = QGroupBox("Publish")
        pub_layout = QHBoxLayout(pub_frame)
        pub_layout.setContentsMargins(5, 5, 5, 5)
        pub_layout.addWidget(QLabel("W(px)"))
        self.mf_pub_w = QLineEdit("1200")
        self.mf_pub_w.setMaximumWidth(60)
        pub_layout.addWidget(self.mf_pub_w)
        pub_layout.addWidget(QLabel("H(px)"))
        self.mf_pub_h = QLineEdit("800")
        self.mf_pub_h.setMaximumWidth(60)
        pub_layout.addWidget(self.mf_pub_h)
        pub_layout.addWidget(QLabel("Name"))
        self.mf_pub_name = QLineEdit("MeanForce_plot.png")
        self.mf_pub_name.setMaximumWidth(150)
        pub_layout.addWidget(self.mf_pub_name)
        mf_pub_button = QPushButton("Publish PNG")
        mf_pub_button.clicked.connect(self.publish_mean_force_figure)
        pub_layout.addWidget(mf_pub_button)
        middle_layout.addWidget(pub_frame)

        # Axes & Legend Controls (compact horizontal)
        axes_frame = QGroupBox("Axes and Legend")
        axes_layout = QHBoxLayout(axes_frame)
        axes_layout.setContentsMargins(5, 5, 5, 5)
        axes_layout.addWidget(QLabel("X min"))
        self.mf_xmin = QLineEdit("")
        self.mf_xmin.setPlaceholderText("auto")
        self.mf_xmin.setMaximumWidth(60)
        axes_layout.addWidget(self.mf_xmin)
        axes_layout.addWidget(QLabel("X max"))
        self.mf_xmax = QLineEdit("")
        self.mf_xmax.setPlaceholderText("auto")
        self.mf_xmax.setMaximumWidth(60)
        axes_layout.addWidget(self.mf_xmax)
        axes_layout.addWidget(QLabel("Y min"))
        self.mf_ymin = QLineEdit("")
        self.mf_ymin.setPlaceholderText("auto")
        self.mf_ymin.setMaximumWidth(60)
        axes_layout.addWidget(self.mf_ymin)
        axes_layout.addWidget(QLabel("Y max"))
        self.mf_ymax = QLineEdit("")
        self.mf_ymax.setPlaceholderText("auto")
        self.mf_ymax.setMaximumWidth(60)
        axes_layout.addWidget(self.mf_ymax)
        axes_layout.addWidget(QLabel("Tick font"))
        self.mf_tick_font = QComboBox()
        self.mf_tick_font.addItems(['Default','DejaVu Sans','Arial','Calibri','Times New Roman','Helvetica'])
        self.mf_tick_font.setMaximumWidth(100)
        axes_layout.addWidget(self.mf_tick_font)
        self.mf_legend_on = QCheckBox("Legend")
        axes_layout.addWidget(self.mf_legend_on)
        self.mf_legend_loc = QComboBox()
        self.mf_legend_loc.addItems(["best","upper right","upper left","lower left","lower right","right","center left","center right","lower center","upper center","center"]) 
        self.mf_legend_loc.setCurrentText("best")
        self.mf_legend_loc.setMaximumWidth(80)
        axes_layout.addWidget(QLabel("Loc"))
        axes_layout.addWidget(self.mf_legend_loc)
        middle_layout.addWidget(axes_frame)

        # Additional controls panel (for missing elements)
        additional_panel = QWidget()
        additional_layout = QHBoxLayout(additional_panel)
        additional_layout.setContentsMargins(5, 5, 5, 5)
        additional_layout.setSpacing(10)

        # Title controls
        title_frame = QGroupBox("Title")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(5, 5, 5, 5)
        self.mf_title_on = QCheckBox("Title")
        title_layout.addWidget(self.mf_title_on)
        self.mf_title_text = QLineEdit("")
        self.mf_title_text.setPlaceholderText("auto")
        self.mf_title_text.setMaximumWidth(150)
        title_layout.addWidget(self.mf_title_text)
        additional_layout.addWidget(title_frame)

        # X Label controls
        xlabel_frame = QGroupBox("X Label")
        xlabel_layout = QHBoxLayout(xlabel_frame)
        xlabel_layout.setContentsMargins(5, 5, 5, 5)
        self.mf_xlabel_on = QCheckBox("X Label")
        xlabel_layout.addWidget(self.mf_xlabel_on)
        self.mf_xlabel_text = QLineEdit("Absolute Twist (degrees)")
        self.mf_xlabel_text.setMaximumWidth(150)
        xlabel_layout.addWidget(self.mf_xlabel_text)
        additional_layout.addWidget(xlabel_frame)

        # Y Label controls
        ylabel_frame = QGroupBox("Y Label")
        ylabel_layout = QHBoxLayout(ylabel_frame)
        ylabel_layout.setContentsMargins(5, 5, 5, 5)
        self.mf_ylabel_on = QCheckBox("Y Label")
        ylabel_layout.addWidget(self.mf_ylabel_on)
        self.mf_ylabel_text = QLineEdit("Mean Thrust Force (N)")
        self.mf_ylabel_text.setMaximumWidth(150)
        ylabel_layout.addWidget(self.mf_ylabel_text)
        additional_layout.addWidget(ylabel_frame)

        # Tick step controls
        tick_frame = QGroupBox("Tick Steps")
        tick_layout = QHBoxLayout(tick_frame)
        tick_layout.setContentsMargins(5, 5, 5, 5)
        tick_layout.addWidget(QLabel("X format"))
        self.mf_xticks_text = QLineEdit("")
        self.mf_xticks_text.setPlaceholderText("start:step:end")
        self.mf_xticks_text.setMaximumWidth(100)
        tick_layout.addWidget(self.mf_xticks_text)
        tick_layout.addWidget(QLabel("Y step"))
        self.mf_ytick_step = QLineEdit("")
        self.mf_ytick_step.setPlaceholderText("auto")
        self.mf_ytick_step.setMaximumWidth(60)
        tick_layout.addWidget(self.mf_ytick_step)
        tick_layout.addWidget(QLabel("Tick size"))
        self.mf_tick_fs = QLineEdit("")
        self.mf_tick_fs.setPlaceholderText("auto")
        self.mf_tick_fs.setMaximumWidth(60)
        tick_layout.addWidget(self.mf_tick_fs)
        additional_layout.addWidget(tick_frame)

        # Marker style controls (compact horizontal)
        marker_frame = QGroupBox("Marker Style")
        marker_layout = QHBoxLayout(marker_frame)
        marker_layout.setContentsMargins(5, 5, 5, 5)
        marker_layout.addWidget(QLabel("Size"))
        self.mf_marker_size = QLineEdit("50")
        self.mf_marker_size.setMaximumWidth(50)
        marker_layout.addWidget(self.mf_marker_size)
        marker_layout.addWidget(QLabel("Edge color"))
        self.mf_marker_edge_color = QLineEdit("#000000")
        self.mf_marker_edge_color.setMaximumWidth(80)
        marker_layout.addWidget(self.mf_marker_edge_color)
        marker_layout.addWidget(QLabel("Edge width"))
        self.mf_marker_edge_width = QLineEdit("0.4")
        self.mf_marker_edge_width.setMaximumWidth(50)
        marker_layout.addWidget(self.mf_marker_edge_width)
        self.mf_grid_on = QCheckBox("Grid")
        self.mf_grid_on.setChecked(True)
        marker_layout.addWidget(self.mf_grid_on)
        middle_layout.addWidget(marker_frame)

        # Assemble controls panel
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(0,0,0,0)
        panel_layout.setSpacing(5)
        panel_layout.addWidget(top_panel)
        panel_layout.addWidget(self.mean_force_var_controls_frame)
        panel_layout.addWidget(middle_panel)
        panel_layout.addWidget(additional_panel)

        # Create matplotlib figure for mean force below in splitter for larger plot area (50/50 split)
        self.mean_force_figure = Figure(figsize=(12, 8))
        self.mean_force_canvas = FigureCanvas(self.mean_force_figure)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(panel_widget)
        splitter.addWidget(self.mean_force_canvas)
        splitter.setSizes([400, 400])  # 50/50 split instead of 300/900
        layout.addWidget(splitter)
        
        # Seed parameter controls
        self.update_mean_force_parameter_controls()
        
        # Populate twist checkboxes
        self._populate_twist_checkboxes('mean')
        
        self.tab_widget.addTab(tab, "Mean Force")
        
    def create_peak_location_tab(self):
        """Create the peak location tab - data selection like Mean Force; color by twist."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Compact top controls panel
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)

        # Variable Selection (compact horizontal)
        var_frame = QGroupBox("Variable Selection")
        var_layout = QHBoxLayout(var_frame)
        var_layout.setContentsMargins(5, 5, 5, 5)
        self.peak_variable_group = QButtonGroup()
        self.peak_flow_radio = QRadioButton("Flow")
        self.peak_sweep_radio = QRadioButton("Sweep")
        self.peak_variable_group.addButton(self.peak_flow_radio, 0)
        self.peak_variable_group.addButton(self.peak_sweep_radio, 1)
        self.peak_flow_radio.setChecked(True)
        var_layout.addWidget(self.peak_flow_radio)
        var_layout.addWidget(self.peak_sweep_radio)
        # No overlap in Power stroke
        top_layout.addWidget(var_frame)

        # Fixed Parameters (compact)
        peak_fixed = QGroupBox("Fixed Parameters")
        peak_fixed_layout = QHBoxLayout(peak_fixed)
        peak_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.peak_fixed_params_label = QLabel("Flow: Variable | Sweep: 80° | Period: 2.25s")
        peak_fixed_layout.addWidget(self.peak_fixed_params_label)
        top_layout.addWidget(peak_fixed)

        # Plot controls (compact horizontal)
        plot_control_frame = QGroupBox("Plot Control Panel")
        plot_control_layout = QHBoxLayout(plot_control_frame)
        plot_control_layout.setContentsMargins(5, 5, 5, 5)
        plot_control_layout.addWidget(QLabel("Channel:"))
        self.peak_location_channel = QComboBox()
        self.peak_location_channel.addItems(["Thrust", "Lift"])
        self.peak_location_channel.setCurrentText("Thrust")
        plot_control_layout.addWidget(self.peak_location_channel)
        self.plot_peak_location_button = QPushButton("Plot Peak Location")
        self.plot_peak_location_button.clicked.connect(self.plot_peak_location)
        self.plot_peak_location_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        plot_control_layout.addWidget(self.plot_peak_location_button)
        top_layout.addWidget(plot_control_frame)
        
        # Twist selection (checkbox row)
        self.peak_twist_box = QGroupBox("Twists")
        self.peak_twist_layout = QHBoxLayout(self.peak_twist_box)
        self.peak_twist_layout.setContentsMargins(5, 5, 5, 5)
        self.peak_twist_checks = {}
        top_layout.addWidget(self.peak_twist_box)

        # Variable Parameter Controls (marker style + toggle per value)
        self.peak_var_controls_frame = QGroupBox("Variable Parameter Controls")
        self.peak_var_controls_layout = QVBoxLayout(self.peak_var_controls_frame)
        self.peak_var_controls_layout.setContentsMargins(5, 5, 5, 5)
        self.peak_parameter_controls = {}

        # Compact middle controls panel
        middle_panel = QWidget()
        middle_layout = QHBoxLayout(middle_panel)
        middle_layout.setContentsMargins(5, 5, 5, 5)
        middle_layout.setSpacing(10)

        # Publish controls (compact)
        pub_frame = QGroupBox("Publish")
        pub_layout = QHBoxLayout(pub_frame)
        pub_layout.setContentsMargins(5, 5, 5, 5)
        pub_layout.addWidget(QLabel("W(px)"))
        self.pk_pub_w = QLineEdit("1200")
        self.pk_pub_w.setMaximumWidth(60)
        pub_layout.addWidget(self.pk_pub_w)
        pub_layout.addWidget(QLabel("H(px)"))
        self.pk_pub_h = QLineEdit("800")
        self.pk_pub_h.setMaximumWidth(60)
        pub_layout.addWidget(self.pk_pub_h)
        pub_layout.addWidget(QLabel("Name"))
        self.pk_pub_name = QLineEdit("PeakLocation_plot.png")
        self.pk_pub_name.setMaximumWidth(150)
        pub_layout.addWidget(self.pk_pub_name)
        pk_pub_button = QPushButton("Publish PNG")
        pk_pub_button.clicked.connect(self.publish_peak_location_figure)
        pub_layout.addWidget(pk_pub_button)
        middle_layout.addWidget(pub_frame)

        # Axes and legend controls (compact horizontal)
        axes_frame = QGroupBox("Axes and Legend")
        axes_layout = QHBoxLayout(axes_frame)
        axes_layout.setContentsMargins(5, 5, 5, 5)
        axes_layout.addWidget(QLabel("X min"))
        self.pk_xmin = QLineEdit("")
        self.pk_xmin.setPlaceholderText("auto")
        self.pk_xmin.setMaximumWidth(60)
        axes_layout.addWidget(self.pk_xmin)
        axes_layout.addWidget(QLabel("X max"))
        self.pk_xmax = QLineEdit("")
        self.pk_xmax.setPlaceholderText("auto")
        self.pk_xmax.setMaximumWidth(60)
        axes_layout.addWidget(self.pk_xmax)
        axes_layout.addWidget(QLabel("Y min"))
        self.pk_ymin = QLineEdit("")
        self.pk_ymin.setPlaceholderText("auto")
        self.pk_ymin.setMaximumWidth(60)
        axes_layout.addWidget(self.pk_ymin)
        axes_layout.addWidget(QLabel("Y max"))
        self.pk_ymax = QLineEdit("")
        self.pk_ymax.setPlaceholderText("auto")
        self.pk_ymax.setMaximumWidth(60)
        axes_layout.addWidget(self.pk_ymax)
        axes_layout.addWidget(QLabel("Tick font"))
        self.pk_tick_font = QComboBox()
        self.pk_tick_font.addItems(['Default','DejaVu Sans','Arial','Calibri','Times New Roman','Helvetica'])
        self.pk_tick_font.setMaximumWidth(100)
        axes_layout.addWidget(self.pk_tick_font)
        self.pk_legend_on = QCheckBox("Legend")
        axes_layout.addWidget(self.pk_legend_on)
        self.pk_legend_loc = QComboBox()
        self.pk_legend_loc.addItems(["best","upper right","upper left","lower left","lower right","right","center left","center right","lower center","upper center","center"]) 
        self.pk_legend_loc.setCurrentText("best")
        self.pk_legend_loc.setMaximumWidth(80)
        axes_layout.addWidget(QLabel("Loc"))
        axes_layout.addWidget(self.pk_legend_loc)
        middle_layout.addWidget(axes_frame)

        # Marker styling (compact horizontal)
        marker_frame = QGroupBox("Marker Style")
        marker_layout = QHBoxLayout(marker_frame)
        marker_layout.setContentsMargins(5, 5, 5, 5)
        marker_layout.addWidget(QLabel("Size"))
        self.pk_marker_size = QLineEdit("60")
        self.pk_marker_size.setMaximumWidth(50)
        marker_layout.addWidget(self.pk_marker_size)
        marker_layout.addWidget(QLabel("Edge color"))
        self.pk_marker_edge_color = QLineEdit("#000000")
        self.pk_marker_edge_color.setMaximumWidth(80)
        marker_layout.addWidget(self.pk_marker_edge_color)
        marker_layout.addWidget(QLabel("Edge width"))
        self.pk_marker_edge_width = QLineEdit("0.4")
        self.pk_marker_edge_width.setMaximumWidth(50)
        marker_layout.addWidget(self.pk_marker_edge_width)
        self.pk_grid_on = QCheckBox("Grid")
        self.pk_grid_on.setChecked(True)
        marker_layout.addWidget(self.pk_grid_on)
        middle_layout.addWidget(marker_frame)

        # Additional controls panel (for missing elements)
        additional_panel = QWidget()
        additional_layout = QHBoxLayout(additional_panel)
        additional_layout.setContentsMargins(5, 5, 5, 5)
        additional_layout.setSpacing(10)

        # Title controls
        title_frame = QGroupBox("Title")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(5, 5, 5, 5)
        self.pk_title_on = QCheckBox("Title")
        title_layout.addWidget(self.pk_title_on)
        self.pk_title_text = QLineEdit("")
        self.pk_title_text.setPlaceholderText("auto")
        self.pk_title_text.setMaximumWidth(150)
        title_layout.addWidget(self.pk_title_text)
        additional_layout.addWidget(title_frame)

        # X Label controls
        xlabel_frame = QGroupBox("X Label")
        xlabel_layout = QHBoxLayout(xlabel_frame)
        xlabel_layout.setContentsMargins(5, 5, 5, 5)
        self.pk_xlabel_on = QCheckBox("X Label")
        xlabel_layout.addWidget(self.pk_xlabel_on)
        self.pk_xlabel_text = QLineEdit("Absolute Twist (degrees)")
        self.pk_xlabel_text.setMaximumWidth(150)
        xlabel_layout.addWidget(self.pk_xlabel_text)
        additional_layout.addWidget(xlabel_frame)

        # Y Label controls
        ylabel_frame = QGroupBox("Y Label")
        ylabel_layout = QHBoxLayout(ylabel_frame)
        ylabel_layout.setContentsMargins(5, 5, 5, 5)
        self.pk_ylabel_on = QCheckBox("Y Label")
        ylabel_layout.addWidget(self.pk_ylabel_on)
        self.pk_ylabel_text = QLineEdit("Peak Thrust Timing (Normalized)")
        self.pk_ylabel_text.setMaximumWidth(150)
        ylabel_layout.addWidget(self.pk_ylabel_text)
        additional_layout.addWidget(ylabel_frame)

        # Tick step controls
        tick_frame = QGroupBox("Tick Steps")
        tick_layout = QHBoxLayout(tick_frame)
        tick_layout.setContentsMargins(5, 5, 5, 5)
        tick_layout.addWidget(QLabel("X format"))
        self.pk_xticks_text = QLineEdit("")
        self.pk_xticks_text.setPlaceholderText("start:step:end")
        self.pk_xticks_text.setMaximumWidth(100)
        tick_layout.addWidget(self.pk_xticks_text)
        tick_layout.addWidget(QLabel("Y step"))
        self.pk_ytick_step = QLineEdit("")
        self.pk_ytick_step.setPlaceholderText("auto")
        self.pk_ytick_step.setMaximumWidth(60)
        tick_layout.addWidget(self.pk_ytick_step)
        tick_layout.addWidget(QLabel("Tick size"))
        self.pk_tick_fs = QLineEdit("")
        self.pk_tick_fs.setPlaceholderText("auto")
        self.pk_tick_fs.setMaximumWidth(60)
        tick_layout.addWidget(self.pk_tick_fs)
        additional_layout.addWidget(tick_frame)

        # Assemble controls panel
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(0,0,0,0)
        panel_layout.setSpacing(5)
        panel_layout.addWidget(top_panel)
        panel_layout.addWidget(self.peak_var_controls_frame)
        panel_layout.addWidget(middle_panel)
        panel_layout.addWidget(additional_panel)

        # Figure in splitter for larger plot (50/50 split)
        self.peak_location_figure = Figure(figsize=(12, 8))
        self.peak_location_canvas = FigureCanvas(self.peak_location_figure)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(panel_widget)
        splitter.addWidget(self.peak_location_canvas)
        splitter.setSizes([400, 400])  # 50/50 split instead of 300/900
        layout.addWidget(splitter)

        # Wire variable group to rebuild controls
        self.peak_variable_group.buttonClicked.connect(self.update_peak_parameter_controls)
        self.update_peak_parameter_controls()
        
        # Populate twist checkboxes
        self._populate_twist_checkboxes('peak')

        self.tab_widget.addTab(tab, "Peak Location")

    def update_peak_parameter_controls(self):
        """Refresh per-value controls for Peak tab to mirror Mean Force selection behavior."""
        if not hasattr(self, 'peak_var_controls_layout') or self.peak_var_controls_layout is None:
            return
        try:
            while self.peak_var_controls_layout.count():
                item = self.peak_var_controls_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        except RuntimeError:
            return
        self.peak_parameter_controls = {}
        if not self.data or 'experiments' not in self.data:
            return
        # Fixed label + values
        if self.peak_flow_radio.isChecked():
            self.peak_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s")
            values = self.get_available_flow_values(); label_name = 'flow'
        elif self.peak_sweep_radio.isChecked():
            self.peak_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s")
            values = self.get_available_sweep_values(); label_name = 'sweep'
        # No phase overlap mode for Power stroke data
        markers = ["o","s","^","v","D","p","*","h","X","+"]
        for i, value in enumerate(sorted(values)):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(6,2,6,4)
            row.setSpacing(10)
            txt = f"{value:.2f}" if isinstance(value,(int,float)) else str(value)
            lab = QLabel(f"{label_name.title()}: {txt}")
            lab.setMinimumWidth(140)
            row.addWidget(lab)
            row.addWidget(QLabel("Marker:"))
            mc = QComboBox(); mc.addItems(markers); mc.setCurrentText(markers[i % len(markers)])
            row.addWidget(mc)
            tg = QCheckBox("Show"); tg.setChecked(True)
            row.addWidget(tg)
            row.addStretch()
            self.peak_var_controls_layout.addWidget(row_widget)
            self.peak_parameter_controls[value] = {'marker': mc, 'toggle': tg}
        # Populate twist checkboxes
        self._populate_twist_checkboxes(target='peak')
        
    def create_vector_tab(self):
        """Create the vector tab - selection like Mean/Peak; color by twist; style by variable."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Compact top controls panel
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)

        # Variable Selection (compact horizontal)
        var_frame = QGroupBox("Variable Selection")
        var_layout = QHBoxLayout(var_frame)
        var_layout.setContentsMargins(5, 5, 5, 5)
        self.vec_variable_group = QButtonGroup()
        self.vec_flow_radio = QRadioButton("Flow")
        self.vec_sweep_radio = QRadioButton("Sweep")
        self.vec_variable_group.addButton(self.vec_flow_radio, 0)
        self.vec_variable_group.addButton(self.vec_sweep_radio, 1)
        self.vec_flow_radio.setChecked(True)
        var_layout.addWidget(self.vec_flow_radio)
        var_layout.addWidget(self.vec_sweep_radio)
        # No overlap in Power stroke
        top_layout.addWidget(var_frame)

        # Fixed params label (compact)
        vec_fixed = QGroupBox("Fixed Parameters")
        vec_fixed_layout = QHBoxLayout(vec_fixed)
        vec_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.vec_fixed_params_label = QLabel("Flow: Variable | Sweep: 80° | Period: 2.25s")
        vec_fixed_layout.addWidget(self.vec_fixed_params_label)
        top_layout.addWidget(vec_fixed)

        # Plot controls (compact horizontal)
        plot_control_frame = QGroupBox("Plot Control Panel")
        plot_control_layout = QHBoxLayout(plot_control_frame)
        plot_control_layout.setContentsMargins(5, 5, 5, 5)
        self.plot_vector_button = QPushButton("Plot Vector")
        self.plot_vector_button.clicked.connect(self.plot_vector)
        self.plot_vector_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; font-weight: bold; }")
        plot_control_layout.addWidget(self.plot_vector_button)
        plot_control_layout.addWidget(QLabel("Arrow LW"))
        self.vec_arrow_lw = QLineEdit("1.5")
        self.vec_arrow_lw.setMaximumWidth(50)
        plot_control_layout.addWidget(self.vec_arrow_lw)
        plot_control_layout.addWidget(QLabel("Head W"))
        self.vec_head_w = QLineEdit("0.01")
        self.vec_head_w.setMaximumWidth(50)
        plot_control_layout.addWidget(self.vec_head_w)
        plot_control_layout.addWidget(QLabel("Head L"))
        self.vec_head_l = QLineEdit("0.02")
        self.vec_head_l.setMaximumWidth(50)
        plot_control_layout.addWidget(self.vec_head_l)
        top_layout.addWidget(plot_control_frame)
        
        # Twist selection (checkbox row)
        self.vec_twist_box = QGroupBox("Twists")
        self.vec_twist_layout = QHBoxLayout(self.vec_twist_box)
        self.vec_twist_layout.setContentsMargins(5, 5, 5, 5)
        self.vec_twist_checks = {}
        top_layout.addWidget(self.vec_twist_box)

        # Variable Parameter Controls (style toggle)
        self.vec_var_controls_frame = QGroupBox("Variable Parameter Controls")
        self.vec_var_controls_layout = QVBoxLayout(self.vec_var_controls_frame)
        self.vec_var_controls_layout.setContentsMargins(5, 5, 5, 5)
        self.vec_parameter_controls = {}

        # Compact middle controls panel
        middle_panel = QWidget()
        middle_layout = QHBoxLayout(middle_panel)
        middle_layout.setContentsMargins(5, 5, 5, 5)
        middle_layout.setSpacing(10)

        # Publish controls (compact)
        pub_frame = QGroupBox("Publish")
        pub_layout = QHBoxLayout(pub_frame)
        pub_layout.setContentsMargins(5, 5, 5, 5)
        pub_layout.addWidget(QLabel("W(px)"))
        self.vec_pub_w = QLineEdit("1200")
        self.vec_pub_w.setMaximumWidth(60)
        pub_layout.addWidget(self.vec_pub_w)
        pub_layout.addWidget(QLabel("H(px)"))
        self.vec_pub_h = QLineEdit("800")
        self.vec_pub_h.setMaximumWidth(60)
        pub_layout.addWidget(self.vec_pub_h)
        pub_layout.addWidget(QLabel("Name"))
        self.vec_pub_name = QLineEdit("Vector_plot.png")
        self.vec_pub_name.setMaximumWidth(150)
        pub_layout.addWidget(self.vec_pub_name)
        vec_pub_button = QPushButton("Publish PNG")
        vec_pub_button.clicked.connect(self.publish_vector_figure)
        pub_layout.addWidget(vec_pub_button)
        middle_layout.addWidget(pub_frame)

        # Title controls
        title_frame = QGroupBox("Title")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(5, 5, 5, 5)
        self.v_title_on = QCheckBox("Title")
        title_layout.addWidget(self.v_title_on)
        self.v_title_text = QLineEdit("")
        self.v_title_text.setPlaceholderText("auto")
        self.v_title_text.setMaximumWidth(150)
        title_layout.addWidget(self.v_title_text)
        middle_layout.addWidget(title_frame)

        # X Label controls
        xlabel_frame = QGroupBox("X Label")
        xlabel_layout = QHBoxLayout(xlabel_frame)
        xlabel_layout.setContentsMargins(5, 5, 5, 5)
        self.v_xlabel_on = QCheckBox("X Label")
        xlabel_layout.addWidget(self.v_xlabel_on)
        self.v_xlabel_text = QLineEdit("Mean Thrust (N)")
        self.v_xlabel_text.setMaximumWidth(150)
        xlabel_layout.addWidget(self.v_xlabel_text)
        middle_layout.addWidget(xlabel_frame)

        # Y Label controls
        ylabel_frame = QGroupBox("Y Label")
        ylabel_layout = QHBoxLayout(ylabel_frame)
        ylabel_layout.setContentsMargins(5, 5, 5, 5)
        self.v_ylabel_on = QCheckBox("Y Label")
        ylabel_layout.addWidget(self.v_ylabel_on)
        self.v_ylabel_text = QLineEdit("Mean Lift (N)")
        self.v_ylabel_text.setMaximumWidth(150)
        ylabel_layout.addWidget(self.v_ylabel_text)
        middle_layout.addWidget(ylabel_frame)

        # Axes and controls (compact horizontal)
        axes_frame = QGroupBox("Axes and Controls")
        axes_layout = QHBoxLayout(axes_frame)
        axes_layout.setContentsMargins(5, 5, 5, 5)
        axes_layout.addWidget(QLabel("X min"))
        self.v_xmin = QLineEdit("")
        self.v_xmin.setPlaceholderText("auto")
        self.v_xmin.setMaximumWidth(60)
        axes_layout.addWidget(self.v_xmin)
        axes_layout.addWidget(QLabel("X max"))
        self.v_xmax = QLineEdit("")
        self.v_xmax.setPlaceholderText("auto")
        self.v_xmax.setMaximumWidth(60)
        axes_layout.addWidget(self.v_xmax)
        axes_layout.addWidget(QLabel("Y min"))
        self.v_ymin = QLineEdit("")
        self.v_ymin.setPlaceholderText("auto")
        self.v_ymin.setMaximumWidth(60)
        axes_layout.addWidget(self.v_ymin)
        axes_layout.addWidget(QLabel("Y max"))
        self.v_ymax = QLineEdit("")
        self.v_ymax.setPlaceholderText("auto")
        self.v_ymax.setMaximumWidth(60)
        axes_layout.addWidget(self.v_ymax)
        axes_layout.addWidget(QLabel("Tick font"))
        self.v_tick_font = QComboBox()
        self.v_tick_font.addItems(['Default','DejaVu Sans','Arial','Calibri','Times New Roman','Helvetica'])
        self.v_tick_font.setMaximumWidth(100)
        axes_layout.addWidget(self.v_tick_font)
        self.v_grid_on = QCheckBox("Grid")
        self.v_grid_on.setChecked(True)
        axes_layout.addWidget(self.v_grid_on)
        middle_layout.addWidget(axes_frame)

        # Assemble controls panel
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(0,0,0,0)
        panel_layout.setSpacing(5)
        panel_layout.addWidget(top_panel)
        panel_layout.addWidget(self.vec_var_controls_frame)
        panel_layout.addWidget(middle_panel)

        # Create matplotlib figure for vector plot in splitter (50/50 split)
        self.vector_figure = Figure(figsize=(12, 8))
        self.vector_canvas = FigureCanvas(self.vector_figure)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(panel_widget)
        splitter.addWidget(self.vector_canvas)
        splitter.setSizes([400, 400])  # 50/50 split instead of 300/900
        layout.addWidget(splitter)
        
        # Wire variable group
        self.vec_variable_group.buttonClicked.connect(self.update_vec_parameter_controls)
        self.update_vec_parameter_controls()
        self.tab_widget.addTab(tab, "Vector Plot")

    def update_vec_parameter_controls(self):
        if not hasattr(self, 'vec_var_controls_layout') or self.vec_var_controls_layout is None:
            return
        try:
            while self.vec_var_controls_layout.count():
                item = self.vec_var_controls_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        except RuntimeError:
            return
        self.vec_parameter_controls = {}
        if not self.data or 'experiments' not in self.data:
            return
        if self.vec_flow_radio.isChecked():
            self.vec_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s")
            values = self.get_available_flow_values(); label_name = 'flow'
        elif self.vec_sweep_radio.isChecked():
            self.vec_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s")
            values = self.get_available_sweep_values(); label_name = 'sweep'
        # No phase overlap mode for Power stroke data
        linestyles = ['-','--','-.',':']
        for i, value in enumerate(sorted(values)):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(6,2,6,4)
            row.setSpacing(10)
            txt = f"{value:.2f}" if isinstance(value,(int,float)) else str(value)
            lab = QLabel(f"{label_name.title()}: {txt}")
            lab.setMinimumWidth(140)
            row.addWidget(lab)
            row.addWidget(QLabel("Line:"))
            style = QComboBox(); style.addItems(linestyles); style.setCurrentText(linestyles[i % len(linestyles)])
            row.addWidget(style)
            tg = QCheckBox("Show"); tg.setChecked(True)
            row.addWidget(tg)
            row.addStretch()
            self.vec_var_controls_layout.addWidget(row_widget)
            self.vec_parameter_controls[value] = {'style': style, 'toggle': tg}
        # Populate twist checkboxes
        self._populate_twist_checkboxes(target='vec')
        
    def create_mean_overview_tab(self):
        """Create the Mean Overview tab with decoupled data selection"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Variable Selection
        var_frame = QGroupBox("Variable Selection")
        var_layout = QVBoxLayout(var_frame)
        
        self.variable_group = QButtonGroup()
        self.flow_radio = QRadioButton("Flow")
        self.sweep_radio = QRadioButton("Sweep") 
        
        self.variable_group.addButton(self.flow_radio, 0)
        self.variable_group.addButton(self.sweep_radio, 1)
        
        self.flow_radio.setChecked(True)  # Default to Flow
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.flow_radio)
        radio_layout.addWidget(self.sweep_radio)
        # No overlap in Power stroke
        radio_layout.addStretch()
        var_layout.addLayout(radio_layout)
        
        # Connect radio buttons to update parameter controls
        self.variable_group.buttonClicked.connect(self.update_parameter_controls)
        
        layout.addWidget(var_frame)
        
        # Fixed Parameters Display
        fixed_frame = QGroupBox("Fixed Parameters")
        fixed_layout = QHBoxLayout(fixed_frame)
        
        self.fixed_params_label = QLabel("Flow: 0.1 | Sweep: 80° | Period: 2.25s")
        fixed_layout.addWidget(self.fixed_params_label)
        fixed_layout.addStretch()
        
        layout.addWidget(fixed_frame)
        
        # Variable Parameter Controls
        self.var_controls_frame = QGroupBox("Variable Parameter Controls")
        self.var_controls_layout = QVBoxLayout(self.var_controls_frame)
        
        # This will be populated dynamically based on variable selection
        self.parameter_controls = {}  # Store controls for each parameter value
        
        layout.addWidget(self.var_controls_frame)
        
        # Plot Controls
        plot_frame = QGroupBox("Plot Controls")
        plot_layout = QVBoxLayout(plot_frame)
        
        # Channel selection
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        self.mean_channel_combo = QComboBox()
        self.mean_channel_combo.addItems(["Thrust", "Lift"])
        channel_layout.addWidget(self.mean_channel_combo)
        channel_layout.addStretch()
        plot_layout.addLayout(channel_layout)
        
        # Plot and export buttons
        button_layout = QHBoxLayout()
        plot_button = QPushButton("Plot Mean Overview")
        plot_button.clicked.connect(self.plot_mean_overview)
        button_layout.addWidget(plot_button)
        
        export_png_button = QPushButton("Export PNG")
        export_png_button.clicked.connect(self.export_mean_overview_png)
        button_layout.addWidget(export_png_button)
        
        export_pdf_button = QPushButton("Export PDF")
        export_pdf_button.clicked.connect(self.export_mean_overview_pdf)
        button_layout.addWidget(export_pdf_button)
        
        button_layout.addStretch()
        plot_layout.addLayout(button_layout)
        
        layout.addWidget(plot_frame)
        
        # Matplotlib figure
        self.mean_figure = Figure(figsize=(10, 6), dpi=100)
        self.mean_ax = self.mean_figure.add_subplot(111)
        self.mean_ax.grid(True, alpha=0.3)
        self.mean_canvas = FigureCanvas(self.mean_figure)
        layout.addWidget(self.mean_canvas)
        
        # Initialize parameter controls
        self.update_parameter_controls()
        
        return tab
        
    def update_parameter_controls(self):
        """Update parameter controls based on selected variable"""
        # Check if the layout still exists
        if not hasattr(self, 'var_controls_layout') or self.var_controls_layout is None:
            return
            
        # Clear existing controls safely
        try:
            while self.var_controls_layout.count():
                child = self.var_controls_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except RuntimeError:
            # Layout has been deleted, skip clearing
            pass
        
        self.parameter_controls = {}
        
        if not self.data or 'experiments' not in self.data:
            return
            
        # Check if radio buttons exist
        if not hasattr(self, 'flow_radio') or self.flow_radio is None:
            return
            
        # Get available parameter values based on selected variable
        if self.flow_radio.isChecked():
            # Flow mode: show flow values, fixed sweep=80, period=2.25
            self.fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s")
            param_values = self.get_available_flow_values()
            param_name = "flow"
        elif self.sweep_radio.isChecked():
            # Sweep mode: show sweep values, fixed flow=0.1, period=2.25
            self.fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s")
            param_values = self.get_available_sweep_values()
            param_name = "sweep"
        # No phase overlap mode for Power stroke data
        
        # Create controls for each parameter value
        markers = ["o", "s", "^", "v", "D", "p", "*", "h", "X", "+"]
        
        for i, value in enumerate(sorted(param_values)):
            row_widget = QWidget()
            control_layout = QHBoxLayout(row_widget)
            control_layout.setContentsMargins(6, 2, 6, 4)
            control_layout.setSpacing(10)
            
            # Parameter value label (fixed/min width to avoid overlap)
            val_text = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
            label = QLabel(f"{param_name.title()}: {val_text}")
            label.setMinimumWidth(140)
            control_layout.addWidget(label)
            
            # Marker style
            marker_label = QLabel("Marker:")
            control_layout.addWidget(marker_label)
            marker_combo = QComboBox()
            marker_combo.addItems(markers)
            marker_combo.setCurrentText(markers[i % len(markers)])
            control_layout.addWidget(marker_combo)
            
            # Toggle checkbox
            toggle_checkbox = QCheckBox("Show")
            toggle_checkbox.setChecked(True)
            control_layout.addWidget(toggle_checkbox)
            
            control_layout.addStretch()
            
            # Store controls
            self.parameter_controls[value] = {
                'marker': marker_combo,
                'toggle': toggle_checkbox
            }
            
            self.var_controls_layout.addWidget(row_widget)
        
    def get_available_flow_values(self):
        """Get available flow values (normalized), keeping other dims at common settings."""
        flow_values = set()
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['sweep'] - 80) < 1e-6 and
                abs(m['stroke_period'] - 2.25) < 1e-6):
                flow_values.add(m['flow'])
        return flow_values
        
    def get_available_sweep_values(self):
        """Get available sweep values with strict parameter control (flow=0.1, period=2.25)"""
        sweep_values = set()
        
        # Debug: Print all available parameter combinations
        print("DEBUG: All available parameter combinations:")
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            print(f"  {exp_key}: flow={m['flow']}, sweep={m['sweep']}, period={m['stroke_period']}")
        
        # Only look for experiments with ideal settings: flow=0.1, period=2.25
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['flow'] - 0.1) < 1e-6 and
                abs(m['stroke_period'] - 2.25) < 1e-6):
                sweep_values.add(m['sweep'])
        
        print(f"DEBUG: Found {len(sweep_values)} sweep values with ideal settings: {sweep_values}")
        
        return sweep_values
        
    # No phase overlap method for Power stroke data
        
    def plot_mean_overview(self):
        """Plot mean overview with windowed means vs roll angle using new data selection"""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return
            
        # Clear previous plot
        self.mean_ax.clear()
        
        # Get selected channel
        channel = self.mean_channel_combo.currentText().lower()
        
        # Get selected variable type
        if self.flow_radio.isChecked():
            variable_type = "flow"
        elif self.sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "overlap"
        
        # Collect data for each enabled parameter value
        plot_data = {}
        
        for param_value, controls in self.parameter_controls.items():
            if not controls['toggle'].isChecked():
                continue
                
            marker = controls['marker'].currentText()
            
            # Find experiments matching this parameter value
            experiments = self.get_experiments_for_parameter(variable_type, param_value)
            
            if not experiments:
                continue
                
            # Calculate windowed means for each experiment (fixed normalization [0.75,2.25]→[0,1])
            twist_values = []
            mean_values = []
            
            for exp_key in experiments:
                exp_data = self.data['experiments'][exp_key]
                params = exp_data['parameters']
                
                # Get twist (roll angle) value
                twist = abs(params.get('twist', 0))
                
                # Get time series data
                time_vector = exp_data.get('time_vector', [])
                if channel == 'thrust':
                    force_data = exp_data.get('thrust_mean', [])
                else:
                    force_data = exp_data.get('lift_mean', [])
                
                if len(time_vector) == 0 or len(force_data) == 0:
                    continue
                
                # Fixed normalization and mask
                time_array = np.asarray(time_vector)
                # No normalization or windowing
                window_force = np.asarray(force_data)
                mean_force = float(np.mean(window_force)) if window_force.size > 0 else np.nan
                
                twist_values.append(twist)
                mean_values.append(mean_force)
            
            if twist_values and mean_values:
                plot_data[param_value] = {
                    'twist': twist_values,
                    'mean': mean_values,
                    'marker': marker
                }
        
        # Plot the data
        for param_value, data in plot_data.items():
            self.mean_ax.scatter(data['twist'], data['mean'], 
                               marker=data['marker'], 
                               s=50, 
                               color='black',
                               label=f"{variable_type.title()} {param_value}")
        
        # Set labels and title
        self.mean_ax.set_xlabel('Absolute Roll Angle (Twist) [degrees]')
        self.mean_ax.set_ylabel(f'Mean {channel.title()} Force [N]')
        self.mean_ax.set_title(f'Mean {channel.title()} vs Roll Angle')
        self.mean_ax.grid(True, alpha=0.3)
        self.mean_ax.legend()
        
        # Set x-axis range to 0-90 degrees
        self.mean_ax.set_xlim(0, 90)
        
        # Refresh canvas
        self.mean_canvas.draw()
        
    def get_experiments_for_parameter(self, variable_type, param_value, fixed_params=None):
        """Get experiments matching the specified parameter value with optional fixed parameter constraints"""
        matching_experiments = []
        
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            
            # Apply fixed parameter constraints if provided
            if fixed_params:
                if 'sweep' in fixed_params and abs(m['sweep'] - fixed_params['sweep']) > 1e-6:
                    continue
                if 'period' in fixed_params and abs(m['stroke_period'] - fixed_params['period']) > 1e-6:
                    continue
                if 'flow' in fixed_params and abs(m['flow'] - fixed_params['flow']) > 1e-6:
                    continue
                if 'twist' in fixed_params and abs(m['twist'] - fixed_params['twist']) > 1e-6:
                    continue
            
            # Match the variable parameter
            if variable_type == "flow":
                if abs(m['flow'] - float(param_value)) < 1e-6:
                    matching_experiments.append(exp_key)
            elif variable_type == "sweep":
                if abs(m['sweep'] - float(param_value)) < 1e-6:
                    matching_experiments.append(exp_key)
            elif variable_type == "twist":
                if abs(m['twist'] - float(param_value)) < 1e-6:
                    matching_experiments.append(exp_key)
            elif variable_type == "period":
                if abs(m['stroke_period'] - float(param_value)) < 1e-6:
                    matching_experiments.append(exp_key)
        
        return matching_experiments
        
    def export_mean_overview_png(self):
        """Export mean overview plot as PNG"""
        if hasattr(self, 'mean_figure'):
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Mean Overview as PNG", 
                "mean_overview.png", "PNG files (*.png)")
            if filename:
                self.mean_figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Export Complete", f"Plot saved to {filename}")
                
    def export_mean_overview_pdf(self):
        """Export mean overview plot as PDF"""
        if hasattr(self, 'mean_figure'):
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Mean Overview as PDF", 
                "mean_overview.pdf", "PDF files (*.pdf)")
            if filename:
                self.mean_figure.savefig(filename, bbox_inches='tight')
                QMessageBox.information(self, "Export Complete", f"Plot saved to {filename}")
            
        # Get selected experiments from the traces tab
        selected_experiments = self.get_selected_experiments()
        if not selected_experiments:
            QMessageBox.warning(self, "No Selection", "Please select experiments in the Trial Traces tab")
            return
            
        channel = self.mean_overview_channel.currentText().lower()
        
        # Clear previous plot
        self.mean_overview_figure.clear()
        ax = self.mean_overview_figure.add_subplot(111)
        
        # Prepare data for plotting
        roll_angles = []
        mean_forces = []
        flow_speeds = []
        periods = []
        
        # Compute windowed means for each selected experiment
        for exp_key in selected_experiments:
            if exp_key in self.data['experiments']:
                exp_data = self.data['experiments'][exp_key]
                
                # Get the appropriate trace data
                if channel == 'thrust':
                    trace = exp_data.get('thrust_mean', [])
                else:  # lift
                    trace = exp_data.get('lift_mean', [])
                
                time_vector = exp_data.get('time_vector', [])
                
                if len(trace) > 0 and len(time_vector) > 0:
                    # Use absolute time directly; no normalization or masking
                    windowed_trace = np.asarray(trace)
                    windowed_time = np.asarray(time_vector)
                    
                    # Compute arithmetic mean over the full trace
                    mean_force = float(np.mean(windowed_trace)) if len(windowed_trace) > 0 else np.nan

                    # Get experiment parameters
                    params = exp_data.get('parameters', {})
                    roll_angle = abs(params.get('twist', 0))  # Absolute value for x-axis
                    flow = params.get('flow', 0)
                    period = params.get('period', 0)

                    # Store data
                    roll_angles.append(roll_angle)
                    mean_forces.append(mean_force)
                    flow_speeds.append(flow)
                    periods.append(period)
        
        if not roll_angles:
            QMessageBox.warning(self, "No Data", "No valid data found for plotting")
            return
        
        # Convert to numpy arrays
        import numpy as np
        roll_angles = np.array(roll_angles)
        mean_forces = np.array(mean_forces)
        flow_speeds = np.array(flow_speeds)
        periods = np.array(periods)
        
        # Create scatter plot
        scatter = ax.scatter(roll_angles, mean_forces, 
                           c=flow_speeds, 
                           cmap=self.mean_overview_color.currentText(),
                           marker=self.mean_overview_marker.currentText(),
                           s=100, alpha=0.7)
        
        # Add colorbar
        cbar = self.mean_overview_figure.colorbar(scatter, ax=ax)
        cbar.set_label('Flow Speed')
        
        # Set labels and title
        ax.set_xlabel('Roll Angle (Twist) [degrees]')
        ax.set_ylabel(f'Mean {channel.capitalize()} Force')
        ax.set_title(f'Mean {channel.capitalize()} Force vs Roll Angle (Twist)')
        ax.grid(True, alpha=0.3)
        
        # Set x-axis range to 0-90
        ax.set_xlim(0, 90)
        
        # Add legend with period information
        unique_periods = np.unique(periods)
        for period in unique_periods:
            mask = periods == period
            ax.scatter([], [], c='gray', marker=self.mean_overview_marker.currentText(), 
                      s=100, alpha=0.7, label=f'Period: {period:.2f}')
        ax.legend()
        
        self.mean_overview_canvas.draw()
        
    def plot_mean_force(self):
        """Plot mean force using decoupled variable selection (black markers)"""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return
        
        channel = self.mean_force_channel.currentText().lower()
        
        # Determine variable type
        if hasattr(self, 'mean_force_flow_radio') and self.mean_force_flow_radio.isChecked():
            variable_type = "flow"
        elif hasattr(self, 'mean_force_sweep_radio') and self.mean_force_sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "flow"
        
        # Clear previous plot
        self.mean_force_figure.clear()
        ax = self.mean_force_figure.add_subplot(111)
        
        # Build selected twist set from checkboxes (if any)
        selected_twists = self._get_selected_twists('mean')

        # Get fixed parameters based on variable type (hardcoded like in the UI)
        fixed_params = {}
        if variable_type == "flow":
            # Flow mode: fixed sweep=80, period=2.25
            fixed_params = {'sweep': 80.0, 'period': 2.25}
        elif variable_type == "sweep":
            # Sweep mode: fixed flow=0.1, period=2.25
            fixed_params = {'flow': 0.1, 'period': 2.25}

        # Collect and plot for each enabled parameter value
        for param_value, controls in self.mean_force_parameter_controls.items():
            if not controls['toggle'].isChecked():
                continue
            marker = controls['marker'].currentText()
            
            experiments = self.get_experiments_for_parameter(variable_type, param_value, fixed_params)
            if not experiments:
                continue
            
            twist_values = []
            mean_values = []
            baseline_indices = []
            
            for i, exp_key in enumerate(experiments):
                exp_data = self.data['experiments'][exp_key]
                params = exp_data['parameters']
                twist = abs(params.get('twist', 0))
                if selected_twists is not None and twist not in selected_twists:
                    continue
                
                time_vector = exp_data.get('time_vector', [])
                if channel == 'thrust':
                    force_data = exp_data.get('thrust_mean', [])
                else:
                    force_data = exp_data.get('lift_mean', [])
                if len(time_vector) == 0 or len(force_data) == 0:
                    continue
                
                # Compute mean across full absolute-time trace
                force_array = np.asarray(force_data)
                window_force = force_array
                mean_force = float(np.mean(window_force)) if window_force.size > 0 else np.nan
                
                # Check if this is a baseline experiment
                flow = params.get('flow', 0)
                period = params.get('period', 0)
                sweep = params.get('sweep', 0)
                if self._is_baseline_experiment(flow, period, sweep, twist):
                    baseline_indices.append(len(twist_values))
                
                twist_values.append(twist)
                mean_values.append(mean_force)
            
            if twist_values and mean_values:
                # Color points by twist using the global twist color map (consistent across tabs)
                colors = [self.twist_color_map.get(tw, (0.2, 0.2, 0.2, 1.0)) for tw in twist_values]
                def _pf(s, d):
                    try: return float(s)
                    except: return d
                size = _pf(self.mf_marker_size.text(), 50.0) if hasattr(self, 'mf_marker_size') else 50.0
                ecolor = self.mf_marker_edge_color.text().strip() if hasattr(self, 'mf_marker_edge_color') else '#000000'
                if ecolor and not ecolor.startswith('#'):
                    ecolor = '#' + ecolor
                ewidth = _pf(self.mf_marker_edge_width.text(), 0.4) if hasattr(self, 'mf_marker_edge_width') else 0.4
                
                # Apply baseline styling to baseline experiments
                if baseline_indices:
                    # Create separate arrays for baseline and non-baseline points
                    baseline_twist = [twist_values[i] for i in baseline_indices]
                    baseline_mean = [mean_values[i] for i in baseline_indices]
                    baseline_colors = [colors[i] for i in baseline_indices]
                    
                    non_baseline_twist = [twist_values[i] for i in range(len(twist_values)) if i not in baseline_indices]
                    non_baseline_mean = [mean_values[i] for i in range(len(mean_values)) if i not in baseline_indices]
                    non_baseline_colors = [colors[i] for i in range(len(colors)) if i not in baseline_indices]
                    
                    # Plot non-baseline points first
                    if non_baseline_twist and non_baseline_mean:
                        ax.scatter(non_baseline_twist, non_baseline_mean, marker=marker, s=size, c=non_baseline_colors,
                                   edgecolors=ecolor, linewidths=ewidth,
                                   label=f"{variable_type.title()} {param_value}")
                    
                    # Plot baseline points with special styling
                    if baseline_twist and baseline_mean:
                        baseline_color = self.baseline_color if self.baseline_color.startswith('#') else '#' + self.baseline_color
                        ax.scatter(baseline_twist, baseline_mean, marker=marker, s=size*1.5, c=baseline_color,
                                   edgecolors='black', linewidths=ewidth*2,
                                   label=f"{variable_type.title()} {param_value} (Baseline)")
                else:
                    # No baseline experiments, plot normally
                    ax.scatter(twist_values, mean_values, marker=marker, s=size, c=colors,
                               edgecolors=ecolor, linewidths=ewidth,
                               label=f"{variable_type.title()} {param_value}")
        
        ax.set_xlabel('Absolute Roll Angle (Twist) [degrees]')
        ax.set_ylabel(f'Mean {channel.title()} Force [N]')
        ax.set_title(f'Mean {channel.title()} vs Roll Angle')
        ax.grid(self.mf_grid_on.isChecked(), alpha=0.3)
        # Axis limits (if provided)
        def _to_float(s):
            try:
                return float(s)
            except Exception:
                return None
        xmin = _to_float(self.mf_xmin.text())
        xmax = _to_float(self.mf_xmax.text())
        ymin = _to_float(self.mf_ymin.text())
        ymax = _to_float(self.mf_ymax.text())
        if xmin is not None or xmax is not None:
            # start from requested range; if both provided and equal, expand slightly
            if xmin is not None and xmax is not None:
                new_min, new_max = xmin, xmax
            else:
                xr = list(ax.get_xlim())
                new_min = xmin if xmin is not None else xr[0]
                new_max = xmax if xmax is not None else xr[1]
            if new_max <= new_min:
                new_max = new_min + max(1.0, abs(new_min) * 0.05 + 1e-6)
            ax.set_xlim(new_min, new_max)
        if ymin is not None or ymax is not None:
            yr = list(ax.get_ylim())
            new_min = ymin if ymin is not None else yr[0]
            new_max = ymax if ymax is not None else yr[1]
            if new_max <= new_min:
                new_max = new_min + 1.0
            ax.set_ylim(new_min, new_max)
        # Labels (toggle logic: empty text = no label)
        if self.mf_title_on.isChecked():
            ttl = self.mf_title_text.text().strip()
            if ttl:
                ax.set_title(ttl)
            else:
                ax.set_title("")
        else:
            ax.set_title("")
        
        if self.mf_xlabel_on.isChecked():
            xl = self.mf_xlabel_text.text().strip()
            if xl:
                ax.set_xlabel(xl)
            else:
                ax.set_xlabel("")
        else:
            ax.set_xlabel("")
            
        if self.mf_ylabel_on.isChecked():
            yl = self.mf_ylabel_text.text().strip()
            if yl:
                ax.set_ylabel(yl)
            else:
                ax.set_ylabel("")
        else:
            ax.set_ylabel("")
        # Tick steps and fonts
        def _pf(s, default=None):
            try:
                return float(s)
            except Exception:
                return default
        
        # X ticks format parsing (start:step:end)
        xticks_text = self.mf_xticks_text.text().strip()
        if xticks_text:
            parts = xticks_text.split(':')
            if len(parts) == 3:
                try:
                    start, step, end = float(parts[0]), float(parts[1]), float(parts[2])
                    xticks = np.arange(start, end + step/2, step)
                    ax.set_xticks(xticks)
                except ValueError:
                    pass  # Invalid format, use default
        
        ystep = _pf(self.mf_ytick_step.text())
        if ystep and ystep > 0:
            ymin_cur, ymax_cur = ax.get_ylim()
            ax.set_yticks(np.arange(ymin_cur, ymax_cur + 0.5 * ystep, ystep))
        tick_fs = _pf(self.mf_tick_fs.text())
        if tick_fs:
            ax.tick_params(labelsize=tick_fs)
        # Legend
        if self.mf_legend_on.isChecked():
            ax.legend(loc=self.mf_legend_loc.currentText())
        
        self.mean_force_canvas.draw()

    def update_mean_force_parameter_controls(self):
        """Populate per-value controls for Mean Force tab based on selected variable"""
        print("DEBUG: update_mean_force_parameter_controls called")
        
        # Guard for layout existence
        if not hasattr(self, 'mean_force_var_controls_layout') or self.mean_force_var_controls_layout is None:
            print("DEBUG: Layout not found, returning")
            return
        # Clear existing child widgets safely
        try:
            while self.mean_force_var_controls_layout.count():
                child = self.mean_force_var_controls_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except RuntimeError:
            return
        
        self.mean_force_parameter_controls = {}
        
        if not self.data or 'experiments' not in self.data:
            print("DEBUG: No data available, returning")
            return
        
        # Determine variable and fixed label
        if self.mean_force_flow_radio.isChecked():
            print("DEBUG: Flow radio button is checked")
            self.mean_force_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s")
            values = self.get_available_flow_values()
            label_name = "flow"
        elif self.mean_force_sweep_radio.isChecked():
            print("DEBUG: Sweep radio button is checked")
            self.mean_force_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s")
            values = self.get_available_sweep_values()
            label_name = "sweep"
        # No phase overlap mode for Power stroke data
        
        print(f"DEBUG: Found {len(values)} {label_name} values: {values}")
        
        markers = ["o", "s", "^", "v", "D", "p", "*", "h", "X", "+"]
        for i, value in enumerate(sorted(values)):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(6, 2, 6, 4)
            row.setSpacing(10)
            val_text = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
            lab = QLabel(f"{label_name.title()}: {val_text}")
            lab.setMinimumWidth(140)
            row.addWidget(lab)
            row.addWidget(QLabel("Marker:"))
            marker_combo = QComboBox()
            marker_combo.addItems(markers)
            marker_combo.setCurrentText(markers[i % len(markers)])
            row.addWidget(marker_combo)
            toggle = QCheckBox("Show")
            toggle.setChecked(True)
            row.addWidget(toggle)
            row.addStretch()
            self.mean_force_var_controls_layout.addWidget(row_widget)
            self.mean_force_parameter_controls[value] = {'marker': marker_combo, 'toggle': toggle}
        
        # Populate twist checkboxes
        self._populate_twist_checkboxes(target='mean')
        
    def plot_peak_location(self):
        """Plot peak location with variable selection; color by twist palette."""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return

        # Determine variable type like Mean Force
        if hasattr(self, 'peak_flow_radio') and self.peak_flow_radio.isChecked():
            variable_type = "flow"
        elif hasattr(self, 'peak_sweep_radio') and self.peak_sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "flow"

        channel = self.peak_location_channel.currentText().lower()

        self.peak_location_figure.clear()
        ax = self.peak_location_figure.add_subplot(111)

        # Build marker controls
        def _marker_for(val):
            ctrl = self.peak_parameter_controls.get(val)
            return ctrl['marker'].currentText() if ctrl else 'o'
        def _enabled(val):
            ctrl = self.peak_parameter_controls.get(val)
            return ctrl and ctrl['toggle'].isChecked()

        # Smoothing helper to stabilize peak detection
        def _smooth_signal(y: np.ndarray, window_size: int = 5) -> np.ndarray:
            try:
                w = int(max(3, min(window_size, (len(y)//10)*2+1)))
            except Exception:
                w = 5
            if w % 2 == 0:
                w += 1
            if w <= 1 or w > len(y):
                return y
            kernel = np.ones(w, dtype=float) / float(w)
            return np.convolve(y, kernel, mode='same')

        # Build an optional comma-separated twist filter text box if not present
        if not hasattr(self, 'peak_twist_filter'):
            try:
                filter_row = QWidget()
                frl = QHBoxLayout(filter_row)
                frl.setContentsMargins(5, 0, 5, 0)
                frl.addWidget(QLabel("Twist filter (deg, comma-separated, optional):"))
                self.peak_twist_filter = QLineEdit("")
                self.peak_twist_filter.setPlaceholderText("e.g. 0,15,30,45,60,75,90")
                self.peak_twist_filter.setMaximumWidth(300)
                frl.addWidget(self.peak_twist_filter)
                frl.addStretch()
                # Insert above the plot? Assume there is a layout available
                # If not available, ignore silently
                if hasattr(self, 'peak_location_controls_frame') and self.peak_location_controls_frame:
                    self.peak_location_controls_frame.layout().addWidget(filter_row)
            except Exception:
                pass

        # Selected twists from checkboxes
        selected_twists = self._get_selected_twists('peak')

        # Get fixed parameters based on variable type (hardcoded like in the UI)
        fixed_params = {}
        if variable_type == "flow":
            # Flow mode: fixed sweep=80, period=2.25
            fixed_params = {'sweep': 80.0, 'period': 2.25}
        elif variable_type == "sweep":
            # Sweep mode: fixed flow=0.1, period=2.25
            fixed_params = {'flow': 0.1, 'period': 2.25}

        # Iterate parameter values selected
        for param_value, ctrl in list(self.peak_parameter_controls.items()):
            if not _enabled(param_value):
                continue
            marker = _marker_for(param_value)
            experiments = self.get_experiments_for_parameter(variable_type, param_value, fixed_params)
            if not experiments:
                continue

            added_label = False
            for exp_key in experiments:
                exp = self.data['experiments'][exp_key]
                m = self._param_map(exp['parameters'])
                # Apply optional twist filter
                if 'twist' in m and selected_twists is not None and m['twist'] not in selected_twists:
                    continue
                t_abs = np.asarray(exp.get('time_vector', []))
                if channel == 'thrust':
                    ysig = np.asarray(exp.get('thrust_mean', []))
                else:
                    ysig = np.asarray(exp.get('lift_mean', []))
                if t_abs.size == 0 or ysig.size == 0:
                    continue
                
                # For paddle stroke: normalize time to [0.4, 1.0] range (paddle portion of full stroke)
                # Map absolute time to normalized time
                period = m.get('period', 2.25)
                if abs(period - 1.75) < 0.1:
                    paddle_window = self.paddle_stroke_windows[1.75]
                elif abs(period - 2.25) < 0.1:
                    paddle_window = self.paddle_stroke_windows[2.25]
                else:
                    paddle_window = self.paddle_stroke_windows[1.75] if period < 2.0 else self.paddle_stroke_windows[2.25]
                
                start_time = paddle_window['start']
                end_time = paddle_window['end']
                
                # Apply paddle stroke window mask
                mask = (t_abs >= start_time) & (t_abs <= end_time)
                if mask.sum() < 3:
                    continue
                
                # Extract windowed data and map to normalized time [0.4, 1.0]
                t_abs_windowed = t_abs[mask]
                y_windowed = ysig[mask]
                t_norm = np.linspace(0.4, 1.0, len(t_abs_windowed))
                
                # Only consider peaks before 0.8 of the full period (exclude last 20%)
                peak_mask = t_norm < 0.8
                if peak_mask.sum() < 3:
                    continue
                
                t_norm_for_peak = t_norm[peak_mask]
                y_for_peak = y_windowed[peak_mask]
                
                # Simple peak detection: max for thrust, min for lift (within paddle stroke window, before t=0.8)
                pts = []
                if channel == 'thrust':
                    # For thrust: find maximum (positive peak)
                    max_idx = np.argmax(y_for_peak)
                    peak_time = float(t_norm_for_peak[max_idx])
                    peak_value = float(y_for_peak[max_idx])
                    pts.append((peak_time, peak_value))
                else:
                    # For lift: find minimum (negative peak)
                    min_idx = np.argmin(y_for_peak)
                    peak_time = float(t_norm_for_peak[min_idx])
                    peak_value = float(y_for_peak[min_idx])
                    pts.append((peak_time, peak_value))

                if len(pts) == 0:
                    continue
                
                # Check if this is a baseline experiment
                flow = m.get('flow', 0)
                period = m.get('period', 0)
                sweep = m.get('sweep', 0)
                twist = m.get('twist', 0)
                is_baseline = self._is_baseline_experiment(flow, period, sweep, twist)
                
                # Apply baseline styling if needed
                if is_baseline:
                    color = self.baseline_color if self.baseline_color.startswith('#') else '#' + self.baseline_color
                    size_multiplier = 1.5
                    ecolor = 'black'
                    ewidth_multiplier = 2.0
                    baseline_suffix = " (Baseline)"
                else:
                    color = self.twist_color_map.get(m['twist'], (0.2,0.2,0.2,1.0))
                    size_multiplier = 1.0
                    ecolor = self.pk_marker_edge_color.text().strip() if hasattr(self, 'pk_marker_edge_color') else '#000000'
                    if ecolor and not ecolor.startswith('#'):
                        ecolor = '#' + ecolor
                    ewidth_multiplier = 1.0
                    baseline_suffix = ""
                
                # plot points with marker style controls
                def _pf(s, d):
                    try: return float(s)
                    except: return d
                size = _pf(self.pk_marker_size.text(), 60.0) if hasattr(self, 'pk_marker_size') else 60.0
                ewidth = _pf(self.pk_marker_edge_width.text(), 0.4) if hasattr(self, 'pk_marker_edge_width') else 0.4
                for j, (px, py) in enumerate(pts):
                    lbl = f"{variable_type.title()} {param_value}{baseline_suffix}" if not added_label and j == 0 else "_nolegend_"
                    ax.scatter(px, py, marker=marker, s=size*size_multiplier, c=[color], 
                               edgecolors=ecolor, linewidths=ewidth*ewidth_multiplier, label=lbl)
                # connect if two points
                if len(pts) == 2:
                    ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color=color, linewidth=1.0, alpha=0.7)
                added_label = True

        # Apply user axes options
        def _f(s):
            try: return float(s)
            except: return None
        xmin = _f(self.pk_xmin.text()); xmax = _f(self.pk_xmax.text())
        ymin = _f(self.pk_ymin.text()); ymax = _f(self.pk_ymax.text())
        if xmin is not None or xmax is not None:
            xr = ax.get_xlim(); ax.set_xlim(xmin if xmin is not None else xr[0], xmax if xmax is not None else xr[1])
        if ymin is not None or ymax is not None:
            yr = ax.get_ylim(); ax.set_ylim(ymin if ymin is not None else yr[0], ymax if ymax is not None else yr[1])
        # Default to normalized x-limits if none provided
        if xmin is None and xmax is None:
            ax.set_xlim(0.0, 1.0)
        
        # Labels (toggle logic: empty text = no label)
        if self.pk_title_on.isChecked():
            ttl = self.pk_title_text.text().strip()
            if ttl:
                ax.set_title(ttl)
            else:
                ax.set_title("")
        else:
            ax.set_title("")
        
        if self.pk_xlabel_on.isChecked():
            xl = self.pk_xlabel_text.text().strip()
            if xl:
                ax.set_xlabel(xl)
            else:
                ax.set_xlabel("")
        else:
            ax.set_xlabel("")
            
        if self.pk_ylabel_on.isChecked():
            yl = self.pk_ylabel_text.text().strip()
            if yl:
                ax.set_ylabel(yl)
            else:
                ax.set_ylabel("")
        else:
            ax.set_ylabel("")
        
        ax.grid(self.pk_grid_on.isChecked(), alpha=0.3)
        
        # Tick steps and fonts
        # X ticks format parsing (start:step:end)
        xticks_text = self.pk_xticks_text.text().strip()
        if xticks_text:
            parts = xticks_text.split(':')
            if len(parts) == 3:
                try:
                    start, step, end = float(parts[0]), float(parts[1]), float(parts[2])
                    xticks = np.arange(start, end + step/2, step)
                    ax.set_xticks(xticks)
                except ValueError:
                    pass  # Invalid format, use default
        
        ystep = _f(self.pk_ytick_step.text())
        if ystep and ystep > 0:
            ymin_cur, ymax_cur = ax.get_ylim(); ax.set_yticks(np.arange(ymin_cur, ymax_cur + 0.5*ystep, ystep))
        ts = _f(self.pk_tick_fs.text())
        if ts:
            ax.tick_params(labelsize=ts)
        if self.pk_legend_on.isChecked():
            ax.legend(loc=self.pk_legend_loc.currentText())
        self.peak_location_canvas.draw()
        
    def plot_vector(self):
        """Plot vector plot with thrust on X-axis and lift on Y-axis using decoupled selection."""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return
        # Variable type
        if self.vec_flow_radio.isChecked():
            variable_type = "flow"
        elif self.vec_sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "flow"
        
        # Clear previous plot
        self.vector_figure.clear()
        ax = self.vector_figure.add_subplot(111)
        
        # Style options
        def _f(s):
            try: return float(s)
            except: return None
        head_w = _f(self.vec_head_w.text()) or 0.08
        head_l = _f(self.vec_head_l.text()) or 0.12
        lw = _f(self.vec_arrow_lw.text()) or 1.5
        # Make line styles more pronounced via explicit dash patterns
        def _style_to_dashes(style: str):
            # Return on/off dash sequence for Line2D.set_dashes
            if style == '--':
                return [10, 6]
            if style == '-.':
                return [10, 5, 2, 5]
            if style == ':':
                return [2, 6]
            return None
        
        # Marker/linestyle by parameter value
        def _enabled(val):
            ctrl = self.vec_parameter_controls.get(val)
            return ctrl and ctrl['toggle'].isChecked()
        def _linestyle(val):
            ctrl = self.vec_parameter_controls.get(val)
            return ctrl['style'].currentText() if ctrl else '-'
        
        # Selected twists from checkboxes
        selected_twists = self._get_selected_twists('vec')

        # Get fixed parameters based on variable type (hardcoded like in the UI)
        fixed_params = {}
        if variable_type == "flow":
            # Flow mode: fixed sweep=80, period=2.25
            fixed_params = {'sweep': 80.0, 'period': 2.25}
        elif variable_type == "sweep":
            # Sweep mode: fixed flow=0.1, period=2.25
            fixed_params = {'flow': 0.1, 'period': 2.25}

        # Iterate values
        for param_value, ctrl in list(self.vec_parameter_controls.items()):
            if not _enabled(param_value):
                continue
            experiments = self.get_experiments_for_parameter(variable_type, param_value, fixed_params)
            if not experiments:
                continue
            ls = _linestyle(param_value)
            for exp_key in experiments:
                exp = self.data['experiments'][exp_key]
                m = self._param_map(exp['parameters'])
                if selected_twists is not None and m.get('twist', 0.0) not in selected_twists:
                    continue
                t_abs = np.asarray(exp.get('time_vector', []))
                thrust = np.asarray(exp.get('thrust_mean', []))
                lift = np.asarray(exp.get('lift_mean', []))
                if t_abs.size == 0 or thrust.size == 0 or lift.size == 0:
                    continue
                period = m['stroke_period']
                # Apply user-defined trimming from normalization tab
                # Use correct window based on period
                if abs(period - 1.75) < 0.1:
                    paddle_window = self.paddle_stroke_windows[1.75]
                elif abs(period - 2.25) < 0.1:
                    paddle_window = self.paddle_stroke_windows[2.25]
                else:
                    paddle_window = self.paddle_stroke_windows[1.75] if period < 2.0 else self.paddle_stroke_windows[2.25]
                
                start_time = paddle_window['start']
                end_time = paddle_window['end']
                mask = (t_abs >= start_time) & (t_abs <= end_time)
                if not np.any(mask):
                    continue
                # Calculate means from user-trimmed data
                mt = float(np.mean(thrust[mask]))
                ml = float(np.mean(lift[mask]))
                
                # Check if this is a baseline experiment
                flow = m.get('flow', 0)
                period = m.get('period', 0)
                sweep = m.get('sweep', 0)
                twist = m.get('twist', 0)
                is_baseline = self._is_baseline_experiment(flow, period, sweep, twist)
                
                # Apply baseline styling if needed
                if is_baseline:
                    color = self.baseline_color if self.baseline_color.startswith('#') else '#' + self.baseline_color
                    linewidth = lw * 2.0  # Make baseline vectors thicker
                    alpha = 1.0  # Make baseline vectors more opaque
                else:
                    color = self.twist_color_map.get(m['twist'], (0.2,0.2,0.2,1.0))
                    linewidth = lw
                    alpha = 0.95
                
                # draw shaft with pronounced dashes, then draw a solid head only
                line, = ax.plot([0, mt], [0, ml], color=color, linewidth=linewidth, alpha=alpha, solid_capstyle='round')
                dashes = _style_to_dashes(ls)
                if dashes is not None:
                    line.set_dashes(dashes)
                # arrow head at the tip, keep it solid regardless of shaft style
                length = float(np.hypot(mt, ml))
                if length > 0:
                    ux, uy = mt/length, ml/length
                    tail_x = mt - head_l * ux
                    tail_y = ml - head_l * uy
                    ax.arrow(tail_x, tail_y, head_l * ux, head_l * uy,
                             head_width=head_w, head_length=head_l, fc=color, ec=color,
                             linewidth=0, alpha=alpha)
        
        
        # Labels (toggle logic: empty text = no label)
        if self.v_title_on.isChecked():
            ttl = self.v_title_text.text().strip()
            if ttl:
                ax.set_title(ttl)
            else:
                ax.set_title("")
        else:
            ax.set_title("")
        
        if self.v_xlabel_on.isChecked():
            xl = self.v_xlabel_text.text().strip()
            if xl:
                ax.set_xlabel(xl)
            else:
                ax.set_xlabel("")
        else:
            ax.set_xlabel("")
            
        if self.v_ylabel_on.isChecked():
            yl = self.v_ylabel_text.text().strip()
            if yl:
                ax.set_ylabel(yl)
            else:
                ax.set_ylabel("")
        else:
            ax.set_ylabel("")
        
        ax.grid(self.v_grid_on.isChecked(), alpha=0.3)
        # Axes limits controls (avoid invalid ranges)
        xmin = _f(self.v_xmin.text()); xmax = _f(self.v_xmax.text())
        ymin = _f(self.v_ymin.text()); ymax = _f(self.v_ymax.text())
        if xmin is not None or xmax is not None:
            if xmin is not None and xmax is not None:
                new_min, new_max = xmin, xmax
            else:
                xr = list(ax.get_xlim())
                new_min = xmin if xmin is not None else xr[0]
                new_max = xmax if xmax is not None else xr[1]
            if new_max <= new_min:
                new_max = new_min + max(1.0, abs(new_min) * 0.05 + 1e-6)
            ax.set_xlim(new_min, new_max)
        if ymin is not None or ymax is not None:
            yr = list(ax.get_ylim())
            new_min = ymin if ymin is not None else yr[0]
            new_max = ymax if ymax is not None else yr[1]
            if new_max <= new_min:
                new_max = new_min + 1.0
            ax.set_ylim(new_min, new_max)
        # Maintain equal aspect while respecting explicit limits
        ax.set_aspect('equal', adjustable='box')
        
        self.vector_canvas.draw()
        
    def get_selected_experiments(self):
        """Get list of selected experiment keys from checked dataset selectors"""
        selected_experiments = []
        
        for row in self.dataset_rows:
            if not row['include'].isChecked():
                continue
            try:
                flow = float(row['flow'].currentText())
                period = float(row['period'].currentText())
                yaw = float(row['yaw'].currentText())
                roll = float(row['roll'].currentText())
                # No phase overlap for Power stroke data
                
                # Find matching experiment
                for exp_key, exp_data in self.data['experiments'].items():
                    params = exp_data.get('parameters', {})
                    if (abs(params.get('flow', 0) - flow) < 1e-6 and
                        abs(params.get('period', 0) - period) < 1e-6 and
                        abs(params.get('sweep', 0) - yaw) < 1e-6 and
                        abs(params.get('twist', 0) - roll) < 1e-6 and
                        True):  # No phase overlap for Power stroke data
                        selected_experiments.append(exp_key)
                        break
            except (ValueError, TypeError):
                continue
                
        return selected_experiments
        
    # Window controls removed – domain is fixed to 0..1
        
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
        
        
    def update_data_info(self):
        """Update the data information display"""
        if not self.data:
            return
            
        info_text = "Data Summary:\n"
        info_text += f"Total Experiments: {len(self.data['experiments'])}\n"
        info_text += f"Selected Experiments: {len(self.get_selected_experiments())}\n"
        
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
            
            # Time vector length varies per experiment in Paddle stroke data
            info_text += f"\nTime Vector Length: Variable per experiment (200-290 samples)\n"
            info_text += "Evaluation Window: 0.00 - 1.00 (fixed normalization)\n"
        
        # Data info display removed - functionality moved to individual tabs
        
    def plot_selected_traces(self):
        """Plot the selected experiment traces in original GUI style"""
        try:
            self.traces_figure.clear()
            ax = self.traces_figure.add_subplot(1, 1, 1)
            
            # Gather selections from dataset rows (from original GUI)
            selections = []
            for row in self.dataset_rows:
                if not row['include'].isChecked():
                    continue
                try:
                    flow = float(row['flow'].currentText())
                    period = float(row['period'].currentText())
                    yaw = float(row['yaw'].currentText())
                    roll = float(row['roll'].currentText())
                    # No phase overlap for Power stroke data
                except ValueError:
                    continue
                    
                # Find matching experiment
                exp_key = self._select_experiment(flow, period, yaw, roll)
                if exp_key is None:
                    continue
                    
                selections.append((exp_key, row))
            
            if not selections:
                QMessageBox.warning(self, "No Selection", "No valid experiments selected")
                return
            
            # Plot each selection
            for exp_key, row in selections:
                if exp_key not in self.data['experiments']:
                    continue
                    
                exp_data = self.data['experiments'][exp_key]
                # Normalize and clip time to [0,1]
                t_abs = np.asarray(exp_data['time_vector'])
                # Use absolute time directly; no normalization window
                # Get channel data
                channel = self.channel_var.currentText()
                if channel == 'thrust':
                    trace_data = np.asarray(exp_data['thrust_mean'])
                else:  # lift
                    trace_data = np.asarray(exp_data['lift_mean'])
                
                # Get styling
                color = row['color'].text()
                try:
                    lw = float(row['lw'].text())
                except ValueError:
                    lw = 2.0
                try:
                    alpha = float(row['alpha'].text())
                except ValueError:
                    alpha = 0.7
                
                # Plot the trace
                label = row['legend_label'].text() if row['legend_on'].isChecked() else None
                ax.plot(t_abs, trace_data, color=color, linewidth=lw, 
                       alpha=alpha, label=label)
                
                # Add variance shading if requested
                if row['variance'].isChecked():
                    if channel == 'thrust' and 'thrust_std' in exp_data:
                        std_data = exp_data['thrust_std']
                    elif channel == 'lift' and 'lift_std' in exp_data:
                        std_data = exp_data['lift_std']
                    else:
                        std_data = None
                        
                    if std_data is not None:
                        std_data = np.asarray(std_data)
                        ax.fill_between(t_abs, trace_data - std_data, 
                                      trace_data + std_data, color=color, alpha=0.1)
            
            # Set axis properties
            try:
                # Leave x-limits automatic for absolute time
                ax.set_ylim(float(self.ymin_var.text()), float(self.ymax_var.text()))
            except ValueError:
                pass
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Force (scaled)')
            ax.set_title('Mean Trial Traces')
            ax.grid(True, alpha=0.3)
            
            # Add legend if any traces have labels
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            self.traces_figure.tight_layout()
            self.traces_canvas.draw()
            
            # No window lines
                
            self.statusBar().showMessage(f"Plotted {len(selections)} experiments")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot traces:\n{str(e)}")
            
    def _select_experiment(self, flow, period, sweep_abs, twist_abs):
        """Select experiment using normalized parameters for Power stroke data."""
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['flow'] - flow) < 1e-6 and
                abs(m['stroke_period'] - period) < 1e-6 and
                abs(m['sweep'] - sweep_abs) < 1e-6 and
                abs(m['twist'] - twist_abs) < 1e-6):
                return exp_key
        return None
            
    def generate_all_overview_plots(self):
        """Generate all overview plots using selected experiments from dataset selectors"""
        # Get selected experiments from dataset selectors
        selected_experiments = set()
        for row in self.dataset_rows:
            if not row['include'].isChecked():
                continue
            try:
                flow = float(row['flow'].currentText())
                period = float(row['period'].currentText())
                yaw = float(row['yaw'].currentText())
                roll = float(row['roll'].currentText())
                # No phase overlap for Power stroke data
                
                exp_key = self._select_experiment(flow, period, yaw, roll)
                if exp_key:
                    selected_experiments.add(exp_key)
            except ValueError:
                continue
                
        if not selected_experiments:
            QMessageBox.warning(self, "No Selection", "Please select at least one experiment")
            return
            
        try:
            # Process data for plotting (only selected experiments)
            plot_data = self.process_data_for_plotting(selected_experiments)
            
            # Generate plots for each tab
            self.generate_mean_force_plot(plot_data)
            self.generate_peak_location_plot(plot_data)
            self.generate_vector_plot(plot_data)
            
            self.statusBar().showMessage("All overview plots generated successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate overview plots:\n{str(e)}")
            
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
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Flow Speed')
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center')
                   
    def plot_peak_location_channel(self, ax, plot_data, channel, title):
        """Plot peak location for a specific channel (lift or thrust)"""
        ax.set_title(title)
        ax.set_xlabel('Twist')
        ax.set_ylabel('Peak Location Time (s)')
        
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
            cbar = plt.colorbar(scatter, ax=ax)
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
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Flow Speed')
            
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                   ha='center', va='center')
            
    def process_data_for_plotting(self, selected_experiments=None):
        """Process the loaded mean traces data for plotting (selected experiments only)"""
        if selected_experiments is None:
            selected_experiments = self.get_selected_experiments()
            
        plot_data = {
            'twist': [],
            'sweep': [],
            'flow_speed': [],
            'stroke_period': [],
            # No phase overlap for Power stroke data
            'thrust_mean': [],
            'lift_mean': [],
            'thrust_peak_location': [],
            'lift_peak_location': [],
            'thrust_peak_value': [],
            'lift_peak_value': []
        }
        
        # Extract parameters and calculate metrics from selected experiments only
        for exp_key in selected_experiments:
            if exp_key not in self.data['experiments']:
                continue
                
            exp_data = self.data['experiments'][exp_key]
            params = exp_data['parameters']
            
            # Extract parameters (adapt based on your actual parameter names)
            period = params.get('period', params.get('stroke_period', 2.25))
            plot_data['twist'].append(params.get('twist', 0.0))
            plot_data['sweep'].append(params.get('sweep', 0.0))
            plot_data['flow_speed'].append(params.get('flow_speed', 0.0))
            plot_data['stroke_period'].append(period)
            # No phase overlap for Paddle stroke data
            
            # Get mean traces
            thrust_trace = exp_data['thrust_mean']
            lift_trace = exp_data['lift_mean']
            time_vector = exp_data['time_vector']
            
            # Get mask for paddle stroke portion (trimming artifacts)
            window_mask = self._get_paddle_stroke_mask(time_vector, period)
            if not np.any(window_mask):
                continue
            
            # Apply mask to trim data, then normalize using full stroke reference
            thrust_windowed = thrust_trace[window_mask]
            lift_windowed = lift_trace[window_mask]
            time_trimmed = time_vector[window_mask]
            time_windowed = np.linspace(0.4, 1.0, len(time_trimmed))  # Direct mapping to paddle stroke portion [0.4, 1.0]
            
            # Calculate mean forces within window
            plot_data['thrust_mean'].append(np.mean(thrust_windowed))
            plot_data['lift_mean'].append(np.mean(lift_windowed))
            
            # Calculate peak locations and values within window (only before t=0.8)
            # Only consider peaks before 0.8 of the full period
            peak_mask = time_windowed < 0.8
            if np.sum(peak_mask) > 0:
                thrust_peak_idx = np.argmax(np.abs(thrust_windowed[peak_mask]))
                lift_peak_idx = np.argmax(np.abs(lift_windowed[peak_mask]))
                
                plot_data['thrust_peak_location'].append(time_windowed[peak_mask][thrust_peak_idx])
                plot_data['lift_peak_location'].append(time_windowed[peak_mask][lift_peak_idx])
                plot_data['thrust_peak_value'].append(thrust_windowed[peak_mask][thrust_peak_idx])
                plot_data['lift_peak_value'].append(lift_windowed[peak_mask][lift_peak_idx])
            else:
                # If no data before 0.8, use the overall peak (fallback)
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
        if not self.data:
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
                         "Full-Stroke Overview Metrics GUI\n\n"
                         "Interactive tool for visualizing full-stroke experimental data\n"
                         "with customizable visual encodings and export capabilities.")
        
    def closeEvent(self, event):
        """Handle application close event"""
        event.accept()

    def _get_available_twist_values(self):
        twists = set()
        if not self.data or 'experiments' not in self.data:
            return twists
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data.get('parameters', {}))
            twists.add(m.get('twist', 0.0))
        return sorted(twists)
    
    def _populate_twist_checkboxes(self, target: str):
        # target in {'mean','peak','vec'}
        twists = self._get_available_twist_values()
        if target == 'mean' and hasattr(self, 'mean_twist_layout'):
            layout = self.mean_twist_layout; store = 'mean_twist_checks'
        elif target == 'peak' and hasattr(self, 'peak_twist_layout'):
            layout = self.peak_twist_layout; store = 'peak_twist_checks'
        elif target == 'vec' and hasattr(self, 'vec_twist_layout'):
            layout = self.vec_twist_layout; store = 'vec_twist_checks'
        else:
            return
        # Clear existing
        try:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        except RuntimeError:
            pass
        # Build row of checkboxes: | [x] 0° | [x] 15° | ... |
        checks = {}
        allowed_default = {0, 15, 30, 45, 60, 75, 90}
        for t in twists:
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4,0,4,0)
            cb = QCheckBox(f"{int(t)}°")
            checked = int(round(float(t))) in allowed_default
            cb.setChecked(checked)
            hl.addWidget(cb); layout.addWidget(w)
            checks[t] = cb
        layout.addStretch()
        setattr(self, store, checks)

    def _populate_twist_checkboxes(self, target: str):
        """Populate twist checkboxes for the given target (mean/peak/vec)"""
        # target in {'mean','peak','vec'}
        checks_attr = None
        layout_attr = None
        
        if target == 'mean':
            checks_attr = 'mean_twist_checks'
            layout_attr = 'mean_twist_layout'
        elif target == 'peak':
            checks_attr = 'peak_twist_checks'
            layout_attr = 'peak_twist_layout'
        elif target == 'vec':
            checks_attr = 'vec_twist_checks'
            layout_attr = 'vec_twist_layout'
        
        if not checks_attr or not hasattr(self, checks_attr) or not hasattr(self, layout_attr):
            return
        
        checks = getattr(self, checks_attr)
        layout = getattr(self, layout_attr)
        
        # Clear existing checkboxes
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        checks.clear()
        
        # Get available twist values
        twist_values = sorted(self.param_index.get('twist', []))
        
        # Create checkboxes
        for twist in twist_values:
            cb = QCheckBox(f"{int(twist)}°")
            cb.setChecked(True)  # Default to checked
            cb.stateChanged.connect(lambda: self.plot_mean_force() if target == 'mean' 
                                  else self.plot_peak_location() if target == 'peak'
                                  else self.plot_vector())
            layout.addWidget(cb)
            checks[twist] = cb
        
        layout.addStretch()

    def _get_selected_twists(self, target: str):
        checks_attr = None
        if target == 'mean' and hasattr(self, 'mean_twist_checks'):
            checks_attr = self.mean_twist_checks
        elif target == 'peak' and hasattr(self, 'peak_twist_checks'):
            checks_attr = self.peak_twist_checks
        elif target == 'vec' and hasattr(self, 'vec_twist_checks'):
            checks_attr = self.vec_twist_checks
        if not checks_attr:
            return None
        return {t for t, cb in checks_attr.items() if cb.isChecked()}

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Power-Stroke Overview Metrics GUI")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = PaddleStrokeOverviewGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
