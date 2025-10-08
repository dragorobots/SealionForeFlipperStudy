#!/usr/bin/env python3
"""
Paddle Stroke Trial Alignment GUI

Copy of the Power trial alignment flow adapted for Paddle raw trials with Arduino.

Notes:
- Loads raw Paddle MATLAB v7.3 .mat (via mat73) and groups trials by parameters.
- Each trial is a (7500, 3) array: [thrust, lift, arduino] inferred from value ranges
  (arduino column ranges ~0..3.5). Sampling rate assumed 500 Hz.
- UI mirrors Power: detect trial start from Arduino, fixed trial length by period,
  discard first, use next up to 5 across trials, overlay thrust/lift/arduino.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import h5py
import mat73
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class PaddleTrialAlignmentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Paddle Stroke Trial Alignment GUI")
        self.root.geometry("1400x900")

        # Data containers
        self.mat_paths = []
        self.groups = []           # list of group keys (flow,sweep,twist,period)
        self.params_by_group = {}  # key -> {flow,sweep,twist,period,num_trials}
        self.data_by_group = {}    # key -> dict with 'trials': list of np.ndarray shape (3,T)

        # Current selection
        self.current_group = None

        # Build UI
        self._build_ui()
        self._auto_load_latest()

    # ---------------- UI ----------------
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        # Title
        ttk.Label(main, text="Paddle Stroke Trial Alignment (with Arduino)", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky=tk.W)

        # Selection frame
        sel = ttk.LabelFrame(main, text="Experiment Selection", padding=8)
        sel.grid(row=1, column=0, sticky=(tk.E, tk.W))
        sel.columnconfigure(6, weight=1)

        ttk.Label(sel, text="Flow (m/s):").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.flow_cb = ttk.Combobox(sel, state="readonly", width=10)
        self.flow_cb.grid(row=0, column=1, sticky=tk.W, padx=(0, 16))

        ttk.Label(sel, text="Sweep (°):").grid(row=0, column=2, sticky=tk.W, padx=(0, 6))
        self.sweep_cb = ttk.Combobox(sel, state="readonly", width=10)
        self.sweep_cb.grid(row=0, column=3, sticky=tk.W, padx=(0, 16))

        ttk.Label(sel, text="Twist (°):").grid(row=0, column=4, sticky=tk.W, padx=(0, 6))
        self.twist_cb = ttk.Combobox(sel, state="readonly", width=10)
        self.twist_cb.grid(row=0, column=5, sticky=tk.W, padx=(0, 16))

        ttk.Label(sel, text="Period (s):").grid(row=0, column=6, sticky=tk.W, padx=(0, 6))
        self.period_cb = ttk.Combobox(sel, state="readonly", width=10)
        self.period_cb.grid(row=0, column=7, sticky=tk.W, padx=(0, 16))
        self.period_cb.bind('<<ComboboxSelected>>', lambda e: self._on_period_change())

        self.load_btn = ttk.Button(sel, text="Load Group", command=self._load_selected_group)
        self.load_btn.grid(row=0, column=8, sticky=tk.W)

        self.status_lbl = ttk.Label(sel, text="", foreground="blue")
        self.status_lbl.grid(row=1, column=0, columnspan=9, sticky=tk.W, pady=(6, 0))

        # Detection / Plot controls (similar to Power)
        ctrl = ttk.LabelFrame(main, text="Detection and Plot Controls", padding=8)
        ctrl.grid(row=2, column=0, sticky=(tk.E, tk.W), pady=(8, 8))
        # Before trial include and trial length
        ttk.Label(ctrl, text="Before Trial Include (samples):").grid(row=0, column=0, sticky=tk.W)
        self.before_trial_include = tk.StringVar(value="10")
        ttk.Entry(ctrl, width=8, textvariable=self.before_trial_include).grid(row=0, column=1)
        ttk.Label(ctrl, text="Trial Length (samples):").grid(row=0, column=2, sticky=tk.W, padx=(12,0))
        self.trial_length = tk.StringVar(value="300")
        ttk.Entry(ctrl, width=8, textvariable=self.trial_length).grid(row=0, column=3)

        # Thresholds
        ttk.Label(ctrl, text="Low Band Max:").grid(row=0, column=4, sticky=tk.W, padx=(12,0))
        self.low_thr = tk.StringVar(value="1.5")
        ttk.Entry(ctrl, width=8, textvariable=self.low_thr).grid(row=0, column=5)
        ttk.Label(ctrl, text="High Band Min:").grid(row=0, column=6, sticky=tk.W)
        self.high_thr = tk.StringVar(value="2.0")
        ttk.Entry(ctrl, width=8, textvariable=self.high_thr).grid(row=0, column=7)

        # Y ranges
        ttk.Label(ctrl, text="Y Ranges (Thrust/Lift):").grid(row=1, column=0, sticky=tk.W, pady=(6,0))
        self.t_ymin = tk.StringVar(value="-3"); self.t_ymax = tk.StringVar(value="3")
        self.l_ymin = tk.StringVar(value="-3"); self.l_ymax = tk.StringVar(value="3")
        ttk.Entry(ctrl, width=6, textvariable=self.t_ymin).grid(row=1, column=1)
        ttk.Label(ctrl, text="to").grid(row=1, column=2)
        ttk.Entry(ctrl, width=6, textvariable=self.t_ymax).grid(row=1, column=3)
        ttk.Label(ctrl, text="  |  ").grid(row=1, column=4)
        ttk.Entry(ctrl, width=6, textvariable=self.l_ymin).grid(row=1, column=5)
        ttk.Label(ctrl, text="to").grid(row=1, column=6)
        ttk.Entry(ctrl, width=6, textvariable=self.l_ymax).grid(row=1, column=7)

        # Processing toggles
        self.zero_correction_var = tk.BooleanVar()
        ttk.Checkbutton(ctrl, text="Zero the Data", variable=self.zero_correction_var, command=lambda: self.update_plot()).grid(row=1, column=8, padx=(12, 6), sticky=tk.W)
        self.apply_filters_var = tk.BooleanVar()
        ttk.Checkbutton(ctrl, text="Apply Filters (Thrust/Lift Only)", variable=self.apply_filters_var, command=lambda: self.update_plot()).grid(row=1, column=9, padx=(6, 6), sticky=tk.W)
        self.apply_arduino_filters_var = tk.BooleanVar()
        ttk.Checkbutton(ctrl, text="Apply Arduino Filters", variable=self.apply_arduino_filters_var, command=lambda: self.update_plot()).grid(row=1, column=10, padx=(6, 6), sticky=tk.W)

        # Processing params row
        ttk.Label(ctrl, text="Median Window:").grid(row=2, column=0, sticky=tk.W)
        self.median_window_var = tk.StringVar(value="11")
        ttk.Entry(ctrl, width=8, textvariable=self.median_window_var).grid(row=2, column=1)
        ttk.Label(ctrl, text="Sampling Rate (Hz):").grid(row=2, column=2, sticky=tk.W)
        self.sampling_rate_var = tk.StringVar(value="500")
        ttk.Entry(ctrl, width=8, textvariable=self.sampling_rate_var).grid(row=2, column=3)
        ttk.Label(ctrl, text="Cutoff Freq (Hz):").grid(row=2, column=4, sticky=tk.W)
        self.cutoff_freq_var = tk.StringVar(value="4.0")
        ttk.Entry(ctrl, width=8, textvariable=self.cutoff_freq_var).grid(row=2, column=5)
        ttk.Label(ctrl, text="Arduino Median Window:").grid(row=2, column=6, sticky=tk.W)
        self.arduino_median_window_var = tk.StringVar(value="21")
        ttk.Entry(ctrl, width=8, textvariable=self.arduino_median_window_var).grid(row=2, column=7)

        # Action buttons
        self.detect_btn = ttk.Button(ctrl, text="Detect Trials", command=self.detect_trials)
        self.detect_btn.grid(row=2, column=8, padx=(12, 6))
        self.align_btn = ttk.Button(ctrl, text="Align & Plot Trials", command=self.align_and_plot_trials)
        self.align_btn.grid(row=2, column=9, padx=(6, 0))

        # Debug frame
        dbg = ttk.LabelFrame(main, text="Detection Debug", padding=6)
        dbg.grid(row=3, column=0, sticky=(tk.E, tk.W), pady=(0, 8))
        dbg.columnconfigure(0, weight=1)
        self.debug_text = tk.Text(dbg, height=7, width=120, font=("Courier", 9))
        self.debug_text.grid(row=0, column=0, sticky=(tk.E, tk.W))
        self.debug_text.insert(1.0, "Ready. Click Detect Trials to view debug logs.\n")

        # Matplotlib figure (3 rows: thrust, lift, arduino)
        fig_frame = ttk.LabelFrame(main, text="Trial Visualization", padding=8)
        fig_frame.grid(row=4, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        fig_frame.columnconfigure(0, weight=1)
        fig_frame.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax_thrust = self.fig.add_subplot(3, 1, 1)
        self.ax_lift = self.fig.add_subplot(3, 1, 2)
        self.ax_arduino = self.fig.add_subplot(3, 1, 3)
        self.canvas = FigureCanvasTkAgg(self.fig, fig_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    # --------------- Data loading ---------------
    def _auto_load_latest(self):
        # Preferred raw Paddle files (update if needed)
        paths = [
            os.path.join('data', 'raw', 'Master_Data_Set_Backup', '19-Oct-2022_results_PaddleStroke.mat'),
            os.path.join('data', 'raw', 'Raw_Experimental_Data', '19-Oct-2022_Paddle_Stroke_Flipper_Results', '19-Oct-2022_results_PaddleStroke.mat'),
            os.path.join('data', 'raw', 'Raw_Experimental_Data', '27-Oct-2022_Power_Stroke_Flipper_Results', '27-Oct-2022_results_PaddleStroke.mat'),
        ]
        existing = [p for p in paths if os.path.exists(p)]
        if not existing:
            messagebox.showerror("Error", "No Paddle .mat files found. Please add the raw files.")
            return
        self._load_mat_trials(existing)

    def _load_mat_trials(self, paths):
        try:
            self.groups.clear(); self.params_by_group.clear(); self.data_by_group.clear(); self.mat_paths = list(paths)
            # mapping
            sweep_map = {60.0: 70.0, 75.0: 80.0, 90.0: 90.0, 105.0: 100.0}
            flow_map = {0.0: 0.0, 70.0: 0.1}
            for p in paths:
                d = mat73.loadmat(p)
                results = d.get('results', {})
                data_list = results.get('data', [])
                params_list = results.get('parameters', [])
                if not isinstance(data_list, list) or not isinstance(params_list, list):
                    continue
                n = min(len(data_list), len(params_list))
                for i in range(n):
                    trial = data_list[i]
                    params = params_list[i]
                    if not hasattr(trial, 'shape') or trial.shape[1] < 3 or params is None:
                        continue
                    period = float(params[0])
                    sweep_raw = abs(float(params[1])); sweep = sweep_map.get(sweep_raw, sweep_raw)
                    twist = abs(float(params[2]))
                    flow_raw = float(params[3]); flow = flow_map.get(flow_raw, flow_raw)
                    # Channels: [thrust, lift, arduino] inferred from ranges
                    thrust = trial[:, 0]; lift = trial[:, 1]; arduino = trial[:, 2]
                    ch = np.vstack([thrust, lift, arduino])  # shape (3, T)
                    key = (flow, sweep, twist, period)
                    if key not in self.data_by_group:
                        self.data_by_group[key] = {'trials': []}
                        self.params_by_group[key] = dict(flow=flow, sweep=sweep, twist=twist, period=period, num_trials=0)
                        self.groups.append(key)
                    self.data_by_group[key]['trials'].append(ch)
                    self.params_by_group[key]['num_trials'] += 1
            # Populate combo boxes
            flows = sorted({k[0] for k in self.groups})
            sweeps = sorted({k[1] for k in self.groups})
            twists = sorted({k[2] for k in self.groups})
            periods = sorted({k[3] for k in self.groups})
            self.flow_cb['values'] = [str(v) for v in flows]
            self.sweep_cb['values'] = [str(int(v)) for v in sweeps]
            self.twist_cb['values'] = [str(int(v)) for v in twists]
            self.period_cb['values'] = [str(v) for v in periods]
            if flows: self.flow_cb.set(str(flows[0]))
            if sweeps: self.sweep_cb.set(str(int(sweeps[0])))
            if twists: self.twist_cb.set(str(int(twists[0])))
            if periods: self.period_cb.set(str(periods[-1]))
            self.status_lbl.config(text=f"Loaded {len(self.groups)} parameter groups from {len(paths)} file(s)", foreground="green")
            # After loading, show raw first trial trace to mirror Power behavior
            if self.groups:
                self.current_group = self.groups[0]
                self.update_plot()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load HDF5: {e}")

    # --------------- Interaction ---------------
    def _load_selected_group(self):
        if not self.groups:
            return
        try:
            flow = float(self.flow_cb.get()); sweep = float(self.sweep_cb.get()); twist = float(self.twist_cb.get()); period = float(self.period_cb.get())
        except Exception:
            messagebox.showerror("Error", "Invalid selection values.")
            return
        # Find matching group
        matches = [g for g in self.groups if abs(g[0]-flow)<1e-6 and abs(g[1]-sweep)<1e-6 and abs(g[2]-twist)<1e-6 and abs(g[3]-period)<1e-6]
        if not matches:
            messagebox.showerror("Not Found", "No matching parameter group found.")
            return
        self.current_group = matches[0]
        p = self.params_by_group[self.current_group]
        self.status_lbl.config(text=f"Selected group: flow={p['flow']}, sweep={p['sweep']}, twist={p['twist']}, period={p['period']} | trials={p['num_trials']}", foreground="blue")
        # Set trial length default from period combobox
        try:
            self.set_trial_length_for_period(float(self.period_cb.get()))
        except Exception:
            self.set_trial_length_for_period(p['period'])
        # Show raw first trial
        self.update_plot()

    # ----- Power-like processing helpers -----
    def apply_zero_correction(self, data_3xT: np.ndarray) -> np.ndarray:
        if not self.zero_correction_var.get():
            return data_3xT
        d = data_3xT.copy()
        # subtract mean of first 100 samples for thrust/lift
        d[0, :] = d[0, :] - float(np.mean(d[0, :100]))
        d[1, :] = d[1, :] - float(np.mean(d[1, :100]))
        return d

    def apply_data_filters(self, data_3xT: np.ndarray) -> np.ndarray:
        if not self.apply_filters_var.get():
            return data_3xT
        try:
            mw = int(self.median_window_var.get()); fs = float(self.sampling_rate_var.get()); cf = float(self.cutoff_freq_var.get())
        except Exception:
            mw, fs, cf = 11, 500.0, 4.0
        # ensure odd
        if mw % 2 == 0:
            mw += 1
        from scipy.signal import medfilt, firwin, filtfilt
        out = data_3xT.copy()
        # median filter thrust/lift
        out[0, :] = medfilt(out[0, :], kernel_size=mw)
        out[1, :] = medfilt(out[1, :], kernel_size=mw)
        # low-pass thrust/lift
        wn = (2.0 / fs) * cf
        b = firwin(1001, wn, window=('kaiser', 1))
        out[0, :] = filtfilt(b, [1], out[0, :])
        out[1, :] = filtfilt(b, [1], out[1, :])
        # arduino unchanged here
        return out

    def apply_arduino_filters(self, arduino: np.ndarray) -> np.ndarray:
        if not self.apply_arduino_filters_var.get():
            return arduino
        try:
            mw = int(self.arduino_median_window_var.get())
        except Exception:
            mw = 21
        if mw % 2 == 0:
            mw += 1
        from scipy.signal import medfilt
        return medfilt(arduino, kernel_size=mw)

    def update_plot(self):
        # Show raw first trial of current group
        self.ax_thrust.clear(); self.ax_lift.clear(); self.ax_arduino.clear()
        if not self.current_group:
            self.canvas.draw(); return
        trials = self.data_by_group[self.current_group]['trials']
        if not trials:
            self.canvas.draw(); return
        fs = float(self.sampling_rate_var.get()) if self.sampling_rate_var.get() else 500.0
        d = trials[0]
        d = self.apply_zero_correction(d)
        d = self.apply_data_filters(d)
        ard = self.apply_arduino_filters(d[2, :])
        t = np.arange(d.shape[1]) / fs
        self.ax_thrust.plot(t, d[0, :], 'b-', linewidth=1)
        self.ax_lift.plot(t, d[1, :], 'r-', linewidth=1)
        self.ax_arduino.plot(t, ard, 'g-', linewidth=1)
        self.ax_thrust.set_title('Thrust (raw)'); self.ax_thrust.set_ylabel('Force (a.u.)'); self.ax_thrust.grid(True, alpha=0.3)
        self.ax_lift.set_title('Lift (raw)'); self.ax_lift.set_ylabel('Force (a.u.)'); self.ax_lift.grid(True, alpha=0.3)
        self.ax_arduino.set_title('Arduino (raw)'); self.ax_arduino.set_xlabel('Time (s)'); self.ax_arduino.set_ylabel('Signal'); self.ax_arduino.grid(True, alpha=0.3)
        try:
            self.ax_thrust.set_ylim(float(self.t_ymin.get()), float(self.t_ymax.get()))
            self.ax_lift.set_ylim(float(self.l_ymin.get()), float(self.l_ymax.get()))
        except Exception:
            pass
        self.fig.tight_layout(); self.canvas.draw()

    def detect_trials(self):
        # Paddle data: each parameter group has one long trace with multiple trials (high/low Arduino periods)
        self.detected_trials = {'starts': [], 'ends': [], 'num_trials': 0, 'low_band_max': None, 'high_band_min': None, 'trial_list': []}
        if not self.current_group:
            return
        trials = self.data_by_group[self.current_group]['trials']
        if not trials:
            return
        try:
            before = int(self.before_trial_include.get()); tl = int(self.trial_length.get())
            low_t = float(self.low_thr.get()); high_t = float(self.high_thr.get())
        except Exception:
            before, tl, low_t, high_t = 10, 300, 1.5, 2.0
        fs = float(self.sampling_rate_var.get()) if self.sampling_rate_var.get() else 500.0
        
        # Debug
        try:
            self.debug_text.delete(1.0, tk.END)
        except Exception:
            pass
        def dbg(msg: str):
            try:
                self.debug_text.insert(tk.END, msg + "\n"); self.debug_text.see(tk.END)
            except Exception:
                pass
        
        dbg(f"Paddle: Finding multiple trials within long trace")
        dbg(f"Parameters: before={before} tl={tl} low={low_t} high={high_t}")
        
        # Process the long trace
        tr = trials[0]  # One long trace per group
        d = self.apply_zero_correction(tr)
        d = self.apply_data_filters(d)
        ard = self.apply_arduino_filters(d[2, :])
        
        # Find Arduino high/low periods
        base = float(np.median(ard[:50])) if ard.size >= 50 else float(np.median(ard))
        a = ard - base
        a[a < 0] = 0.0
        hb = a >= high_t  # High band mask
        
        dbg(f"Arduino: min={float(np.min(ard)):.2f} max={float(np.max(ard)):.2f} base={base:.2f}")
        dbg(f"High band samples: {np.sum(hb)} / {len(hb)} ({100*np.sum(hb)/len(hb):.1f}%)")
        dbg(f"High threshold: {high_t}, Low threshold: {low_t}")
        
        # Show first 20 samples of Arduino signal for debugging
        dbg(f"First 20 Arduino samples: {ard[:20].tolist()}")
        dbg(f"First 20 high band mask: {hb[:20].tolist()}")
        
        # Find all rising and falling edges
        rising = np.where((hb[1:] & (~hb[:-1])))[0] + 1
        falling = np.where((~hb[1:] & hb[:-1]))[0] + 1
        
        # Handle case where trace starts high
        if hb[0]:
            rising = np.concatenate([np.array([0]), rising])
        # Handle case where trace ends high
        if hb[-1]:
            falling = np.concatenate([falling, np.array([len(hb)])])
        
        dbg(f"Rising edges: {rising[:10]}... (total: {rising.size})")
        dbg(f"Falling edges: {falling[:10]}... (total: {falling.size})")
        
        # Show Arduino values around first few edges for debugging
        if rising.size > 0:
            for i, edge in enumerate(rising[:3]):
                start_idx = max(0, edge-5)
                end_idx = min(len(ard), edge+5)
                dbg(f"Rising edge {i+1} at {edge}: Arduino values around = {ard[start_idx:end_idx].tolist()}")
        if falling.size > 0:
            for i, edge in enumerate(falling[:3]):
                start_idx = max(0, edge-5)
                end_idx = min(len(ard), edge+5)
                dbg(f"Falling edge {i+1} at {edge}: Arduino values around = {ard[start_idx:end_idx].tolist()}")
        
        # Pair up rising/falling edges to find trial periods
        trial_starts = []
        trial_ends = []
        
        for i, rise in enumerate(rising):
            # Find the next falling edge after this rising edge
            fall_candidates = falling[falling > rise]
            if len(fall_candidates) > 0:
                fall = fall_candidates[0]
                # Check if this is a reasonable trial duration
                duration = fall - rise
                if duration >= 50:  # At least 50 samples (0.1s at 500Hz)
                    trial_starts.append(rise)
                    trial_ends.append(fall)
                    dbg(f"Trial {len(trial_starts)}: rise={rise} fall={fall} duration={duration} samples ({duration/fs:.2f}s)")
        
        dbg(f"Found {len(trial_starts)} complete trials")
        
        if len(trial_starts) == 0:
            dbg("No complete trials found - using start of trace")
            trial_starts = [0]
            trial_ends = [min(tl, d.shape[1])]
        
        # Apply selection logic: discard first, use next 5
        if len(trial_starts) >= 6:
            trial_starts = trial_starts[1:6]
            trial_ends = trial_ends[1:6]
            dbg("Applied selection: discarded first, kept next 5")
        elif len(trial_starts) >= 2:
            trial_starts = trial_starts[1:]
            trial_ends = trial_ends[1:]
            dbg("Applied selection: discarded first, kept remaining")
        
        # Convert to start/end indices with before_trial_include
        for i, (start_rise, end_fall) in enumerate(zip(trial_starts, trial_ends)):
            start = start_rise - before
            start = max(0, start)
            end = min(start + tl, d.shape[1])
            self.detected_trials['starts'].append(start)
            self.detected_trials['ends'].append(end)
            self.detected_trials['trial_list'].append(0)  # Always use trial 0 (the long trace)
        
        self.detected_trials['num_trials'] = len(self.detected_trials['trial_list'])
        self.detected_trials['low_band_max'] = low_t
        self.detected_trials['high_band_min'] = high_t
        
        dbg(f"Final selection: {self.detected_trials['num_trials']} trials")
        for i, (start, end) in enumerate(zip(self.detected_trials['starts'], self.detected_trials['ends'])):
            dbg(f"  Trial {i}: start={start} end={end} t=({start/fs:.3f}s,{end/fs:.3f}s)")
        
        # Show detection
        self.update_plot_with_detection()

    def update_plot_with_detection(self):
        self.ax_thrust.clear(); self.ax_lift.clear(); self.ax_arduino.clear()
        if not self.current_group or not self.detected_trials or self.detected_trials['num_trials'] == 0:
            self.canvas.draw(); return
        trials = self.data_by_group[self.current_group]['trials']
        fs = float(self.sampling_rate_var.get()) if self.sampling_rate_var.get() else 500.0
        idx = self.detected_trials['trial_list'][0]
        start = self.detected_trials['starts'][0]; end = self.detected_trials['ends'][0]
        d = trials[idx]
        d = self.apply_zero_correction(d); d = self.apply_data_filters(d); ard = self.apply_arduino_filters(d[2, :])
        t = np.arange(d.shape[1]) / fs
        self.ax_thrust.plot(t, d[0, :], 'b-', linewidth=1)
        self.ax_lift.plot(t, d[1, :], 'r-', linewidth=1)
        self.ax_arduino.plot(t, ard, 'g-', linewidth=1)
        # thresholds
        self.ax_arduino.axhline(y=self.detected_trials['low_band_max'], color='orange', linestyle='--', alpha=0.7)
        self.ax_arduino.axhline(y=self.detected_trials['high_band_min'], color='red', linestyle='--', alpha=0.7)
        # shade selected window
        self.ax_arduino.axvspan(t[start], t[end-1] if end>start else t[start], alpha=0.2, color='yellow')
        self.ax_thrust.set_title('Thrust (raw) with detection'); self.ax_thrust.set_ylabel('Force (a.u.)'); self.ax_thrust.grid(True, alpha=0.3)
        self.ax_lift.set_title('Lift (raw) with detection'); self.ax_lift.set_ylabel('Force (a.u.)'); self.ax_lift.grid(True, alpha=0.3)
        self.ax_arduino.set_title('Arduino (raw) with detection'); self.ax_arduino.set_xlabel('Time (s)'); self.ax_arduino.set_ylabel('Signal'); self.ax_arduino.grid(True, alpha=0.3)
        self.fig.tight_layout(); self.canvas.draw()

    def align_and_plot_trials(self):
        self.ax_thrust.clear(); self.ax_lift.clear(); self.ax_arduino.clear()
        if not self.current_group or not self.detected_trials or self.detected_trials['num_trials'] == 0:
            messagebox.showerror("Error", "No trials detected. Please run trial detection first.")
            self.canvas.draw(); return
        trials = self.data_by_group[self.current_group]['trials']
        fs = float(self.sampling_rate_var.get()) if self.sampling_rate_var.get() else 500.0
        try:
            tl = int(self.trial_length.get())
        except Exception:
            tl = 150
        aligned = []
        for idx, start, end in zip(self.detected_trials['trial_list'], self.detected_trials['starts'], self.detected_trials['ends']):
            d = trials[idx]
            d = self.apply_zero_correction(d); d = self.apply_data_filters(d); d[2, :] = self.apply_arduino_filters(d[2, :])
            seg = d[:, start:end]
            if seg.shape[1] < tl:
                pad = np.zeros((3, tl)); pad[:, :seg.shape[1]] = seg; seg = pad
            else:
                seg = seg[:, :tl]
            aligned.append(seg)
        if not aligned:
            self.canvas.draw(); return
        t = np.arange(tl) / fs
        # Plot all detected trials
        for i, seg in enumerate(aligned):
            alpha = 0.6 if len(aligned) > 1 else 1.0
            self.ax_thrust.plot(t, seg[0, :], color='tab:blue', alpha=alpha, linewidth=1)
            self.ax_lift.plot(t, seg[1, :], color='tab:red', alpha=alpha, linewidth=1)
            self.ax_arduino.plot(t, seg[2, :], color='tab:green', alpha=alpha, linewidth=1)
        
        # Plot mean if multiple trials
        if len(aligned) > 1:
            mean_seg = np.mean(np.stack(aligned, axis=0), axis=0)
            self.ax_thrust.plot(t, mean_seg[0, :], color='black', linewidth=2, label='Mean')
            self.ax_lift.plot(t, mean_seg[1, :], color='black', linewidth=2, label='Mean')
            self.ax_arduino.plot(t, mean_seg[2, :], color='black', linewidth=2, label='Mean')
        # Ranges
        try:
            self.ax_thrust.set_ylim(float(self.t_ymin.get()), float(self.t_ymax.get()))
            self.ax_lift.set_ylim(float(self.l_ymin.get()), float(self.l_ymax.get()))
        except Exception:
            pass
        self.ax_thrust.set_title('Thrust Force - Aligned Trials'); self.ax_thrust.set_ylabel('Force (a.u.)'); self.ax_thrust.grid(True, alpha=0.3)
        self.ax_lift.set_title('Lift Force - Aligned Trials'); self.ax_lift.set_ylabel('Force (a.u.)'); self.ax_lift.grid(True, alpha=0.3)
        self.ax_arduino.set_title('Arduino Signal - Aligned Trials'); self.ax_arduino.set_xlabel('Time (s)'); self.ax_arduino.set_ylabel('Signal'); self.ax_arduino.grid(True, alpha=0.3)
        self.fig.tight_layout(); self.canvas.draw()

    def set_trial_length_for_period(self, period: float):
        try:
            period = float(period)
        except Exception:
            return
        # Set trial length based on period
        if abs(period - 1.75) < 1e-6:
            self.trial_length.set("200")
        elif abs(period - 2.25) < 1e-6:
            self.trial_length.set("290")
        else:
            # Default fallback
            self.trial_length.set("200")

    def _on_period_change(self):
        try:
            self.set_trial_length_for_period(float(self.period_cb.get()))
        except Exception:
            pass


def main():
    root = tk.Tk()
    app = PaddleTrialAlignmentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


