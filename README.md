# Sea Lion Foreflipper Stroke Analysis
## Master Repository Guide & Primer

**Repository Checkpoint:** September 9, 2025  
**Purpose:** Bio-inspired AUV propulsion research using sea lion foreflipper mechanics  
**Language:** MATLAB (primary), Python (tools), Arduino (control)  
**Data Storage:** Dropbox (separate from repository) [[memory:7630130]]

---

## 🎯 Quick Start for New Users

### What This Repository Does
This repository analyzes experimental data from a 3-DOF robotic flipper system that mimics sea lion foreflipper swimming mechanics. The goal is to understand hydrodynamics and optimize bio-inspired AUV propulsion.

### Essential Concepts
- **Full stroke**: Complete swimming cycle from start to finish
- **Power stroke**: High-force propulsion phase (thrust generation)
- **Paddle stroke**: Low-force recovery/repositioning phase
- **Flow tank**: Controlled water environment for testing
- **3-DOF**: Three degrees of freedom (yaw, roll, pitch)

### First Steps
1. **Read this README** (you're here!)
2. **Check the audit report**: `docs/audit_report.md`
3. **Run the example**: `analysis/good/example_analysis.m`
4. **Explore the data**: `data/raw/Master_Data_Set_Backup/`

---

## 📁 Repository Tour

### 🏗️ **Core Structure**
```
├── src/                          # Source code
│   ├── helpers/                  # Reusable functions (9 files)
│   │   ├── AoA_Calc_Func.m      # Angle of Attack calculations
│   │   ├── Data_Filters_Full.m  # Signal filtering (4Hz cutoff)
│   │   └── ...                  # Other utility functions
│   └── pipeline/                 # Data processing pipeline (26 files)
│       ├── Standardize_Datasets.m # Main data standardization
│       └── ...                  # Collection and processing scripts
│
├── analysis/                     # Analysis scripts
│   ├── good/                     # Validated, current analysis (14 files)
│   │   ├── Full_MEAN_Plotter_2023_11_7.m    # Full stroke analysis
│   │   ├── Power_MEAN_Plotter_2023_12_19.m  # Power stroke analysis
│   │   ├── Paddle_MEAN_Plotter_2023_11_1.m  # Paddle stroke analysis
│   │   └── ...                  # Heat maps, traces, examples
│   └── legacy/                   # Older analysis scripts (8 files)
│
├── data/                         # Data storage
│   ├── raw/                      # Immutable experimental data
│   │   └── Master_Data_Set_Backup/ # Core datasets (6 files, ~150MB)
│   └── processed/                # Analysis-ready data
│       └── Standardized_Data_Sets/ # Cleaned datasets (4 files)
│
├── config/                       # Configuration
│   ├── config_paths.m           # Path and parameter settings
│   ├── setup_data_paths.m       # Data path management
│   └── Arduino/                 # Control system code
│
├── docs/                         # Documentation
│   ├── audit_report.md          # Comprehensive repository analysis
│   ├── reorg_plan.tsv           # Reorganization plan
│   └── repo_provenance.json     # Repository state snapshot
│
├── tests/                        # Validation scripts (3 files)
├── tools/                        # Repository management tools
└── LeftOvers/                    # Files pending organization
```

### 🔬 **Experimental Data Overview**

| Dataset | Type | Experiments | Flow Speed | Date | Size |
|---------|------|-------------|------------|------|------|
| `20-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0.1 m/s | Jan 2023 | 37.8 MB |
| `23-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0.05 m/s | Jan 2023 | 37.5 MB |
| `30-Jan-2023_results_FullStroke.mat` | Full Stroke | 168 | 0 m/s | Jan 2023 | 37.4 MB |
| `14-Oct-2022_results_PowerStroke.mat` | Power Stroke | 132 | 0, 100 | Oct 2022 | 18.8 MB |
| `07-Oct-2022_results_PowerStroke.mat` | Power Stroke | 132 | 28, 70 | Oct 2022 | 14.8 MB |
| `19-Oct-2022_results_PaddleStroke.mat` | Paddle Stroke | 84 | Unknown | Oct 2022 | Unknown |

### 📊 **Key Analysis Scripts**

#### Current (Validated) Analysis
- **`Full_MEAN_Plotter_2023_11_7.m`**: Complete full stroke analysis with statistical summaries
- **`Power_MEAN_Plotter_2023_12_19.m`**: Power stroke performance analysis
- **`Paddle_MEAN_Plotter_2023_11_1.m`**: Paddle stroke recovery analysis
- **`*_HeatMap_Plotter_*.m`**: Performance visualization across parameter space
- **`*_Trace_Plotter_*.m`**: Individual stroke trace visualization

#### Data Processing Pipeline
- **`Standardize_Datasets.m`**: Main data cleaning and standardization
- **`Data_Filters_Full.m`**: Signal filtering (4Hz low-pass, median filter)
- **`AoA_Calc_Func.m`**: Angle of Attack calculations for hydrodynamics

---

## 🔬 Research Context & Background

### What We're Studying
Sea lions are exceptional swimmers, using their foreflippers for both propulsion and maneuverability. This research aims to:
1. **Understand** the hydrodynamics of sea lion foreflipper swimming
2. **Optimize** bio-inspired AUV propulsion systems
3. **Develop** control strategies for underwater robotics

### Experimental Setup
- **Flow tank**: Controlled water environment with adjustable flow speeds
- **3-DOF robotic flipper**: Mimics sea lion foreflipper mechanics
- **Force sensors**: Measure thrust and lift forces
- **Arduino control**: Real-time trajectory control and data acquisition
- **500 Hz sampling**: High-frequency data collection

### Key Parameters
- **Flow speeds**: 0, 0.05, 0.1 m/s (Full); 0, 28, 70, 100 (Power/Paddle)
- **Stroke periods**: 1.75s, 2.25s
- **Yaw amplitudes**: -70° to -100° (Full); -60° to -90° (Power/Paddle)
- **Roll angles**: 0° to 90° (7-11 different angles)
- **Power/paddle transitions**: 50%, 55%, 60% of stroke cycle

---

## 🚀 Getting Started Guide

### Prerequisites
- **MATLAB** with Signal Processing Toolbox
- **Data access**: Raw data stored in Dropbox [[memory:7630130]]
- **Basic understanding**: Fluid mechanics, robotics, signal processing

### Environment Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/dragorobots/SealionForeFlipperStudy
   cd SealionForeFlipperStudy
   ```

2. **Configure data paths**:
   ```matlab
   % Edit config/config_paths.m
   config.data_base_dir = 'C:\Users\yourname\Dropbox\36 Sea Lion AUV\Sealion_FlowTank\2022_10_06_Experiments_Folder';
   ```

3. **Setup MATLAB environment**:
   ```matlab
   % Add paths and initialize
   setup_data_paths();
   
   % Standardize datasets (if needed)
   Standardize_Datasets();
   ```

### Running Your First Analysis
```matlab
% Start with the example analysis
run('analysis/good/example_analysis.m');

% Or run a specific analysis
Full_MEAN_Plotter_2023_11_7();  % Full stroke analysis
Power_MEAN_Plotter_2023_12_19(); % Power stroke analysis
```

### Understanding the Output
- **Force traces**: Thrust and lift over time
- **Heat maps**: Performance across parameter space
- **Statistical summaries**: Mean forces, standard deviations
- **Trace plots**: Individual stroke examples

---

## 🔧 For AI Assistants & Developers

### Repository State (September 2025)
- **Reorganized**: Clean directory structure implemented
- **Validated**: Core analysis scripts tested and working
- **Documented**: Comprehensive audit and documentation
- **Git managed**: Backup branch created, main branch updated

### Key Technical Details
- **Sampling rate**: 500 Hz
- **Filter cutoff**: 4 Hz (low-pass filter)
- **Force scale**: 2.22 (conversion to Newtons)
- **Coordinate frame**: Unknown (needs documentation)
- **Units**: Mixed (m/s, degrees, Newtons)

### Common Tasks & File Locations
- **Data standardization**: `src/pipeline/Standardize_Datasets.m`
- **Signal filtering**: `src/helpers/Data_Filters_Full.m`
- **Angle calculations**: `src/helpers/AoA_Calc_Func.m`
- **Configuration**: `config/config_paths.m`
- **Validation**: `tests/` directory

### Development Workflow
1. **Make changes** in appropriate directory
2. **Test** using validation scripts
3. **Update documentation** if needed
4. **Commit** with descriptive messages
5. **Push** to repository

### Known Issues & Limitations
- **Coordinate frame**: Not documented (high priority)
- **Unit inconsistencies**: Flow speeds in different units
- **Segmentation**: No centralized stroke detection
- **Path dependencies**: Some hard-coded paths remain

---

## 📚 Learning Resources

### For New Researchers
1. **Start here**: This README and `docs/audit_report.md`
2. **Run examples**: `analysis/good/example_analysis.m`
3. **Explore data**: Load and examine `.mat` files
4. **Read papers**: Check citations in analysis scripts

### For Developers
1. **Understand structure**: Review `docs/reorg_plan.tsv`
2. **Check validation**: Run `tests/` scripts
3. **Review pipeline**: Study `src/pipeline/` scripts
4. **Update paths**: Modify `config/config_paths.m`

### For AI Assistants
1. **Read audit report**: `docs/audit_report.md` for comprehensive overview
2. **Check provenance**: `docs/repo_provenance.json` for repository state
3. **Review organization**: `docs/reorg_plan.tsv` for file structure
4. **Understand context**: This README for research background

---

## 🎯 Current Status & Next Steps

### ✅ Recently Completed
- Repository audit and documentation
- Directory reorganization
- Git backup and version control
- Validation script creation

### 🔄 In Progress
- Dataset standardization
- Analysis script validation
- Documentation updates

### 📋 Next Priorities
1. **Document coordinate frames** (high priority)
2. **Centralize stroke segmentation** (high priority)
3. **Add comprehensive validation** (medium priority)
4. **Create user tutorials** (low priority)

### 🚨 Known Risks
- **Coordinate frame ambiguity**: Unknown reference frame
- **Unit inconsistencies**: Mixed units across datasets
- **Segmentation reliability**: No validation of stroke detection
- **Missing metadata**: Calibration constants not documented

---

## 🤝 Contributing & Contact

### Repository Information
- **GitHub**: https://github.com/dragorobots/SealionForeFlipperStudy
- **Data Storage**: Dropbox (separate from repository)
- **Research Focus**: Bio-inspired robotics, AUV propulsion, hydrodynamics

### Getting Help
1. **Check documentation**: `docs/` directory
2. **Run validation**: `tests/` scripts
3. **Review examples**: `analysis/good/example_analysis.m`
4. **Check issues**: GitHub issues page

### Citation
If you use this code in your research, please cite the associated publications and acknowledge the repository.

---

## 📝 Quick Reference

### Essential Commands
```matlab
% Setup
setup_data_paths();

% Data processing
Standardize_Datasets();

% Analysis
Full_MEAN_Plotter_2023_11_7();
Power_MEAN_Plotter_2023_12_19();
Paddle_MEAN_Plotter_2023_11_1();

% Validation
run('tests/run_tests.m');
```

### Key File Patterns
- **`*_MEAN_Plotter_*.m`**: Statistical analysis scripts
- **`*_HeatMap_Plotter_*.m`**: Performance visualization
- **`*_Trace_Plotter_*.m`**: Individual stroke visualization
- **`*_Standardized.mat`**: Cleaned datasets
- **`*_results_*.mat`**: Raw experimental data

### Directory Quick Access
- **Source code**: `src/`
- **Analysis**: `analysis/good/`
- **Data**: `data/raw/Master_Data_Set_Backup/`
- **Config**: `config/`
- **Documentation**: `docs/`
- **Tests**: `tests/`

---

*This README serves as the master guide for the Sea Lion Fore Flipper Study repository. For the most current information, refer to the latest commit history and analysis scripts. Last updated: September 9, 2025.*
