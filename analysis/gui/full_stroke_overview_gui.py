


#!/usr/bin/env python3
"""
Full-Stroke Overview Metrics GUI

Interactive GUI for visualizing full-stroke experimental data with the following encodings:
- X-axis: twist
- Columns: sweep  
- Color: flow speed
- Line style: stroke period
- Marker shape: phase overlap

Metrics per panel family:
- Phase-mean thrust, phase-mean lift, resultant magnitude
- Peak thrust and peak lift with peak timing markers (normalized phase time)
- Phase-mean resultant angle

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

class FullStrokeOverviewGUI(QMainWindow):
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
            'overlap': set(),
        }
        self.dataset_rows = []
        self.init_ui()
        # Ensure data loads at startup
        self.auto_load_data()

    def _param_map(self, params):
        """Normalize raw HDF5 parameters to canonical terms; enforce absolute sweep/twist."""
        flow   = params.get('flow', params.get('flow_speed', 0.0))
        period = params.get('period', params.get('stroke_period', 0.0))
        sweep_raw  = params.get('yaw_amplitude', params.get('sweep', 0.0))
        twist_raw  = params.get('roll_angle', params.get('twist', 0.0))
        overlap = params.get('paddle_transition', params.get('phase_overlap', 0.0))
        sweep = float(abs(sweep_raw))
        twist = float(abs(twist_raw))
        return {
            'flow': float(flow),
            'stroke_period': float(period),
            'sweep': sweep,
            'twist': twist,
            'overlap': float(overlap)
        }
        
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Full-Stroke Overview Metrics GUI")
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
                    
                    # Load parameters (stored as attributes)
                    params = {}
                    param_group = exp_group['parameters']
                    for attr_name in param_group.attrs:
                        params[attr_name] = param_group.attrs[attr_name]
                    
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
                
                # Update data info
                self.update_data_info()
                
                self.statusBar().showMessage(f"Loaded {len(self.data['experiments'])} experiments from mean traces")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load trial traces data:\n{str(e)}")
            self.statusBar().showMessage("Failed to load data")
            
    def populate_parameter_index(self):
        """Populate parameter index using normalized parameters (absolute sweep/twist)."""
        # Clear existing parameter index (normalized keys)
        self.param_index = {
            'period': set(),
            'flow': set(),
            'sweep': set(),
            'twist': set(),
            'overlap': set(),
        }
        
        # Extract normalized parameters from loaded data
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data['parameters'])
            self.param_index['period'].add(m['stroke_period'])
            self.param_index['flow'].add(m['flow'])
            self.param_index['sweep'].add(m['sweep'])
            self.param_index['twist'].add(m['twist'])
            self.param_index['overlap'].add(m['overlap'])
        
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
            if hasattr(self, 'master_pt'):
                pt = [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) for v in self.param_index.get('overlap', [])]
                self.master_pt.clear(); self.master_pt.addItems(pt)
        except Exception:
            pass

    def _build_twist_color_map(self):
        """Create a categorical color map for twist values (consistent across app)."""
        twists = self.param_index.get('twist', [])
        choice = getattr(self, 'overview_palette_choice', 'Default')
        if choice == 'Custom' and hasattr(self, 'overview_custom_colors') and self.overview_custom_colors:
            palette = list(self.overview_custom_colors)
        elif choice == 'CB friendly':
            palette = ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#999999']
        else:
            palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        return {tw: palette[idx % len(palette)] for idx, tw in enumerate(twists)}

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

    def publish_all_overview_plots(self):
        outdir = os.path.join(os.getcwd(), f"Full_Stroke_Figures_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
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

        variable_types = [('Flow', 0), ('Sweep', 1), ('Overlap', 2)]
        channels = [('Thrust', 'thrust'), ('Lift', 'lift')]

        # Mean plots
        for vname, vidx in variable_types:
            try:
                [self.mean_force_flow_radio, self.mean_force_sweep_radio, self.mean_force_overlap_radio][vidx].setChecked(True)
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
                [self.peak_flow_radio, self.peak_sweep_radio, self.peak_overlap_radio][vidx].setChecked(True)
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
                [self.vec_flow_radio, self.vec_sweep_radio, self.vec_overlap_radio][vidx].setChecked(True)
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

    def _normalize_time_vector(self, time_vector: np.ndarray) -> np.ndarray:
        """Normalize absolute time to the combined stroke phase [0, 1] using [0.75s, 2.25s]."""
        t = np.asarray(time_vector, dtype=float)
        # Map 0.75->0 and 2.25->1
        t_norm = (t - 0.75) / 1.5
        return t_norm
            
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
            
            # Overlap dropdown
            pt_values = [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) for v in sorted(self.param_index.get('overlap', []))]
            row['pt'].clear()
            row['pt'].addItems(pt_values)
        
        # Default values for seeding per requirements
        default_flow = str(self.param_index['flow'][0]) if self.param_index['flow'] else '0.1'
        default_period = '2.25'
        default_pt = '0.5'
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
            if pt_values:
                row['pt'].setCurrentText(default_pt)
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
        
        # Overlap selector
        row_layout.addWidget(QLabel("Overlap"))
        pt_var = QComboBox()
        pt_var.setMinimumWidth(80)
        # Will be populated after data loading
        row_layout.addWidget(pt_var)
        
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
            'pt': pt_var,
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
        try:
            pt = row['pt'].currentText().strip()
        except Exception:
            pt = ''
        parts = [
            f"flow={flow}" if flow != '' else None,
            f"P={period}" if period != '' else None,
            f"sweep={yaw}" if yaw != '' else None,
            f"twist={roll}" if roll != '' else None,
            f"overlap={pt}" if pt != '' else None,
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
                'pt': 'master_pt_fixed',
            }[key_name]
            combo_attr = {
                'flow': 'master_flow',
                'period': 'master_period',
                'yaw': 'master_yaw',
                'roll': 'master_roll',
                'pt': 'master_pt',
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
        for key in ['flow', 'period', 'yaw', 'roll', 'pt']:
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
        
        # Create tabs
        self.create_overview_settings_tab()
        self.create_traces_tab()
        self.create_mean_overview_tab()
        self.create_mean_force_tab()
        self.create_peak_location_tab()
        self.create_vector_tab()
        
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
        self.xlabel_text_var = QLineEdit("Normalized Time (0–1)")
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
        # Overlap
        self.master_pt_fixed = QCheckBox("Fixed")
        self.master_pt = QComboBox(); self.master_pt.setMinimumWidth(80)
        master_layout.addWidget(QLabel("Overlap"), 0, 12)
        master_layout.addWidget(self.master_pt_fixed, 0, 13)
        master_layout.addWidget(self.master_pt, 0, 14)
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
        _bind_master(self.master_pt_fixed, self.master_pt, 'pt')
        
        
    
        
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
                    pt_text = self.master_pt.currentText() if getattr(self, 'master_pt_fixed', None) and self.master_pt_fixed.isChecked() else row['pt'].currentText()

                    flow = float(flow_text)
                    period = float(period_text)
                    yaw = float(yaw_text)   # sweep (absolute)
                    roll = float(roll_text) # twist (absolute)
                    try:
                        pt = float(pt_text) if pt_text != '' else None
                    except Exception:
                        pt = None
                except ValueError:
                    continue
                exp_key = self._select_experiment(flow, period, yaw, roll, pt)
                if exp_key is None:
                    continue
                selections.append((exp_key, flow, period, yaw, roll))

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
                # Normalize absolute time to [0,1] based on [0.75, 2.25]
                t_abs = np.asarray(exp_data['time_vector'])
                t = self._normalize_time_vector(t_abs)
                # Clip to [0,1] domain
                mask_domain = (t >= 0.0) & (t <= 1.0)
                if not np.any(mask_domain):
                    continue
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
                        # PT must match as well if provided
                        try:
                            pt_sel = float(row['pt'].currentText())
                        except Exception:
                            pt_sel = None
                        if pt_sel is not None and abs(pt_sel - float(exp_data['parameters'].get('paddle_transition', 0))) > 1e-6:
                            continue
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

                # Determine color by scheme
                scheme = self.color_scheme_var.currentText()
                if scheme == 'Custom':
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
                plot_label = legend_label if legend_on and legend_label else '_nolegend_'
                self.ax.plot(t[mask_domain], y, linewidth=max(0.5, lw), label=plot_label, color=color)

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
        self.mean_force_overlap_radio = QRadioButton("Overlap")
        
        self.mean_force_variable_group.addButton(self.mean_force_flow_radio, 0)
        self.mean_force_variable_group.addButton(self.mean_force_sweep_radio, 1)
        self.mean_force_variable_group.addButton(self.mean_force_overlap_radio, 2)
        self.mean_force_flow_radio.setChecked(True)
        
        # Connect radio button changes to update controls
        self.mean_force_variable_group.buttonClicked.connect(self.update_mean_force_parameter_controls)
        
        var_layout.addWidget(self.mean_force_flow_radio)
        var_layout.addWidget(self.mean_force_sweep_radio)
        var_layout.addWidget(self.mean_force_overlap_radio)
        top_layout.addWidget(var_frame)
        
        # Fixed Parameters Display (compact)
        mf_fixed_frame = QGroupBox("Fixed Parameters")
        mf_fixed_layout = QHBoxLayout(mf_fixed_frame)
        mf_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.mean_force_fixed_params_label = QLabel("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
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
        tick_layout.addWidget(QLabel("X step"))
        self.mf_xtick_step = QLineEdit("")
        self.mf_xtick_step.setPlaceholderText("auto")
        self.mf_xtick_step.setMaximumWidth(60)
        tick_layout.addWidget(self.mf_xtick_step)
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
        self.peak_overlap_radio = QRadioButton("Overlap")
        self.peak_variable_group.addButton(self.peak_flow_radio, 0)
        self.peak_variable_group.addButton(self.peak_sweep_radio, 1)
        self.peak_variable_group.addButton(self.peak_overlap_radio, 2)
        self.peak_flow_radio.setChecked(True)
        var_layout.addWidget(self.peak_flow_radio)
        var_layout.addWidget(self.peak_sweep_radio)
        var_layout.addWidget(self.peak_overlap_radio)
        top_layout.addWidget(var_frame)

        # Fixed Parameters (compact)
        peak_fixed = QGroupBox("Fixed Parameters")
        peak_fixed_layout = QHBoxLayout(peak_fixed)
        peak_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.peak_fixed_params_label = QLabel("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
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

        # Tick step controls
        tick_frame = QGroupBox("Tick Steps")
        tick_layout = QHBoxLayout(tick_frame)
        tick_layout.setContentsMargins(5, 5, 5, 5)
        tick_layout.addWidget(QLabel("X step"))
        self.pk_xtick_step = QLineEdit("")
        self.pk_xtick_step.setPlaceholderText("auto")
        self.pk_xtick_step.setMaximumWidth(60)
        tick_layout.addWidget(self.pk_xtick_step)
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
            self.peak_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_flow_values(); label_name = 'flow'
        elif self.peak_sweep_radio.isChecked():
            self.peak_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_sweep_values(); label_name = 'sweep'
        else:
            self.peak_fixed_params_label.setText("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: Variable")
            values = self.get_available_overlap_values(); label_name = 'overlap'
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
        self.vec_overlap_radio = QRadioButton("Overlap")
        self.vec_variable_group.addButton(self.vec_flow_radio, 0)
        self.vec_variable_group.addButton(self.vec_sweep_radio, 1)
        self.vec_variable_group.addButton(self.vec_overlap_radio, 2)
        self.vec_flow_radio.setChecked(True)
        var_layout.addWidget(self.vec_flow_radio)
        var_layout.addWidget(self.vec_sweep_radio)
        var_layout.addWidget(self.vec_overlap_radio)
        top_layout.addWidget(var_frame)

        # Fixed params label (compact)
        vec_fixed = QGroupBox("Fixed Parameters")
        vec_fixed_layout = QHBoxLayout(vec_fixed)
        vec_fixed_layout.setContentsMargins(5, 5, 5, 5)
        self.vec_fixed_params_label = QLabel("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
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
            self.vec_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_flow_values(); label_name = 'flow'
        elif self.vec_sweep_radio.isChecked():
            self.vec_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_sweep_values(); label_name = 'sweep'
        else:
            self.vec_fixed_params_label.setText("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: Variable")
            values = self.get_available_overlap_values(); label_name = 'overlap'
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
        self.overlap_radio = QRadioButton("Overlap")
        
        self.variable_group.addButton(self.flow_radio, 0)
        self.variable_group.addButton(self.sweep_radio, 1)
        self.variable_group.addButton(self.overlap_radio, 2)
        
        self.flow_radio.setChecked(True)  # Default to Flow
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.flow_radio)
        radio_layout.addWidget(self.sweep_radio)
        radio_layout.addWidget(self.overlap_radio)
        radio_layout.addStretch()
        var_layout.addLayout(radio_layout)
        
        # Connect radio buttons to update parameter controls
        self.variable_group.buttonClicked.connect(self.update_parameter_controls)
        
        layout.addWidget(var_frame)
        
        # Fixed Parameters Display
        fixed_frame = QGroupBox("Fixed Parameters")
        fixed_layout = QHBoxLayout(fixed_frame)
        
        self.fixed_params_label = QLabel("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
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
            # Flow mode: show flow values, fixed sweep=80, period=2.25, overlap=0.5
            self.fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
            param_values = self.get_available_flow_values()
            param_name = "flow"
        elif self.sweep_radio.isChecked():
            # Sweep mode: show sweep values, fixed flow=0.1, period=2.25, overlap=0.5
            self.fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s | Overlap: 0.5")
            param_values = self.get_available_sweep_values()
            param_name = "sweep"
        else:  # overlap_radio.isChecked()
            # Overlap mode: show overlap values, fixed flow=0.1, sweep=80, period=2.25
            self.fixed_params_label.setText("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: Variable")
            param_values = self.get_available_overlap_values()
            param_name = "overlap"
        
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
                abs(m['stroke_period'] - 2.25) < 1e-6 and
                abs(m['overlap'] - 0.5) < 1e-6):
                flow_values.add(m['flow'])
        return flow_values
        
    def get_available_sweep_values(self):
        """Get available sweep values with strict parameter control (flow=0.1, period=2.25, overlap=0.5)"""
        sweep_values = set()
        
        # Debug: Print all available parameter combinations
        print("DEBUG: All available parameter combinations:")
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            print(f"  {exp_key}: flow={m['flow']}, sweep={m['sweep']}, period={m['stroke_period']}, overlap={m['overlap']}")
        
        # Only look for experiments with ideal settings: flow=0.1, period=2.25, overlap=0.5
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['flow'] - 0.1) < 1e-6 and
                abs(m['stroke_period'] - 2.25) < 1e-6 and
                abs(m['overlap'] - 0.5) < 1e-6):
                sweep_values.add(m['sweep'])
        
        print(f"DEBUG: Found {len(sweep_values)} sweep values with ideal settings: {sweep_values}")
        
        return sweep_values
        
    def get_available_overlap_values(self):
        """Get available overlap values with strict parameter control (flow=0.1, sweep=80, period=2.25)"""
        overlap_values = set()
        
        # Debug: Print all available parameter combinations
        print("DEBUG: All available parameter combinations for overlap:")
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            print(f"  {exp_key}: flow={m['flow']}, sweep={m['sweep']}, period={m['stroke_period']}, overlap={m['overlap']}")
        
        # Only look for experiments with ideal settings: flow=0.1, sweep=80, period=2.25
        for exp_data in self.data['experiments'].values():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['flow'] - 0.1) < 1e-6 and
                abs(m['sweep'] - 80) < 1e-6 and
                abs(m['stroke_period'] - 2.25) < 1e-6):
                overlap_values.add(m['overlap'])
        
        print(f"DEBUG: Found {len(overlap_values)} overlap values with ideal settings: {overlap_values}")
        
        return overlap_values
        
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
                twist = abs(params.get('roll_angle', 0))
                
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
                t_norm = self._normalize_time_vector(time_array)
                mask = (t_norm >= 0.0) & (t_norm <= 1.0)
                if not np.any(mask):
                    continue
                window_force = np.asarray(force_data)[mask]
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
        
    def get_experiments_for_parameter(self, variable_type, param_value):
        """Get experiments matching the specified parameter value with strict parameter control"""
        matching_experiments = []
        print(f"DEBUG: Looking for {variable_type}={param_value}")
        
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            if variable_type == "flow":
                # For flow: fix sweep=80, period=2.25, overlap=0.5, vary flow
                if (abs(m['sweep'] - 80) < 1e-6 and
                    abs(m['stroke_period'] - 2.25) < 1e-6 and
                    abs(m['overlap'] - 0.5) < 1e-6 and
                    abs(m['flow'] - float(param_value)) < 1e-6):
                    matching_experiments.append(exp_key)
                    print(f"  Found flow match: {exp_key}")
            elif variable_type == "sweep":
                # For sweep: fix flow=0.1, period=2.25, overlap=0.5, vary sweep
                if (abs(m['flow'] - 0.1) < 1e-6 and
                    abs(m['stroke_period'] - 2.25) < 1e-6 and
                    abs(m['overlap'] - 0.5) < 1e-6 and
                    abs(m['sweep'] - float(param_value)) < 1e-6):
                    matching_experiments.append(exp_key)
                    print(f"  Found sweep match: {exp_key}")
            else:  # overlap
                # For overlap: fix flow=0.1, sweep=80, period=2.25, vary overlap
                if (abs(m['flow'] - 0.1) < 1e-6 and
                    abs(m['sweep'] - 80) < 1e-6 and
                    abs(m['stroke_period'] - 2.25) < 1e-6 and
                    abs(m['overlap'] - float(param_value)) < 1e-6):
                    matching_experiments.append(exp_key)
                    print(f"  Found overlap match: {exp_key}")
        
        print(f"DEBUG: Found {len(matching_experiments)} matching experiments: {matching_experiments}")
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
                    # Apply fixed normalization domain 0..1
                    t_norm = self._normalize_time_vector(np.asarray(time_vector))
                    mask = (t_norm >= 0.0) & (t_norm <= 1.0)
                    windowed_trace = np.asarray(trace)[mask]
                    windowed_time = t_norm[mask]
                    
                    # Compute arithmetic mean over the phase window
                    mean_force = float(np.mean(windowed_trace)) if len(windowed_trace) > 0 else np.nan

                    # Get experiment parameters
                    params = exp_data.get('parameters', {})
                    roll_angle = abs(params.get('roll_angle', 0))  # Absolute value for x-axis
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
        if self.mean_force_flow_radio.isChecked():
            variable_type = "flow"
        elif self.mean_force_sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "overlap"
        
        # Clear previous plot
        self.mean_force_figure.clear()
        ax = self.mean_force_figure.add_subplot(111)
        
        # Collect and plot for each enabled parameter value
        for param_value, controls in self.mean_force_parameter_controls.items():
            if not controls['toggle'].isChecked():
                continue
            marker = controls['marker'].currentText()
            
            experiments = self.get_experiments_for_parameter(variable_type, param_value)
            if not experiments:
                continue
            
            twist_values = []
            mean_values = []
            
            for exp_key in experiments:
                exp_data = self.data['experiments'][exp_key]
                params = exp_data['parameters']
                twist = abs(params.get('roll_angle', 0))
                
                time_vector = exp_data.get('time_vector', [])
                if channel == 'thrust':
                    force_data = exp_data.get('thrust_mean', [])
                else:
                    force_data = exp_data.get('lift_mean', [])
                if len(time_vector) == 0 or len(force_data) == 0:
                    continue
                
                # Normalize phase 0..1 and compute arithmetic mean within phase window
                time_array = np.asarray(time_vector)
                force_array = np.asarray(force_data)
                t_norm = self._normalize_time_vector(time_array)
                mask = (t_norm >= 0.0) & (t_norm <= 1.0)
                if not np.any(mask):
                    continue
                window_force = force_array[mask]
                mean_force = float(np.mean(window_force)) if window_force.size > 0 else np.nan
                
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
        # Labels
        if self.mf_title_on.isChecked():
            ttl = self.mf_title_text.text().strip() or f"Mean {channel.title()} vs Twist"
            ax.set_title(ttl)
        else:
            ax.set_title("")
        if self.mf_xlabel_on.isChecked():
            xl = self.mf_xlabel_text.text().strip() or "Absolute Twist (degrees)"
            ax.set_xlabel(xl)
        if self.mf_ylabel_on.isChecked():
            yl = self.mf_ylabel_text.text().strip() or f"Mean {channel.title()} Force (N)"
            ax.set_ylabel(yl)
        # Tick steps and fonts
        def _pf(s, default=None):
            try:
                return float(s)
            except Exception:
                return default
        xstep = _pf(self.mf_xtick_step.text())
        ystep = _pf(self.mf_ytick_step.text())
        if xstep and xstep > 0:
            xmin_cur, xmax_cur = ax.get_xlim()
            ax.set_xticks(np.arange(xmin_cur, xmax_cur + 0.5 * xstep, xstep))
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
            self.mean_force_fixed_params_label.setText("Flow: Variable | Sweep: 80° | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_flow_values()
            label_name = "flow"
        elif self.mean_force_sweep_radio.isChecked():
            print("DEBUG: Sweep radio button is checked")
            self.mean_force_fixed_params_label.setText("Flow: 0.1 | Sweep: Variable | Period: 2.25s | Overlap: 0.5")
            values = self.get_available_sweep_values()
            label_name = "sweep"
        else:
            print("DEBUG: Overlap radio button is checked")
            self.mean_force_fixed_params_label.setText("Flow: 0.1 | Sweep: 80° | Period: 2.25s | Overlap: Variable")
            values = self.get_available_overlap_values()
            label_name = "overlap"
        
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
        
    def plot_peak_location(self):
        """Plot peak location with variable selection; color by twist palette."""
        if not self.data or 'experiments' not in self.data:
            QMessageBox.warning(self, "No Data", "Please load data first")
            return

        # Determine variable type like Mean Force
        if self.peak_flow_radio.isChecked():
            variable_type = "flow"
        elif self.peak_sweep_radio.isChecked():
            variable_type = "sweep"
        else:
            variable_type = "overlap"

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

        # Iterate parameter values selected
        for param_value, ctrl in list(self.peak_parameter_controls.items()):
            if not _enabled(param_value):
                continue
            marker = _marker_for(param_value)
            experiments = self.get_experiments_for_parameter(variable_type, param_value)
            if not experiments:
                continue

            added_label = False
            for exp_key in experiments:
                exp = self.data['experiments'][exp_key]
                m = self._param_map(exp['parameters'])
                t_abs = np.asarray(exp.get('time_vector', []))
                if channel == 'thrust':
                    ysig = np.asarray(exp.get('thrust_mean', []))
                else:
                    ysig = np.asarray(exp.get('lift_mean', []))
                if t_abs.size == 0 or ysig.size == 0:
                    continue
                t_norm = self._normalize_time_vector(t_abs)
                # Consider peaks after 20% of cycle to capture early positive lift peaks
                min_phase = 0.20
                mask = (t_norm >= min_phase) & (t_norm <= 1.0)
                if mask.sum() < 3:
                    continue
                phase_seg = t_norm[mask]
                y_seg = ysig[mask]
                # Light smoothing for stable extrema detection
                y_sm = _smooth_signal(y_seg, window_size=5)
                # Detect local maxima and minima
                y1 = y_sm[1:-1]
                prev = y_sm[:-2]
                nxt = y_sm[2:]
                max_idx = np.where((y1 > prev) & (y1 >= nxt))[0] + 1
                min_idx = np.where((y1 < prev) & (y1 <= nxt))[0] + 1

                # Dynamic threshold scaled to signal amplitude
                amp = float(np.nanmax(np.abs(y_sm))) if y_sm.size > 0 else 0.0
                thr = max(0.15, 0.12 * amp)

                pts = []
                if channel == 'lift':
                    # Early positive peak: search in [0.20, 0.70]
                    early = (phase_seg >= 0.20) & (phase_seg <= 0.70)
                    pos_idx = [i for i in max_idx if early[i] and (y_sm[i] >= thr)]
                    if len(pos_idx) > 0:
                        i_pos = int(pos_idx[np.argmax([y_sm[i] for i in pos_idx])])
                        pts.append((float(phase_seg[i_pos]), float(y_seg[i_pos])))
                    # Later negative peak: search in [0.55, 1.00]
                    late = (phase_seg >= 0.55) & (phase_seg <= 1.00)
                    neg_idx = [i for i in min_idx if late[i] and (y_sm[i] <= -0.9*thr)]
                    if len(neg_idx) > 0:
                        i_neg = int(neg_idx[np.argmin([y_sm[i] for i in neg_idx])])
                        pts.append((float(phase_seg[i_neg]), float(y_seg[i_neg])))
                    else:
                        # Fallback for broad troughs: pick global min in late window if sufficiently negative
                        if np.any(late):
                            candidates = np.where(late)[0]
                            i_local = int(np.argmin(y_sm[candidates]))
                            i_neg = int(candidates[i_local])
                            if y_sm[i_neg] <= -0.5*thr:
                                pts.append((float(phase_seg[i_neg]), float(y_seg[i_neg])))
                else:
                    # Thrust: fallback to two strongest extrema by |value|
                    cand_idx = np.concatenate([max_idx, min_idx])
                    if cand_idx.size == 0:
                        cand_idx = np.array([int(np.argmax(np.abs(y_sm)))])
                    order = np.argsort(-np.abs(y_sm[cand_idx]))
                    cand_idx = cand_idx[order]
                    keep = [i for i in cand_idx if np.abs(y_sm[i]) >= thr]
                    for i in keep[:2]:
                        pts.append((float(phase_seg[i]), float(y_seg[i])))

                if len(pts) == 0:
                    continue
                color = self.twist_color_map.get(m['twist'], (0.2,0.2,0.2,1.0))
                # plot points with marker style controls
                def _pf(s, d):
                    try: return float(s)
                    except: return d
                size = _pf(self.pk_marker_size.text(), 60.0) if hasattr(self, 'pk_marker_size') else 60.0
                ecolor = self.pk_marker_edge_color.text().strip() if hasattr(self, 'pk_marker_edge_color') else '#000000'
                if ecolor and not ecolor.startswith('#'):
                    ecolor = '#' + ecolor
                ewidth = _pf(self.pk_marker_edge_width.text(), 0.4) if hasattr(self, 'pk_marker_edge_width') else 0.4
                for j, (px, py) in enumerate(pts):
                    lbl = f"{variable_type.title()} {param_value}" if not added_label and j == 0 else "_nolegend_"
                    ax.scatter(px, py, marker=marker, s=size, c=[color], edgecolors=ecolor, linewidths=ewidth, label=lbl)
                # connect if two points
                if len(pts) == 2:
                    ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color=color, linewidth=1.0, alpha=0.7)
                added_label = True

        # Axes formatting
        ax.set_xlabel('Peak timing (normalized 0–1)')
        ax.set_ylabel(f'Peak {channel.title()} (N)')
        ax.grid(self.pk_grid_on.isChecked(), alpha=0.3)
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
        # Tick steps and fonts
        xstep = _f(self.pk_xtick_step.text()); ystep = _f(self.pk_ytick_step.text())
        if xstep and xstep > 0:
            xmin_cur, xmax_cur = ax.get_xlim(); ax.set_xticks(np.arange(xmin_cur, xmax_cur + 0.5*xstep, xstep))
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
            variable_type = "overlap"
        
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
        
        # Iterate values
        for param_value, ctrl in list(self.vec_parameter_controls.items()):
            if not _enabled(param_value):
                continue
            experiments = self.get_experiments_for_parameter(variable_type, param_value)
            if not experiments:
                continue
            ls = _linestyle(param_value)
            for exp_key in experiments:
                exp = self.data['experiments'][exp_key]
                m = self._param_map(exp['parameters'])
                t_abs = np.asarray(exp.get('time_vector', []))
                thrust = np.asarray(exp.get('thrust_mean', []))
                lift = np.asarray(exp.get('lift_mean', []))
                if t_abs.size == 0 or thrust.size == 0 or lift.size == 0:
                    continue
                t_norm = self._normalize_time_vector(t_abs)
                mask = (t_norm >= 0.0) & (t_norm <= 1.0)
                if not np.any(mask):
                    continue
                mt = float(np.mean(thrust[mask]))
                ml = float(np.mean(lift[mask]))
                color = self.twist_color_map.get(m['twist'], (0.2,0.2,0.2,1.0))
                # draw shaft with pronounced dashes, then draw a solid head only
                line, = ax.plot([0, mt], [0, ml], color=color, linewidth=lw, alpha=0.95, solid_capstyle='round')
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
                             linewidth=0, alpha=0.95)
        
        
        ax.set_xlabel('Mean Thrust Force (N)')
        ax.set_ylabel('Mean Lift Force (N)')
        ax.set_title('Force Vector Plot (Thrust vs Lift)')
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
                pt = float(row['pt'].currentText())
                
                # Find matching experiment
                for exp_key, exp_data in self.data['experiments'].items():
                    params = exp_data.get('parameters', {})
                    if (abs(params.get('flow', 0) - flow) < 1e-6 and
                        abs(params.get('period', 0) - period) < 1e-6 and
                        abs(params.get('yaw_amplitude', 0) - yaw) < 1e-6 and
                        abs(params.get('roll_angle', 0) - roll) < 1e-6 and
                        abs(params.get('paddle_transition', 0) - pt) < 1e-6):
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
            
            info_text += f"\nTime Vector Length: {len(self.data['time_vector'])}\n"
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
                    pt = float(row['pt'].currentText()) if row['pt'].currentText() else None
                except ValueError:
                    continue
                    
                # Find matching experiment
                exp_key = self._select_experiment(flow, period, yaw, roll, pt)
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
                t = self._normalize_time_vector(t_abs)
                mask_domain = (t >= 0.0) & (t <= 1.0)
                if not np.any(mask_domain):
                    continue
                
                # Get channel data
                channel = self.channel_var.currentText()
                if channel == 'thrust':
                    trace_data = np.asarray(exp_data['thrust_mean'])[mask_domain]
                else:  # lift
                    trace_data = np.asarray(exp_data['lift_mean'])[mask_domain]
                
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
                ax.plot(t[mask_domain], trace_data, color=color, linewidth=lw, 
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
                        std_data = np.asarray(std_data)[mask_domain]
                        ax.fill_between(t[mask_domain], trace_data - std_data, 
                                      trace_data + std_data, color=color, alpha=0.1)
            
            # Set axis properties
            # Force normalized x-limits
            try:
                ax.set_xlim(0.0, 1.0)
                ax.set_ylim(float(self.ymin_var.text()), float(self.ymax_var.text()))
            except ValueError:
                pass
                
            ax.set_xlabel('Normalized Time (0–1)')
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
            
    def _select_experiment(self, flow, period, sweep_abs, twist_abs, overlap=None):
        """Select experiment using normalized parameters (absolute sweep/twist)."""
        candidates = []
        for exp_key, exp_data in self.data['experiments'].items():
            m = self._param_map(exp_data.get('parameters', {}))
            if (abs(m['flow'] - flow) < 1e-6 and
                abs(m['stroke_period'] - period) < 1e-6 and
                abs(m['sweep'] - sweep_abs) < 1e-6 and
                abs(m['twist'] - twist_abs) < 1e-6):
                if overlap is not None and abs(m['overlap'] - overlap) > 1e-6:
                    continue
                candidates.append((m['overlap'], exp_key))
        if not candidates:
            return None
        # prefer standard overlaps
        priority = [0.5, 0.55, 0.6]
        def rank(v):
            try:
                return priority.index(round(float(v), 2))
            except ValueError:
                return len(priority)
        candidates.sort(key=lambda t: rank(t[0]))
        return candidates[0][1]
            
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
                pt = float(row['pt'].currentText()) if row['pt'].currentText() else None
                
                exp_key = self._select_experiment(flow, period, yaw, roll, pt)
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
            'phase_overlap': [],
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
            plot_data['twist'].append(params.get('twist', 0.0))
            plot_data['sweep'].append(params.get('sweep', 0.0))
            plot_data['flow_speed'].append(params.get('flow_speed', 0.0))
            plot_data['stroke_period'].append(params.get('stroke_period', 0.0))
            plot_data['phase_overlap'].append(params.get('phase_overlap', 0.0))
            
            # Get mean traces
            thrust_trace = exp_data['thrust_mean']
            lift_trace = exp_data['lift_mean']
            time_vector = exp_data['time_vector']
            
            # Normalize absolute time to fixed 0-1 combined stroke phase
            time_norm = self._normalize_time_vector(time_vector)
            
            # Apply fixed domain
            window_mask = (time_norm >= 0.0) & (time_norm <= 1.0)
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

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Full-Stroke Overview Metrics GUI")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = FullStrokeOverviewGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
