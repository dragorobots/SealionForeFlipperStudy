# Read Before Proceeding

This document summarizes the end-to-end pipeline to convert MATLAB v7.3 experiment structs into publishable figures, and how to repeat it for Power and Paddle datasets.

## 1) Source Data (MATLAB v7.3 → HDF5)
- Files are v7.3 (HDF5). Use `h5py`, not `scipy.io.loadmat`.
- Per experiment we normalize to:
  - `/data/exp_XXX`: `(3, time)` → channels: thrust (0), lift (1), arduino (2)
  - `/zeros/exp_XXX`: baseline zeros `(3, Nzero)`
  - `/parameters/exp_XXX`: dataset `(4,1)` = `[period, yaw_amplitude, roll_angle, paddle_transition]`
  - `/metadata` attrs: `sampling_rate` (500), `duration_s` (30), `total_experiments`, etc.
- Flow speed is derived from date if not present per-experiment (20-Jan → 0.1 m/s, 30-Jan → 0.0 m/s) and mapped at read time.

## 2) Extraction (MAT → Unified HDF5)
- Script (support): `fullstroke_extract_complete_data.py` → produces `FullStroke_Complete_YYYY-MM-DD.h5`.
- Prunes to Full Stroke subset and standardizes shapes/attrs above.

## 3) Verify / Inspect
- `support/inspect_dataset.py` prints groups, shapes, parameter distributions; confirms Fs=500 Hz and ~30 s per experiment.

## 4) Full-Signal GUI
- `fullstroke_gui_analysis.py`
  - Parameter selectors; plots thrust/lift/arduino.
  - Processing: zero (thrust/lift), scale 2.22, median filter (odd window), low-pass FIR (Kaiser) with configurable cutoff (default ≈ 4 Hz). Arduino: median only.
  - Axis controls, fixed x=0–30 s, corrected channel order.

## 5) Trial Alignment GUI
- `trial_alignment_gui.py`
  - Manual controls: first offset, window length, inter-trial gap; overlays windows.
  - Auto detection (Arduino edges):
    1) First large negative jump → trial start
    2) First positive jump after start → trial end (duration)
    3) Next negative jump → inter-trial gap
    4) If first change is toward zero at t=0, ignore that trial
    5) Start with 5 trials; if overflow → 4 or error

## 6) Batch Processing (Automatic Trial Traces)
- `process_trial_traces.py` → `TrialTraces_Complete_YYYY-MM-DD.h5`
  - Detect trials (same logic), extract 5 equal-length windows (`length = int(duration*Fs)`).
  - Zero (thrust/lift) using zeros mean; scale 2.22; median filter; low-pass FIR (short taps if needed to avoid filtfilt padlen errors).
  - Save per experiment: `time_vector`, `thrust/lift` individual trials, `mean_trace`, `std_trace`; timing info; parameters.
  - Summary: `TrialTraces_Summary_YYYY-MM-DD.txt`.

## 7) Figure Publishing GUI (Means Overlay)
- `trial_traces_plot_gui.py`
  - Up to 10 dataset slots with selectors: Flow, Yaw, Roll, PT; Channel (Thrust/Lift).
  - Per-dataset style: color (HEX or palettes), line width, shaded variance (±variance), alpha.
  - Per-dataset legend: include toggle + custom label.
  - Global: axis ranges & ticks; labels/titles (toggle, text, font, size); legend on/off + placement; color scheme (Default, Color-blind friendly, Custom).
  - Publish to PNG: width/height (px), filename → `Figures/FullStroke/Traces_YYYY-MM-DD/`.

## How to Repeat for Power and Paddle
1) Inspect raw MATLAB files with `h5py` to confirm channel order, parameters present, Fs, duration.
2) Copy the extractor to `support/power_extract_complete_data.py` and `support/paddle_extract_complete_data.py`:
   - Normalize outputs to the exact schema above. If a parameter doesn’t exist (e.g., PT), write `NaN`.
   - Derive flow if needed (from date) or store a mapping in metadata.
3) Verify with `support/inspect_dataset.py`.
4) Validate trial detection in `trial_alignment_gui.py` (thresholds may need minor tuning if Arduino levels differ).
5) Run `process_trial_traces.py` pointing at the new HDF5, producing `TrialTraces_Complete_<Power|Paddle>_YYYY-MM-DD.h5`.
6) Use `trial_traces_plot_gui.py` to select and publish figures (it auto-discovers files under `data/processed/`).

## Common Pitfalls (and fixes we used)
- v7.3 files: must use `h5py`.
- Groups vs datasets: check types; only datasets have `.shape/.dtype`.
- Parameter shapes differ: standardize to `(4,1)` per experiment.
- Channel order differences: normalize at extraction or swap at load; keep consistent for GUIs.
- Flow not per-exp: derive from date; document in metadata.
- Short windows + FIR: reduce taps so `filtfilt` padlen < signal length.
- Off-by-one trial lengths: compute a single `trial_length_samples` and slice `start:start+length`.
- Fonts: use installed families (Default/Arial/etc.) if a specified family (e.g., Helvetica) isn’t present.

## File Map (stable entry points)
- Root:
  - `fullstroke_gui_analysis.py` (full-signal GUI)
  - `trial_alignment_gui.py` (layering GUI)
  - `process_trial_traces.py` (automatic sorter)
  - `trial_traces_plot_gui.py` (publishing GUI)
- Support utilities: `support/` (extractors, inspectors, runners)
- Outputs: `data/processed/…` HDF5 + summaries; published figures in `Figures/…`
