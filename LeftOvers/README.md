# Sea-lion Foreflipper Stroke Analysis — Repository Checkpoint (2025-09-09)

## Overview

This MATLAB-based repository analyzes sea lion-inspired flipper propulsion in Autonomous Underwater Vehicles (AUVs). The project studies experimental data from flow tank tests with a 3-DOF robotic flipper system to understand hydrodynamics and performance characteristics of bio-inspired swimming mechanisms.

**Stroke Definitions:**
- **Full stroke**: One complete swimming cycle from start to finish
- **Power stroke**: High-force propulsion phase of the stroke
- **Paddle stroke**: Low-force recovery or repositioning phase

## Directory Layout

```
├── Data_Collecting_Functions/     # Automated data collection scripts (7 files)
├── Old_Results_Workers/          # Legacy analysis scripts (11 files)
├── Stuff_For_Shraman/           # Specialized analysis tools (2 files)
├── Master_Data_Set_Backup/      # Core experimental datasets (6 files)
├── Standardized_Data_Sets/      # Processed/curated datasets (4 files)
├── Raw_Experimental_Data/       # Experimental session folders (10 folders)
├── Results/                     # Analysis results (currently empty)
├── Flipper_Videos/             # Video recordings
├── html/                       # Documentation and figures
├── *.m                         # Main analysis and control scripts (66 files)
└── README.md                   # This file
```

## Data Map

### Raw Experimental Data
| Path | Type | Experiments | Flow Speeds | Date | Size |
|------|------|-------------|-------------|------|------|
| `Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0.1 m/s | Jan 2023 | 37.8 MB |
| `Master_Data_Set_Backup/23-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0.05 m/s | Jan 2023 | 37.5 MB |
| `Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0 m/s | Jan 2023 | 37.4 MB |
| `Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat` | Power Stroke | 132 | 0, 100 | Oct 2022 | 18.8 MB |
| `Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat` | Power Stroke | 132 | 28, 70 | Oct 2022 | 14.8 MB |
| `Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat` | Paddle Stroke | 84 | Unknown | Oct 2022 | Unknown |

### Standardized Datasets
| Path | Type | Status | Creation |
|------|------|--------|----------|
| `Standardized_Data_Sets/FullStroke_Curated.mat` | Full Stroke | Curated | Unknown |
| `Standardized_Data_Sets/FullStroke_Modified.mat` | Full Stroke | Modified | Unknown |
| `Standardized_Data_Sets/PowerStroke_Modified.mat` | Power Stroke | Modified | Unknown |
| `Standardized_Data_Sets/PaddleStroke_Modified.mat` | Paddle Stroke | Modified | Unknown |

### Data Schema
- **Sampling rate**: 500 Hz
- **Filter cutoff**: 4 Hz (low-pass)
- **Force scale**: 2.22 (conversion to Newtons)
- **Coordinate frame**: Unknown (needs documentation)
- **Units**: Mixed (m/s for flow speeds, degrees for angles, Newtons for forces)
- **Trial IDs**: Embedded in experiment numbers
- **Calibration constants**: Unknown (needs documentation)

## Pipeline

### 1. Ingest
- **Entrypoint**: `Standardize_Datasets.m`
- **Input**: Raw experimental data from `Master_Data_Set_Backup/`
- **Output**: Standardized datasets in `Standardized_Data_Sets/`
- **Key functions**: `standardize_full_stroke()`, `standardize_power_stroke()`, `standardize_paddle_stroke()`

### 2. Clean
- **Entrypoint**: `Data_Filters_Full.m`
- **Input**: Raw force/time series data
- **Output**: Filtered data (4Hz low-pass, median filter)
- **Key functions**: `Data_Filters_Full()`, `Data_Filters()`

### 3. Align
- **Entrypoint**: Analysis scripts (e.g., `Full_MEAN_Plotter_2023_11_7.m`)
- **Input**: Filtered data with Arduino timing signals
- **Output**: Synchronized force and kinematic data
- **Key functions**: Zero correction, time alignment

### 4. Segment Strokes
- **Entrypoint**: Analysis scripts
- **Input**: Synchronized data
- **Output**: Power vs paddle stroke phases
- **Key functions**: Stroke detection logic embedded in analysis scripts
- **Parameters**: Power/paddle transitions at 50%, 55%, 60% of cycle

### 5. Compute Features
- **Entrypoint**: `AoA_Calc_Func.m`
- **Input**: Kinematic data, flow speeds
- **Output**: Angle of attack, velocity magnitudes
- **Key functions**: `AoA_Calc_Func()`, trajectory generation functions

### 6. Metrics
- **Entrypoint**: Analysis scripts
- **Input**: Features and force data
- **Output**: Performance metrics, efficiency measures
- **Key functions**: Force integration, power calculations

### 7. Plots
- **Entrypoint**: `*_MEAN_Plotter_*.m`, `*_HeatMap_Plotter_*.m`, `*_Trace_Plotter_*.m`
- **Input**: Processed data and metrics
- **Output**: Statistical plots, heat maps, trace visualizations
- **Key functions**: `shadedErrorBar.m`, plotting utilities

## Reproduction

### Environment Setup
1. **MATLAB Requirements**:
   - Signal Processing Toolbox
   - Statistics and Machine Learning Toolbox
   - Data Acquisition Toolbox (for real-time experiments)

2. **Data Path Configuration**:
   ```matlab
   % Update config_paths.m with your data location
   config.data_base_dir = 'C:\Users\yourname\Dropbox\36 Sea Lion AUV\Sealion_FlowTank\2022_10_06_Experiments_Folder';
   ```

3. **Setup Commands**:
   ```matlab
   % Run setup script
   setup_data_paths();
   
   % Standardize datasets
   Standardize_Datasets();
   
   % Run analysis
   Full_MEAN_Plotter_2023_11_7();
   Power_MEAN_Plotter_2023_12_19();
   Paddle_MEAN_Plotter_2023_11_1();
   ```

### Expected Artifacts
- Standardized datasets in `Standardized_Data_Sets/`
- Analysis results in `Results/` (currently empty)
- Figures and plots (generated by plotting scripts)
- **Runtime**: ~10-30 minutes for full analysis pipeline

## Validation and Tests

### Current Tests
- `Verify_Standardized_Datasets.m` - Dataset validation
- `Check_PowerStroke_Structure.m` - Structure validation  
- `Data_Struct_Analyzer.m` - Data structure analysis

### Proposed Minimal Tests
1. **Stroke Segmentation Test**: Verify stroke detection outputs non-empty segments with consistent timing
2. **Unit Consistency Test**: Check that all processed tables declare units and sampling rates
3. **Import Test**: Ensure new directory layout is importable
4. **Coordinate Frame Test**: Validate measurement reference frames

## Where We Left Off

### Last Completed Milestone
- **Dataset Standardization**: Created standardized datasets for all three stroke types
- **Analysis Pipeline**: Functional plotting and analysis scripts for all stroke types
- **Data Validation**: Basic structure validation implemented

### Next Actions
1. **Document coordinate frames and units** (high priority)
2. **Centralize stroke segmentation logic** (high priority)
3. **Add comprehensive validation tests** (medium priority)
4. **Reorganize code structure** (medium priority)
5. **Create user documentation** (low priority)

### File Pointers
- **Current work**: `Standardize_Datasets.m`, validation scripts
- **Latest analysis**: `*_MEAN_Plotter_2024_01_22.m`
- **Active development**: Multiple standardization and validation scripts

## Risks and Gaps

### High Priority Risks
1. **Coordinate frame ambiguity**: Unknown reference frame for measurements
2. **Unit inconsistencies**: Flow speeds in different units across datasets  
3. **Segmentation reliability**: No validation of stroke phase detection
4. **Missing metadata**: Calibration constants, trial IDs not documented

### Evidence Needed
- **Coordinate frame documentation**: Technical drawings or calibration notes
- **Unit specifications**: Original experimental protocol documents
- **Segmentation validation**: Manual verification of stroke detection accuracy
- **Calibration data**: Force sensor calibration constants and procedures

### Medium Priority Gaps
- Path dependencies in scripts
- Limited inline documentation
- Scattered code organization
- Minimal automated testing

## Contact and Citation

**Repository**: https://github.com/dragorobots/SealionForeFlipperStudy  
**Data Storage**: Dropbox (separate from repository)  
**Research Focus**: Bio-inspired robotics, AUV propulsion, hydrodynamics

If you use this code in your research, please cite the associated publications.

---

*This README serves as a checkpoint for the Sea Lion Fore Flipper Study repository as of September 9, 2025. For the most current information, refer to the latest commit history and analysis scripts.*