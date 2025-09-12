#!/usr/bin/env python3
"""
Trial Traces Plotting GUI

- Loads TrialTraces_Complete_*.h5
- Up to 10 dataset selectors (include + Flow/Yaw/Roll)
- Axis controls: ranges, tick steps, axis title
- Overlays mean traces (Thrust or Lift) with the first selected on top

Author: AI Assistant
Date: 2025-09-12
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import h5py
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class TrialTracesPlotGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Trial Traces Plotter (Means Overlay)")

        # State
        self.h5_path = self.find_trial_traces_file()
        if self.h5_path is None:
            messagebox.showerror("File not found", "Could not find TrialTraces_Complete_*.h5 under data/processed.\nPlease run the processing first.")
            self.root.destroy()
            return

        self.experiments = {}           # exp_key -> dict with parameters, time_vector, thrust_mean, lift_mean, thrust_std, lift_std
        self.param_index = {            # unique values
            'flow': set(),
            'yaw': set(),
            'roll': set(),
            'pt': set(),
        }
        self.exp_lookup = []            # list of (exp_key, flow, yaw, roll, paddle)
        self.flow_priority = [0.0, 0.1] # Ordering for display
        self.paddle_priority = [0.5, 0.55, 0.6]

        self.load_experiments()

        # UI Layout
        self.build_ui()

    def find_trial_traces_file(self) -> str | None:
        # Prefer the known path
        base_dir = os.path.join('data', 'processed')
        if not os.path.isdir(base_dir):
            return None
        candidate = None
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.startswith('TrialTraces_Complete_') and f.endswith('.h5'):
                    candidate = os.path.join(root, f)
                    return candidate
        return None

    def map_flow_from_fullstroke(self, exp_index: int) -> float:
        """
        Map exp index to flow speed using the original FullStroke file.
        Assumes ordering: first N = 20-Jan (0.1 m/s), next N = 30-Jan (0.0 m/s).
        If the original file is unavailable, fallback to heuristic: first half 0.1, second half 0.0.
        """
        fullstroke_path = None
        base_dir = os.path.join('data', 'processed')
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f == 'FullStroke_Complete_2025-01-27.h5':
                    fullstroke_path = os.path.join(root, f)
                    break
            if fullstroke_path:
                break

        if fullstroke_path and os.path.exists(fullstroke_path):
            try:
                with h5py.File(fullstroke_path, 'r') as fh:
                    meta = fh['metadata']
                    n20 = int(meta.attrs.get('experiments_from_20Jan', 63))
                    # 20-Jan corresponds to 0.1 m/s; 30-Jan corresponds to 0.0 m/s
                    if exp_index < n20:
                        return 0.1
                    return 0.0
            except Exception:
                pass

        # Fallback heuristic: half 0.1 then 0.0
        # We'll attempt to infer total count from TrialTraces file
        try:
            with h5py.File(self.h5_path, 'r') as f:
                exp_keys = list(f['experiments'].keys())
                total = len(exp_keys)
                half = total // 2
                return 0.1 if exp_index < half else 0.0
        except Exception:
            return 0.0

    def load_experiments(self) -> None:
        with h5py.File(self.h5_path, 'r') as f:
            exp_group = f['experiments']
            exp_keys = sorted(exp_group.keys())
            for idx, exp_key in enumerate(exp_keys):
                grp = exp_group[exp_key]
                # Parameters saved as attrs under 'parameters'
                param_attrs = grp['parameters'].attrs
                period = float(param_attrs.get('period', 2.25))
                yaw = float(param_attrs.get('yaw_amplitude', np.nan))
                roll = float(param_attrs.get('roll_angle', np.nan))
                paddle = float(param_attrs.get('paddle_transition', np.nan))
                flow = self.map_flow_from_fullstroke(idx)

                time_vec = grp['time_vector'][:]
                thrust_mean = grp['thrust']['mean_trace'][:]
                lift_mean = grp['lift']['mean_trace'][:]
                # std traces (used for variance shading)
                thrust_std = grp['thrust']['std_trace'][:] if 'std_trace' in grp['thrust'] else None
                lift_std = grp['lift']['std_trace'][:] if 'std_trace' in grp['lift'] else None

                self.experiments[exp_key] = {
                    'period': period,
                    'yaw': yaw,
                    'roll': roll,
                    'paddle': paddle,
                    'flow': flow,
                    'time': time_vec,
                    'thrust_mean': thrust_mean,
                    'lift_mean': lift_mean,
                    'thrust_std': thrust_std,
                    'lift_std': lift_std,
                }

                if not np.isnan(yaw):
                    self.param_index['yaw'].add(yaw)
                if not np.isnan(roll):
                    self.param_index['roll'].add(roll)
                self.param_index['flow'].add(flow)
                if not np.isnan(paddle):
                    self.param_index['pt'].add(paddle)

                self.exp_lookup.append((exp_key, flow, yaw, roll, paddle))

        # Sort parameter options for UI
        self.param_index['flow'] = sorted(list(self.param_index['flow']))
        self.param_index['yaw'] = sorted(list(self.param_index['yaw']))
        self.param_index['roll'] = sorted(list(self.param_index['roll']))
        self.param_index['pt'] = sorted(list(self.param_index['pt']))

    def build_ui(self) -> None:
        # Top controls frame
        ctrl = ttk.Frame(self.root)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        # Channel selection
        chan_frame = ttk.Frame(ctrl)
        chan_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(chan_frame, text="Channel:").grid(row=0, column=0, sticky=tk.W)
        self.channel_var = tk.StringVar(value='thrust')
        ttk.Radiobutton(chan_frame, text="Thrust", value='thrust', variable=self.channel_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(chan_frame, text="Lift", value='lift', variable=self.channel_var).grid(row=0, column=2, sticky=tk.W)

        # Axis controls
        axis_frame = ttk.LabelFrame(ctrl, text="Axis Controls")
        axis_frame.pack(side=tk.LEFT, padx=(0, 20))

        self.xmin_var = tk.StringVar(value="0.0")
        self.xmax_var = tk.StringVar(value="3.0")
        self.xstep_var = tk.StringVar(value="0.5")
        self.ymin_var = tk.StringVar(value="-5.0")
        self.ymax_var = tk.StringVar(value="5.0")
        self.ystep_var = tk.StringVar(value="1.0")
        # Legacy plot title kept for backward compat (unused once Labels box is used)
        self.title_var = tk.StringVar(value="Mean Trial Traces")

        ttk.Label(axis_frame, text="X min").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(axis_frame, width=7, textvariable=self.xmin_var).grid(row=0, column=1)
        ttk.Label(axis_frame, text="X max").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(axis_frame, width=7, textvariable=self.xmax_var).grid(row=0, column=3)
        ttk.Label(axis_frame, text="X step").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(axis_frame, width=7, textvariable=self.xstep_var).grid(row=0, column=5)

        ttk.Label(axis_frame, text="Y min").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(axis_frame, width=7, textvariable=self.ymin_var).grid(row=1, column=1, pady=(5, 0))
        ttk.Label(axis_frame, text="Y max").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        ttk.Entry(axis_frame, width=7, textvariable=self.ymax_var).grid(row=1, column=3, pady=(5, 0))
        ttk.Label(axis_frame, text="Y step").grid(row=1, column=4, sticky=tk.W, pady=(5, 0))
        ttk.Entry(axis_frame, width=7, textvariable=self.ystep_var).grid(row=1, column=5, pady=(5, 0))

        # Labels/Titles group per sketch: checkbox + text + font + size
        labels_frame = ttk.LabelFrame(ctrl, text="Labels/Titles")
        labels_frame.pack(side=tk.LEFT, padx=(0, 20))

        font_choices = ['Default', 'DejaVu Sans', 'Arial', 'Calibri', 'Times New Roman', 'Helvetica']

        # Title controls
        self.title_on_var = tk.BooleanVar(value=True)
        self.title_text_var = tk.StringVar(value="Mean Trial Traces")
        self.title_font_var = tk.StringVar(value='Default')
        self.title_fs_var = tk.StringVar(value=self.title_fs_var.get() if hasattr(self, 'title_fs_var') else '14')

        ttk.Checkbutton(labels_frame, text="Title", variable=self.title_on_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(labels_frame, width=22, textvariable=self.title_text_var).grid(row=0, column=1, padx=(4, 6))
        ttk.Combobox(labels_frame, state='readonly', width=14, values=font_choices, textvariable=self.title_font_var).grid(row=0, column=2)
        ttk.Entry(labels_frame, width=5, textvariable=self.title_fs_var).grid(row=0, column=3, padx=(6, 0))

        # X label controls
        self.xlabel_on_var = tk.BooleanVar(value=True)
        self.xlabel_text_var = tk.StringVar(value="Time (s)")
        self.xlabel_font_var = tk.StringVar(value='Default')
        self.xlabel_fs_var = tk.StringVar(value='12')

        ttk.Checkbutton(labels_frame, text="X Label", variable=self.xlabel_on_var).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(labels_frame, width=22, textvariable=self.xlabel_text_var).grid(row=1, column=1, padx=(4, 6), pady=(5, 0))
        ttk.Combobox(labels_frame, state='readonly', width=14, values=font_choices, textvariable=self.xlabel_font_var).grid(row=1, column=2, pady=(5, 0))
        ttk.Entry(labels_frame, width=5, textvariable=self.xlabel_fs_var).grid(row=1, column=3, padx=(6, 0), pady=(5, 0))

        # Y label controls
        self.ylabel_on_var = tk.BooleanVar(value=True)
        self.ylabel_text_var = tk.StringVar(value="Force (scaled)")
        self.ylabel_font_var = tk.StringVar(value='Default')
        self.ylabel_fs_var = tk.StringVar(value='12')

        ttk.Checkbutton(labels_frame, text="Y Label", variable=self.ylabel_on_var).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(labels_frame, width=22, textvariable=self.ylabel_text_var).grid(row=2, column=1, padx=(4, 6), pady=(5, 0))
        ttk.Combobox(labels_frame, state='readonly', width=14, values=font_choices, textvariable=self.ylabel_font_var).grid(row=2, column=2, pady=(5, 0))
        ttk.Entry(labels_frame, width=5, textvariable=self.ylabel_fs_var).grid(row=2, column=3, padx=(6, 0), pady=(5, 0))

        # Font controls
        font_frame = ttk.LabelFrame(ctrl, text="Fonts")
        font_frame.pack(side=tk.LEFT, padx=(0, 20))

        self.title_fs_var = tk.StringVar(value="14")
        self.axis_fs_var = tk.StringVar(value="12")
        self.legend_fs_var = tk.StringVar(value="10")
        self.legend_loc_var = tk.StringVar(value="best")

        ttk.Label(font_frame, text="Title FS").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(font_frame, width=5, textvariable=self.title_fs_var).grid(row=0, column=1)
        ttk.Label(font_frame, text="Axis FS").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(font_frame, width=5, textvariable=self.axis_fs_var).grid(row=0, column=3)
        ttk.Label(font_frame, text="Legend FS").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(font_frame, width=5, textvariable=self.legend_fs_var).grid(row=0, column=5)

        ttk.Label(font_frame, text="Legend Loc").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        legend_opts = ['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
        ttk.Combobox(font_frame, state='readonly', width=14, values=legend_opts, textvariable=self.legend_loc_var).grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(5, 0))
        self.legend_on_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(font_frame, text="Show Legend", variable=self.legend_on_var).grid(row=1, column=4, columnspan=2, padx=(10, 0), sticky=tk.W)

        # Color scheme controls
        color_frame = ttk.LabelFrame(ctrl, text="Colors")
        color_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(color_frame, text="Scheme").grid(row=0, column=0, sticky=tk.W)
        self.color_scheme_var = tk.StringVar(value='Default')
        ttk.Combobox(color_frame, state='readonly', width=12, values=['Default','CB friendly','Custom'], textvariable=self.color_scheme_var).grid(row=0, column=1)

        # Publish controls
        pub_frame = ttk.LabelFrame(ctrl, text="Publish")
        pub_frame.pack(side=tk.LEFT)

        self.pub_w_var = tk.StringVar(value="1200")
        self.pub_h_var = tk.StringVar(value="800")
        self.pub_name_var = tk.StringVar(value="FullStroke_plot.png")

        ttk.Label(pub_frame, text="W(px)").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(pub_frame, width=7, textvariable=self.pub_w_var).grid(row=0, column=1)
        ttk.Label(pub_frame, text="H(px)").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(pub_frame, width=7, textvariable=self.pub_h_var).grid(row=0, column=3)
        ttk.Label(pub_frame, text="Name").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(pub_frame, width=24, textvariable=self.pub_name_var).grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(5, 0))

        ttk.Button(pub_frame, text="Publish", command=self.publish_figure).grid(row=0, column=4, rowspan=2, padx=(8, 0))

        # Plot button
        self.plot_button = ttk.Button(ctrl, text="Plot", command=self.plot_overlay, style="Accent.TButton")
        self.plot_button.pack(side=tk.LEFT)

        # Dataset selectors (up to 10)
        sel_frame = ttk.LabelFrame(self.root, text="Datasets (up to 10)")
        sel_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        self.dataset_rows = []
        for i in range(10):
            row = self._build_selector_row(sel_frame, i)
            self.dataset_rows.append(row)

        # Matplotlib Figure
        fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.grid(True, alpha=0.3)
        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Seed selectors with defaults
        self._seed_defaults()
        self.plot_overlay()

    def _build_selector_row(self, parent: ttk.LabelFrame, idx: int):
        rowf = ttk.Frame(parent)
        rowf.grid(row=idx, column=0, sticky=tk.W, padx=5, pady=2)

        include_var = tk.BooleanVar(value=(idx == 0))
        ttk.Checkbutton(rowf, text=f"Include {idx+1}", variable=include_var).grid(row=0, column=0, padx=(0, 8))

        ttk.Label(rowf, text="Flow").grid(row=0, column=1)
        flow_var = tk.StringVar()
        flow_cb = ttk.Combobox(rowf, width=6, state='readonly', textvariable=flow_var,
                               values=[str(v) for v in self.param_index['flow']])
        flow_cb.grid(row=0, column=2, padx=(0, 12))

        ttk.Label(rowf, text="Yaw").grid(row=0, column=3)
        yaw_var = tk.StringVar()
        yaw_cb = ttk.Combobox(rowf, width=6, state='readonly', textvariable=yaw_var,
                              values=[str(int(v)) for v in self.param_index['yaw']])
        yaw_cb.grid(row=0, column=4, padx=(0, 12))

        ttk.Label(rowf, text="Roll").grid(row=0, column=5)
        roll_var = tk.StringVar()
        roll_cb = ttk.Combobox(rowf, width=6, state='readonly', textvariable=roll_var,
                               values=[str(int(v)) for v in self.param_index['roll']])
        roll_cb.grid(row=0, column=6, padx=(0, 12))

        ttk.Label(rowf, text="PT").grid(row=0, column=7)
        pt_var = tk.StringVar()
        pt_vals = [f"{v:.2f}" if abs(v - round(v)) > 1e-6 else str(int(v)) for v in self.param_index['pt']]
        ttk.Combobox(rowf, width=6, state='readonly', textvariable=pt_var, values=pt_vals).grid(row=0, column=8, padx=(0, 12))

        # Style controls: Color (HEX), Line Width, Variance toggle, Alpha
        ttk.Label(rowf, text="Color").grid(row=0, column=9)
        color_var = tk.StringVar()
        ttk.Entry(rowf, width=8, textvariable=color_var).grid(row=0, column=10, padx=(0, 8))

        ttk.Label(rowf, text="LW").grid(row=0, column=11)
        lw_var = tk.StringVar()
        ttk.Entry(rowf, width=4, textvariable=lw_var).grid(row=0, column=12, padx=(0, 8))

        var_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rowf, text="Variance", variable=var_var).grid(row=0, column=13, padx=(0, 8))

        ttk.Label(rowf, text="Alpha").grid(row=0, column=14)
        alpha_var = tk.StringVar()
        ttk.Entry(rowf, width=4, textvariable=alpha_var).grid(row=0, column=15)

        # Legend controls: include + custom label text
        legend_on_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rowf, text="Legend", variable=legend_on_var).grid(row=0, column=16, padx=(8, 4))
        legend_label_var = tk.StringVar()
        ttk.Entry(rowf, width=18, textvariable=legend_label_var).grid(row=0, column=17)

        return {
            'include': include_var,
            'flow': flow_var,
            'yaw': yaw_var,
            'roll': roll_var,
            'pt': pt_var,
            'color': color_var,
            'lw': lw_var,
            'variance': var_var,
            'alpha': alpha_var,
            'legend_on': legend_on_var,
            'legend_label': legend_label_var,
        }

    def _seed_defaults(self) -> None:
        # Default to plotting a small sweep across yaw at roll=-45, flow=0.0 if available
        default_flow = str(self.param_index['flow'][0]) if self.param_index['flow'] else '0.0'
        default_roll = '-45'
        default_yaws = [
            str(int(v)) for v in self.param_index['yaw'][:5]
        ]
        default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        for i, row in enumerate(self.dataset_rows):
            row['flow'].set(default_flow)
            row['roll'].set(default_roll if default_roll in [str(int(v)) for v in self.param_index['roll']] else (str(int(self.param_index['roll'][0])) if self.param_index['roll'] else '0'))
            if i < len(default_yaws):
                row['yaw'].set(default_yaws[i])
                row['include'].set(True)
            else:
                # Set some valid default
                row['yaw'].set(default_yaws[0] if default_yaws else '')
                row['include'].set(False)
            # Set default PT to first available
            try:
                row['pt'].set((f"{self.param_index['pt'][0]:.2f}" if abs(self.param_index['pt'][0] - round(self.param_index['pt'][0])) > 1e-6 else str(int(self.param_index['pt'][0]))) if self.param_index['pt'] else '')
            except Exception:
                pass
            # Style defaults
            row['color'].set(default_colors[i % len(default_colors)])
            row['lw'].set('2.0')
            row['alpha'].set('0.2')
            # Default legend label
            try:
                default_lbl = f"flow={default_flow}, yaw={row['yaw'].get()}, roll={row['roll'].get()}"
            except Exception:
                default_lbl = ''
            row['legend_on'].set(True)
            row['legend_label'].set(default_lbl)

    def _select_experiment(self, flow: float, yaw: float, roll: float, pt: float | None = None) -> str | None:
        """
        Choose an experiment matching flow, yaw, roll.
        If pt is provided, pick exact PT match. Otherwise prefer paddle priority 0.5, 0.55, 0.6.
        Returns exp_key or None.
        """
        candidates = []
        for exp_key, f, y, r, p in self.exp_lookup:
            if abs(f - flow) < 1e-6 and abs(y - yaw) < 1e-6 and abs(r - roll) < 1e-6:
                # If PT specified, only include matching PT
                if pt is not None and abs(float(p) - float(pt)) > 1e-6:
                    continue
                candidates.append((p, exp_key))
        if not candidates:
            return None
        # Sort by paddle priority
        def paddle_rank(pval: float) -> int:
            try:
                return self.paddle_priority.index(round(pval, 2))
            except ValueError:
                return len(self.paddle_priority)
        candidates.sort(key=lambda t: paddle_rank(float(t[0])))
        return candidates[0][1]

    def plot_overlay(self) -> None:
        try:
            # Gather selections in order
            selections = []
            for row in self.dataset_rows:
                if not row['include'].get():
                    continue
                try:
                    flow = float(row['flow'].get())
                    yaw = float(row['yaw'].get())
                    roll = float(row['roll'].get())
                    try:
                        pt = float(row['pt'].get()) if row['pt'].get() != '' else None
                    except Exception:
                        pt = None
                except ValueError:
                    continue
                exp_key = self._select_experiment(flow, yaw, roll, pt)
                if exp_key is None:
                    continue
                selections.append((exp_key, flow, yaw, roll))

            # Clear axes
            self.ax.clear()
            self.ax.grid(True, alpha=0.3)
            # Font sizes
            def _pf(s: str, default: float) -> float:
                try:
                    return float(s)
                except Exception:
                    return default
            title_fs = _pf(self.title_fs_var.get(), 14)
            axis_fs = _pf(self.axis_fs_var.get(), 12)
            legend_fs = _pf(self.legend_fs_var.get(), 10)
            # Font family helper
            def _fontfam(sel: str) -> dict:
                return {'fontfamily': sel} if sel and sel != 'Default' else {}

            # Apply labels based on toggles
            if self.title_on_var.get():
                self.ax.set_title(self.title_text_var.get(), fontsize=title_fs, **_fontfam(self.title_font_var.get()))
            else:
                self.ax.set_title('')
            if self.xlabel_on_var.get():
                self.ax.set_xlabel(self.xlabel_text_var.get(), fontsize=_pf(self.xlabel_fs_var.get(), axis_fs), **_fontfam(self.xlabel_font_var.get()))
            else:
                self.ax.set_xlabel('')
            if self.ylabel_on_var.get():
                self.ax.set_ylabel(self.ylabel_text_var.get(), fontsize=_pf(self.ylabel_fs_var.get(), axis_fs), **_fontfam(self.ylabel_font_var.get()))
            else:
                self.ax.set_ylabel('')
            self.ax.tick_params(labelsize=axis_fs)

            # Plot in reverse so first selection is on top
            for exp_key, flow, yaw, roll in reversed(selections):
                exp = self.experiments[exp_key]
                t = exp['time']
                if self.channel_var.get() == 'thrust':
                    y = exp['thrust_mean']
                    ystd = exp['thrust_std']
                    label = f"T: flow={flow}, yaw={int(yaw)}, roll={int(roll)}"
                else:
                    y = exp['lift_mean']
                    ystd = exp['lift_std']
                    label = f"L: flow={flow}, yaw={int(yaw)}, roll={int(roll)}"

                # Styles
                color = None
                lw = 2.0
                alpha = 0.2
                # Find the row that provided this selection to read style settings
                row_index_for_palette = 0
                for ridx, row in enumerate(self.dataset_rows):
                    try:
                        if not row['include'].get():
                            continue
                        if abs(float(row['flow'].get()) - flow) > 1e-6:
                            continue
                        if abs(float(row['yaw'].get()) - yaw) > 1e-6:
                            continue
                        if abs(float(row['roll'].get()) - roll) > 1e-6:
                            continue
                        # PT must match as well if provided
                        try:
                            pt_sel = float(row['pt'].get())
                        except Exception:
                            pt_sel = None
                        if pt_sel is not None and abs(pt_sel - float(self.experiments[exp_key]['paddle'])) > 1e-6:
                            continue
                        row_index_for_palette = ridx
                        cval = row['color'].get().strip()
                        if cval and not cval.startswith('#'):
                            cval = '#' + cval
                        try:
                            lw = float(row['lw'].get()) if row['lw'].get() else 2.0
                        except Exception:
                            lw = 2.0
                        try:
                            alpha = float(row['alpha'].get()) if row['alpha'].get() else 0.2
                        except Exception:
                            alpha = 0.2
                        include_var = row['variance'].get()
                        legend_on = row['legend_on'].get()
                        legend_label = row['legend_label'].get().strip()
                        break
                    except Exception:
                        continue
                else:
                    include_var = False
                    legend_on = True
                    legend_label = ''

                # Determine color by scheme
                scheme = getattr(self, 'color_scheme_var', None).get() if getattr(self, 'color_scheme_var', None) else 'Default'
                if scheme == 'Custom':
                    # Use user-entered color if provided; else fallback to default palette
                    if cval:
                        color = cval
                    else:
                        color = self._palette_color('Default', row_index_for_palette)
                else:
                    color = self._palette_color(scheme, row_index_for_palette)

                # Variance shading (mean ± variance) — variance = std^2
                if include_var and ystd is not None:
                    yvar = ystd * ystd
                    self.ax.fill_between(t, y - yvar, y + yvar, color=color, alpha=max(0.0, min(alpha, 1.0)), linewidth=0)

                # Mean line with legend label control
                plot_label = legend_label if legend_on and legend_label else '_nolegend_'
                self.ax.plot(t, y, linewidth=max(0.5, lw), label=plot_label, color=color)

            if selections and getattr(self, 'legend_on_var', None) and self.legend_on_var.get():
                loc = self.legend_loc_var.get() if self.legend_loc_var.get() else 'best'
                self.ax.legend(loc=loc, fontsize=legend_fs)

            # Axes ranges and ticks
            def _parse_float(s: str, default: float) -> float:
                try:
                    return float(s)
                except Exception:
                    return default

            xmin = _parse_float(self.xmin_var.get(), 0.0)
            xmax = _parse_float(self.xmax_var.get(), 3.0)
            ymin = _parse_float(self.ymin_var.get(), -5.0)
            ymax = _parse_float(self.ymax_var.get(), 5.0)
            xstep = _parse_float(self.xstep_var.get(), 0.5)
            ystep = _parse_float(self.ystep_var.get(), 1.0)

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

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot: {e}")

    def _normalize_color(self, exp_key: str, flow: float, yaw: float, roll: float) -> str:
        # Default color cycle if user leaves color empty
        # Deterministic per (flow, yaw, roll)
        palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        key = (round(flow, 2), int(yaw), int(roll))
        idx = (hash(key) % len(palette))
        return palette[idx]

    def _palette_color(self, scheme: str, idx: int) -> str:
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

    def publish_figure(self) -> None:
        try:
            # Parse dimensions
            wpx = int(float(self.pub_w_var.get()))
            hpx = int(float(self.pub_h_var.get()))
            if wpx <= 0 or hpx <= 0:
                raise ValueError("Dimensions must be positive")

            # Filename
            name = self.pub_name_var.get().strip()
            if not name:
                name = "FullStroke_plot.png"
            if not name.lower().endswith('.png'):
                name += '.png'

            # Output directory Figures/FullStroke/Traces_YYYY-MM-DD
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            out_dir = os.path.join('Figures', 'FullStroke', f'Traces_{today}')
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, name)

            fig = self.ax.figure
            prev_size = fig.get_size_inches()
            prev_dpi = fig.dpi
            try:
                # Set size to match pixels via dpi=100
                dpi = 100.0
                fig.set_size_inches(wpx / dpi, hpx / dpi)
                fig.savefig(out_path, dpi=dpi, bbox_inches='tight', facecolor='white')
            finally:
                # Restore
                fig.set_size_inches(prev_size)
                fig.set_dpi(prev_dpi)

            messagebox.showinfo("Published", f"Saved figure to\n{out_path}")
        except Exception as e:
            messagebox.showerror("Publish Error", f"Failed to publish figure: {e}")


def main() -> None:
    root = tk.Tk()
    # Optional ttk theme setup
    try:
        from tkinter import ttk as _ttk
        style = _ttk.Style(root)
        # Use default theme; Accent.TButton may not exist on all installs
        if 'azure' in style.theme_names():
            style.theme_use('azure')
    except Exception:
        pass
    app = TrialTracesPlotGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()


