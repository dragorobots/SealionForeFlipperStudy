# Power Stroke Processing Pipeline

This folder contains scripts and docs for converting raw Power stroke `.mat` files
into a GUI‑compatible HDF5 dataset.

## Inputs
- data/raw/Master_Data_Set_Backup/
  - 07-Oct-2022_results_PowerStroke.mat
  - 14-Oct-2022_results_PowerStroke.mat

## Steps
1) Inspect structure (optional)
```
python analysis/power/inspect_power_mat.py data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat
```
2) Convert to HDF5 (normalized phase 0..1, grouped by parameters)
```
python analysis/power/power_to_hdf5.py \
  data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat \
  data/raw/Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat \
  --out data/processed/Power/PowerTraces_Complete_YYYY-MM-DD.h5
```

## Output Schema
```
experiments/exp_XXXX/
  parameters (attrs: flow, sweep, twist, stroke_period, overlap, experiment_id)
  thrust/mean_trace
  thrust/std_trace
  lift/mean_trace
  lift/std_trace
  time_vector  (phase 0..1)
```

This HDF5 can be loaded directly by `analysis/gui/full_stroke_overview_gui.py`.






