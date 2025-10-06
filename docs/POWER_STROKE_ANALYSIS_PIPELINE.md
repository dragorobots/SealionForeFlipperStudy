Power Stroke Analysis Pipeline

Overview

This document captures the full end‑to‑end process we implemented for Power stroke analysis: from raw MATLAB data to standardized HDF5, interactive alignment/QA, automated batch processing, and the final overview GUI. It explains the design choices, common pitfalls, and how to reproduce each step.

Data Sources

- Raw MATLAB v7.3 files (HDF5 under the hood):
  - 14-Oct-2022_results_PowerStroke.mat
  - 07-Oct-2022_results_PowerStroke.mat
- Sampling rate: 500 Hz
- Channels: thrust, lift, arduino (sync)

Key Corrections and Normalizations

- Roll/yaw signs: Flip negatives to positive for both roll (twist) and yaw.
- Yaw relabeling: Original labels [-90°, -75°, -60°] corrected to [90°, 80°, 70°].
- Flow mapping (motor power → m/s): 0 → 0.00, 28 → 0.05, 70 → 0.10, 100 → 0.13.
- Per‑experiment parameters: We persist [period, yaw, roll, flow_speed] per experiment to avoid inferring Cartesian products and to preserve the irregular twist set specific to Power stroke.

Irregular Twist Set (Power)

Power stroke uses a larger, irregular set of twist angles (absolute degrees):

0, 15, 30, 35, 40, 45, 50, 55, 60, 75, 90

Why: This reflects the experimental program and differs from Full stroke; we use the labeled values rather than enforcing even spacing.

Step 1 – Convert Raw MATLAB → Standardized HDF5

Script: power_stroke_data_loader.py

What it does

- Reads v7.3 .mat files using h5py (required for HDF5‑backed MATLAB files).
- Extracts data and parameters in acquisition order.
- Applies corrections (sign flips, yaw relabeling, flow mapping).
- Saves a single consolidated HDF5:
  - data/processed/PowerStroke_Complete_YYYY-MM-DD.h5
  - Datasets:
    - data: float array (3, N_experiments, T)
    - settings: groups for period/yaw/roll/flow unique values
    - parameter_combinations: unique values (for convenience)
    - experiment_parameters: per‑experiment [period, yaw, roll, flow_speed] (critical for alignment of labels)
  - metadata: channels, sampling_rate, provenance, corrections applied

Why h5py instead of scipy.io.loadmat?

MATLAB v7.3 .mat files are HDF5. scipy.io.loadmat does not support these fully and throws NotImplementedError. Using h5py provides reliable structured access to nested cell arrays and datasets.

How to run (from repo root on Windows PowerShell)

```powershell
python .\power_stroke_data_loader.py
```

Common pitfalls addressed

- v7.3 read errors → switched to h5py.
- Handling MATLAB cell arrays → indexed via object references in HDF5.
- Object dtype in HDF5 attributes → stringify/JSON encode complex types.

Step 2 – Interactive Trial Alignment GUI (QA and method development)

File: analysis/good/Power/power_trial_alignment_gui.py

What it does

- Lets you select and view a single experiment (period/yaw/twist/flow) from the standardized HDF5.
- Applies data processing consistent with batch workflow:
  - Scale thrust/lift by 2.22 (to N).
  - Median + low‑pass filtering to thrust/lift only.
  - Never filter Arduino by default; a separate “Apply Arduino Filters” toggle exists for optional denoising.
- Trial detection from Arduino (two‑band logic):
  - Treats low band ~0 and high band ~3.5.
  - Detect transitions to high band as trial starts.
  - Merge starts <0.5s apart (use the later start) to suppress spurious noise.
  - Discard the first detected trial, use the next 5, discard remaining.
  - Trial length is fixed by period (no end detection):
    - Period 1.75 → 150 samples
    - Period 2.25 → 175 samples
  - “Before Trial Include (samples)” offset (default 10) lets you shift the window earlier.
- Plots individual trials (thrust, lift, arduino) and their mean; displays simple stats.

Why fixed trial lengths instead of detecting duration?

Power trials show reliable timing given the period; end detection on noisy/high‑band signals was brittle and added variability. Fixed lengths deliver consistent alignment and make batch processing robust.

Known differences vs Full stroke GUI

- Arduino never filtered by default; optional median filter is user‑driven.
- No phase overlap parameter in Power.
- Absolute time used (no normalization to [0,1]).

Step 3 – Automated Batch Processing (Aligned Means/Variances)

Script: analysis/good/Power/process_power_stroke_trials.py

What it does

- Loads PowerStroke_Complete_YYYY-MM-DD.h5 and uses experiment_parameters per experiment.
- Applies the same processing as the GUI:
  - Scale thrust/lift by 2.22; leave Arduino raw.
  - Median + low‑pass on thrust/lift only.
  - Trial detection with two‑band logic; merge close starts; discard first; take next 5.
  - Trial length fixed by period; include pre‑trial offset (10 samples in GUI; batch uses the same detection/selection without explicit pre‑offset in the saved mean traces).
- Computes per‑experiment mean and variance across extracted trials.
- Saves results to HDF5:
  - data/processed/power_stroke_aligned_trials.h5
  - One group per experiment (experiment_XXX) with:
    - attrs: period, yaw_amplitude, roll_angle (twist), flow_speed, num_trials, trial_length
    - datasets: thrust_mean, lift_mean, thrust_var, lift_var, time_vector, trial_starts

Why per‑experiment parameters?

Power twist angles are irregular and the acquisition ordering is specific to the sessions. Using saved per‑experiment labels guarantees that plotted/aggregated data match the true twist, yaw, flow, period, without relying on an assumed Cartesian enumeration.

How to run

```powershell
python .\analysis\good\Power\process_power_stroke_trials.py
```

Quick sanity checks

- time_vector length matches 150 (period 1.75) or 175 (period 2.25).
- time ranges ~0.30–0.35 s as expected (500 Hz sampling; includes pre‑trial shift in GUI when applicable).
- thrust/lift ranges reflect scaling to Newtons (2.22 factor).

Step 4 – Final Analysis GUI (Overview Metrics)

File: analysis/gui/power_stroke_overview_gui.py

What it does

- Loads power_stroke_aligned_trials.h5 and provides three overview panels:
  - Mean Force (mean thrust/lift vs twist) with decoupled variable selection.
  - Peak Location (time of the first peak for thrust AND the first peak for lift) vs twist.
  - Vector Plot (mean thrust vs mean lift, with selectable variable and color by flow).
- Absolute time only (no phase normalization); axes labeled in seconds.
- No phase overlap parameter (fully removed to avoid crashes).
- Twist selection: each tab shows a compact row of twist angle checkboxes to include/exclude specific twists in the plot.
- Default twist selection: only 0, 15, 30, 45, 60, 75, 90 are ON; any other available twists are OFF by default.
- Default flow set when varying flow: restricted to 0.0, 0.05, and 0.10 (0.13 excluded by default to reduce clutter; can be re‑enabled if we add flow checkboxes later).

Why first peak only on Peak Location?

Power strokes show a prominent early peak of physical interest; plotting the first significant extremum (after a short initial time >0.05s) stabilizes comparisons across parameters and avoids ambiguities with later oscillations.

How to run

```powershell
python .\analysis\gui\power_stroke_overview_gui.py
```

Design Rationale Summary

- h5py for v7.3: Robust access to nested HDF5 content vs. unsupported loadmat.
- Sign flips and yaw relabels: Aligns Power with Full conventions and corrects known label issues.
- Flow mapping: Converts controller setpoints to physical m/s for consistent analysis.
- Per‑experiment parameters: Preserves real acquisition ordering and irregular twist set.
- Arduino detection choices: Two‑band thresholding with merged starts is robust to noise; fixed durations eliminate end‑detection brittleness.
- Scaling/filtering: 2.22 scale for thrust/lift; median + low‑pass improves SNR while preserving transients; Arduino left unfiltered by default to keep transitions sharp.
- Absolute time: Avoids Full‑stroke‑specific normalization ranges; reflects true durations of Power cycles.
- GUI filters (twist/flow): Practical focus on the most relevant values by default while keeping flexibility.

Common Issues and Fixes (Chronology)

- loadmat NotImplementedError → switched to h5py for v7.3.
- HDF5 access TypeError (group slicing) → iterate keys/refs explicitly.
- HDF5 attribute dtype errors → JSON/str encode non‑scalars.
- Trial detection returned none → using wrong input file (ramp signal). Corrected to PowerStroke_Complete HDF5; added band detection, merging starts, fixed lengths.
- GUI “pt/overlap” references causing crashes → removed all overlap controls and code paths for Power.
- Plotting issues due to Full‑stroke normalization → removed normalization; use absolute time.
- Twist ordering mismatch → switched to per‑experiment parameters; verified unique twist set is irregular and respected throughout.

Repro Checklist

1) Convert raw MATLAB to consolidated HDF5 with corrections:
   - Run: power_stroke_data_loader.py
   - Output: data/processed/PowerStroke_Complete_YYYY-MM-DD.h5
2) Inspect/QA an experiment and refine detection parameters (optional):
   - Run: analysis/good/Power/power_trial_alignment_gui.py
3) Batch process aligned means/variances:
   - Run: analysis/good/Power/process_power_stroke_trials.py
   - Output: data/processed/power_stroke_aligned_trials.h5
4) Explore metrics and export figures:
   - Run: analysis/gui/power_stroke_overview_gui.py

Future Extensions

- Add flow selection checkboxes (0, 0.05, 0.10, 0.13) to all tabs like twists.
- Optional Arduino denoising presets for extremely noisy runs.
- Export consolidated CSV/Parquet with chosen twist/flow subsets for downstream modeling.


