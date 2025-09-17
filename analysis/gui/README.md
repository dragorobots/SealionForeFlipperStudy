# Full-Stroke Overview Metrics GUI

Interactive GUI for visualizing full-stroke experimental data from the Sea Lion AUV Flow Tank experiments.

## Features

### Visual Encodings
- **X-axis**: Twist parameter
- **Columns**: Sweep parameter  
- **Color**: Flow speed
- **Line style**: Stroke period
- **Marker shape**: Phase overlap

### Metrics Displayed
- Phase-mean thrust, phase-mean lift, resultant magnitude
- Peak thrust and peak lift with peak timing markers (normalized phase time)
- Phase-mean resultant angle

### Export Capabilities
- Interactive on-screen figure builder
- Export to PNG (high resolution)
- Export to PDF (vector format)
- Export to CSV (data table)

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the GUI:
```bash
python full_stroke_overview_gui.py
```

## Usage

1. **Load Data**: Click "Load HDF5 Data" to select your processed data file
   - Expected location: `data/processed/2025-01-27_ProcessedData/TrialTraces_Complete_2025-01-27.h5`

2. **Configure Plots**: Select which metrics to display and customize visual encodings

3. **Generate Plots**: Click "Generate Plots" to create the overview visualizations

4. **Export Results**: Use the export buttons to save plots and data in various formats

## Data Format

The GUI expects HDF5 files with the following structure:
- `trial_*` groups containing trial data
- `metadata` group with experiment metadata
- `experiment_parameters` group with parameter values

## File Structure

```
analysis/gui/
├── full_stroke_overview_gui.py    # Main GUI application
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## Dependencies

- Python 3.7+
- PyQt5 for GUI framework
- matplotlib for plotting
- h5py for HDF5 data handling
- pandas for data manipulation
- numpy for numerical operations
- seaborn for enhanced plotting

## Author

Generated for Sea Lion AUV Flow Tank Analysis
Date: 2025-01-27

