#!/usr/bin/env python3
"""
Raw Data Organizer & Plotter GUI (Power / Paddle / Full)

Purpose
- Point at a folder with raw .mat files
- List candidate files (07-Oct/14-Oct etc.)
- Load selected file, discover trials + channels (time, thrust, lift, Arduino forces)
- Plot raw channels with simple axes/legend controls

Notes
- Loader is best-effort: tries scipy (MAT v5), mat73 (MAT v7.3), and h5py crawl
- Time channel candidates: ['time','Time','t']
- Channel discovery scans keys for substrings: ['thrust','lift','arduino','fx','fy','force']

Run
  python analysis/gui/raw_data_organizer_gui.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QFileDialog, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def try_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None


scipy_io = try_import('scipy.io')
mat73 = try_import('mat73')
h5py = try_import('h5py')


def load_mat(path: str) -> Dict[str, Any]:
    # Try scipy MAT v5
    if scipy_io is not None:
        try:
            d = scipy_io.loadmat(path, squeeze_me=True, struct_as_record=False)
            return {k: v for k, v in d.items() if not k.startswith('__')}
        except Exception:
            pass
    # Try mat73 MAT v7.3
    if mat73 is not None:
        try:
            d = mat73.loadmat(path)
            return d
        except Exception:
            pass
    # Fallback: attempt to list with h5py and pull numeric datasets
    result: Dict[str, Any] = {}
    if h5py is not None:
        try:
            with h5py.File(path, 'r') as f:
                def collect(name: str, obj: Any):
                    if isinstance(obj, h5py.Dataset):
                        try:
                            result[name] = np.array(obj)
                        except Exception:
                            pass
                f.visititems(collect)
        except Exception:
            pass
    return result


def discover_trials(d: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return list of trials and discovered channel names.
    Each trial dict has keys: 'time' + channel names.
    """
    trials: List[Dict[str, Any]] = []

    # Candidates for time key
    time_keys = ['time', 'Time', 't']
    # Channel name substrings (lowercase)
    chan_tokens = ['thrust', 'lift', 'arduino', 'fx', 'fy', 'force']

    # Helper: extract array safely
    def as_array(x: Any) -> np.ndarray | None:
        try:
            arr = np.asarray(x)
            if arr.size == 0:
                return None
            return arr
        except Exception:
            return None

    # Try struct-array style "trials"
    for key in ['trials', 'Trials', 'experiment', 'experiments', 'data', 'Data']:
        obj = d.get(key)
        if obj is None:
            continue
        try:
            it = list(obj if isinstance(obj, (list, tuple)) else np.atleast_1d(obj))
        except Exception:
            continue
        tmp: List[Dict[str, Any]] = []
        for item in it:
            tr: Dict[str, Any] = {}
            # time
            for tk in time_keys:
                if hasattr(item, tk):
                    t = as_array(getattr(item, tk))
                    if t is not None:
                        tr['time'] = t.ravel()
                        break
            # channels by attribute scan
            for name in dir(item):
                if name.startswith('_'):
                    continue
                val = getattr(item, name)
                arr = as_array(val)
                if arr is None:
                    continue
                name_l = name.lower()
                if any(tok in name_l for tok in chan_tokens):
                    tr[name] = arr.ravel()
            if 'time' in tr:
                tmp.append(tr)
        if tmp:
            trials = tmp
            break

    # If not found, try columnar arrays: shape [n_samples, n_trials]
    if not trials:
        time_arr = None
        for tk in time_keys:
            if tk in d:
                time_arr = as_array(d[tk])
                if time_arr is not None:
                    break
        if time_arr is not None:
            # discover channel arrays with matching first dim
            chan_arrays: Dict[str, np.ndarray] = {}
            for k, v in d.items():
                arr = as_array(v)
                if arr is None or arr.ndim < 1:
                    continue
                if arr.shape[0] != time_arr.shape[0]:
                    continue
                kl = k.lower()
                if any(tok in kl for tok in chan_tokens):
                    chan_arrays[k] = arr
            # build per-trial dicts
            n_trials = 1
            for a in chan_arrays.values():
                if a.ndim == 2:
                    n_trials = max(n_trials, a.shape[1])
            for j in range(n_trials):
                tr: Dict[str, Any] = {'time': (time_arr[:, j] if time_arr.ndim == 2 else time_arr).ravel()}
                for name, arr in chan_arrays.items():
                    col = arr[:, j] if arr.ndim == 2 else arr
                    tr[name] = col.ravel()
                trials.append(tr)

    # Collect union of channel names (excluding 'time')
    chan_names: List[str] = []
    if trials:
        keys = set()
        for tr in trials:
            for k in tr.keys():
                if k == 'time':
                    continue
                keys.add(k)
        chan_names = sorted(keys)
    return trials, chan_names


class RawOrganizerGUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Raw Data Organizer & Plotter")
        self.setGeometry(50, 50, 1400, 900)
        self.trials: List[Dict[str, Any]] = []
        self.chan_names: List[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Folder picker
        fp = QHBoxLayout()
        fp.addWidget(QLabel("Folder:"))
        self.dir_edit = QLineEdit(os.path.join('data','raw','Master_Data_Set_Backup'))
        fp.addWidget(self.dir_edit)
        browse = QPushButton("Browse…"); browse.clicked.connect(self.on_browse)
        fp.addWidget(browse)
        scan = QPushButton("Scan"); scan.clicked.connect(self.on_scan)
        fp.addWidget(scan)
        root.addLayout(fp)

        # File list + channel toggles
        top = QHBoxLayout()
        self.file_list = QListWidget(); self.file_list.itemSelectionChanged.connect(self.on_file_selected)
        top.addWidget(self.file_list, 2)

        chan_box = QGroupBox("Channels")
        chan_layout = QVBoxLayout(chan_box)
        self.chan_checks: Dict[str, QCheckBox] = {}
        self.legend_check = QCheckBox("Legend"); self.legend_check.setChecked(True)
        chan_layout.addWidget(self.legend_check)
        top.addWidget(chan_box, 1)
        self.chan_box = chan_box
        root.addLayout(top)

        # Axes controls
        axes = QHBoxLayout()
        axes.addWidget(QLabel("X min")); self.xmin = QLineEdit(""); self.xmin.setPlaceholderText("auto"); self.xmin.setMaximumWidth(80); axes.addWidget(self.xmin)
        axes.addWidget(QLabel("X max")); self.xmax = QLineEdit(""); self.xmax.setPlaceholderText("auto"); self.xmax.setMaximumWidth(80); axes.addWidget(self.xmax)
        axes.addWidget(QLabel("Y min")); self.ymin = QLineEdit(""); self.ymin.setPlaceholderText("auto"); self.ymin.setMaximumWidth(80); axes.addWidget(self.ymin)
        axes.addWidget(QLabel("Y max")); self.ymax = QLineEdit(""); self.ymax.setPlaceholderText("auto"); self.ymax.setMaximumWidth(80); axes.addWidget(self.ymax)
        plot_btn = QPushButton("Plot"); plot_btn.clicked.connect(self.on_plot)
        axes.addWidget(plot_btn)
        root.addLayout(axes)

        # Figure
        self.fig = Figure(figsize=(10,6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        root.addWidget(self.canvas)

        self.statusBar().showMessage("Ready")
        self.on_scan()

    def on_browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose raw data folder", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)
            self.on_scan()

    def on_scan(self) -> None:
        self.file_list.clear()
        base = self.dir_edit.text().strip()
        if not os.path.isdir(base):
            self.statusBar().showMessage("Folder not found")
            return
        # list .mat files
        mats: List[str] = []
        for root, _, files in os.walk(base):
            for fn in files:
                if fn.lower().endswith('.mat'):
                    mats.append(os.path.join(root, fn))
        mats.sort()
        for p in mats:
            self.file_list.addItem(p)
        self.statusBar().showMessage(f"Found {len(mats)} .mat files")

    def on_file_selected(self) -> None:
        items = self.file_list.selectedItems()
        if not items:
            return
        path = items[0].text()
        d = load_mat(path)
        self.trials, self.chan_names = discover_trials(d)
        # rebuild channel checkboxes
        for i in reversed(range(self.chan_box.layout().count())):
            w = self.chan_box.layout().itemAt(i).widget()
            if isinstance(w, QCheckBox) and w is not self.legend_check:
                w.setParent(None)
        self.chan_checks.clear()
        for name in self.chan_names:
            cb = QCheckBox(name)
            # default on for thrust/lift/arduino if present
            low = name.lower()
            if any(tok in low for tok in ['thrust','lift','arduino','fx','fy','force']):
                cb.setChecked(True)
            self.chan_box.layout().addWidget(cb)
            self.chan_checks[name] = cb
        self.statusBar().showMessage(f"Loaded {len(self.trials)} trials; channels: {len(self.chan_names)}")

    def on_plot(self) -> None:
        self.ax.clear(); self.ax.grid(True, alpha=0.3)
        if not self.trials:
            self.canvas.draw()
            return
        # plot the first trial for now (could add trial selector later)
        tr = self.trials[0]
        t = np.asarray(tr.get('time'))
        if t is None or t.size == 0:
            self.canvas.draw(); return
        # normalize t to start at zero for readability
        t0 = t.min(); t = t - t0
        plotted = 0
        for name, cb in self.chan_checks.items():
            if not cb.isChecked():
                continue
            y = tr.get(name)
            if y is None:
                continue
            y = np.asarray(y)
            if y.size != t.size:
                continue
            self.ax.plot(t, y, label=name)
            plotted += 1
        # axes limits
        def _f(s: str) -> float | None:
            try:
                return float(s)
            except Exception:
                return None
        xmin = _f(self.xmin.text()); xmax = _f(self.xmax.text())
        ymin = _f(self.ymin.text()); ymax = _f(self.ymax.text())
        if xmin is not None or xmax is not None:
            xr = self.ax.get_xlim();
            lo = xmin if xmin is not None else xr[0]; hi = xmax if xmax is not None else xr[1]
            if hi <= lo: hi = lo + max(1.0, abs(lo)*0.05 + 1e-6)
            self.ax.set_xlim(lo, hi)
        if ymin is not None or ymax is not None:
            yr = self.ax.get_ylim();
            lo = ymin if ymin is not None else yr[0]; hi = ymax if ymax is not None else yr[1]
            if hi <= lo: hi = lo + max(1.0, abs(lo)*0.05 + 1e-6)
            self.ax.set_ylim(lo, hi)
        if self.legend_check.isChecked() and plotted > 0:
            self.ax.legend()
        self.ax.set_xlabel('Time (s, zeroed)')
        self.ax.set_ylabel('Force (raw units)')
        self.ax.set_title('Raw Channels (first trial)')
        self.canvas.draw()


def main() -> int:
    app = QApplication(sys.argv)
    w = RawOrganizerGUI(); w.show()
    return app.exec_()


if __name__ == '__main__':
    raise SystemExit(main())



