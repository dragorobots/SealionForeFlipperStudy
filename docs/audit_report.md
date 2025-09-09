# Sea-lion Foreflipper Stroke Analysis - Audit Report
**Date:** 2025-09-09  
**Auditor:** AI Assistant  
**Repository:** Sea Lion Fore Flipper Study

## Executive Summary

This MATLAB-based repository analyzes sea lion-inspired flipper propulsion in AUVs. The project contains experimental data from flow tank tests with a 3-DOF robotic flipper system, focusing on three stroke types: **Full stroke** (complete cycle), **Power stroke** (high-force phase), and **Paddle stroke** (low-force recovery phase).

## Repository Structure Analysis

### Top-level Directories
- **Data_Collecting_Functions/**: 7 automated data collection scripts (2021-2022)
- **Old_Results_Workers/**: 11 legacy analysis scripts 
- **Stuff_For_Shraman/**: 2 specialized analysis tools
- **Master_Data_Set_Backup/**: 6 core experimental datasets
- **Standardized_Data_Sets/**: 4 processed/curated datasets
- **Raw_Experimental_Data/**: 10 experimental session folders
- **Results/**: Empty (no current results)
- **Flipper_Videos/**: Video recordings
- **html/**: Documentation and figures

### File Inventory

#### MATLAB Scripts (66 total)
**Core Analysis Scripts:**
- `Full_MEAN_Plotter_2023_11_7.m` - Full stroke analysis and visualization
- `Power_MEAN_Plotter_2023_12_19.m` - Power stroke analysis  
- `Paddle_MEAN_Plotter_2023_11_1.m` - Paddle stroke analysis
- `*_HeatMap_Plotter_*.m` - Performance heat map generation (3 files)
- `*_Trace_Plotter_*.m` - Trace visualization (3 files)

**Data Processing:**
- `Standardize_Datasets.m` - Main standardization script
- `Data_Filters_Full.m` - Signal filtering (4Hz cutoff, 500Hz sampling)
- `AoA_Calc_Func.m` - Angle of Attack calculations
- `Data_Struct_Analyzer.m` - Data structure validation

**Control & Trajectory:**
- `Matlab_Flipper_Test.m` - Main flipper control
- `flipper_trajs.m` - Basic trajectory generation
- `flipper_trajs_constrained.m` - Constrained trajectory optimization
- `Traj_Builder_Constrained.m` - Advanced trajectory builder

**Configuration:**
- `config_paths.m` - Path configuration
- `setup_data_paths.m` - Data path setup

#### Data Files (21 .mat files)
**Master Datasets (6 files, ~150MB total):**
- 3 Full Stroke datasets (Jan 2023): 168 experiments each
- 2 Power Stroke datasets (Oct 2022): 132 experiments each  
- 1 Paddle Stroke dataset (Oct 2022): 84 experiments

**Standardized Datasets (4 files):**
- `FullStroke_Curated.mat`, `FullStroke_Modified.mat`
- `PowerStroke_Modified.mat`, `PaddleStroke_Modified.mat`

**Processed Results (3 files):**
- `Full_Traces.mat`, `Power_Traces.mat`, `Paddle_Traces.mat`

## Experimental Parameters

### Measurement System
- **Sampling rate**: 500 Hz
- **Filter cutoff**: 4 Hz (low-pass)
- **Force scale**: 2.22 (conversion factor to Newtons)
- **Flipper length**: 190.5 mm
- **Coordinate frame**: Unknown (needs investigation)

### Variable Parameters
- **Flow speeds**: 0, 0.05, 0.1 m/s (Full); 0, 28, 70, 100 (Power/Paddle)
- **Stroke periods**: 1.75s, 2.25s
- **Yaw amplitudes**: -70°, -80°, -90°, -100° (Full); -60°, -75°, -90° (Power/Paddle)
- **Roll angles**: 0° to 90° (7-11 different angles)
- **Power/paddle transitions**: 50%, 55%, 60% of stroke cycle

## Pipeline Analysis

### Data Flow
1. **Ingest**: Raw experimental data from flow tank tests
2. **Clean**: Signal filtering, zero correction, force scaling
3. **Align**: Synchronization with Arduino timing signals
4. **Segment**: Stroke phase detection (power vs paddle)
5. **Features**: Kinematics, forces, angle of attack
6. **Metrics**: Performance calculations, efficiency measures
7. **Visualize**: Heat maps, trace plots, statistical summaries

### Key Functions
- **Segmentation**: Implemented in analysis scripts, not centralized
- **Filtering**: `Data_Filters_Full.m` (4Hz low-pass, median filter)
- **Angle of Attack**: `AoA_Calc_Func.m` (hydrodynamic calculations)
- **Trajectory Generation**: `flipper_trajs.m` and variants

## Recent Activity Analysis

### Git History
- **Latest commit**: 1687e1a "Add data path management and example scripts"
- **Previous**: 2b260ea "Initial commit: Sea Lion Fore Flipper Study MATLAB analysis code"
- **Branch**: master (up to date with origin/master)

### File Timestamps
- **Most recent analysis**: 2024-04-29 (Trace Appendix Makers)
- **Latest plotters**: 2024-01-22 (Power MEAN Plotter)
- **Standardization work**: Recent (multiple standardization scripts)

### Current State
- **Modified files**: `Full_Trace_Plotter_2023_11_1.m`, `Paddle_Trace_Plotter_2023_11_1.m`
- **Untracked files**: 15 new analysis and standardization scripts
- **Active work**: Dataset standardization and validation

## Data Quality Assessment

### Strengths
- Consistent experimental protocol across sessions
- Standardized data structures
- Comprehensive parameter sweeps
- Good documentation of experimental settings

### Issues Identified
- **Coordinate frame**: Not documented
- **Units**: Some inconsistencies in flow speed units (m/s vs arbitrary)
- **Segmentation**: No centralized stroke detection algorithm
- **Validation**: Limited automated quality checks
- **Metadata**: Missing calibration constants and trial IDs

## Validation and Testing

### Current Tests
- `Verify_Standardized_Datasets.m` - Dataset validation
- `Check_PowerStroke_Structure.m` - Structure validation
- `Data_Struct_Analyzer.m` - Data structure analysis

### Missing Tests
- Stroke segmentation validation
- Unit consistency checks
- Coordinate frame validation
- Import/export functionality tests

## Risks and Gaps

### High Priority
1. **Coordinate frame ambiguity**: Unknown reference frame for measurements
2. **Unit inconsistencies**: Flow speeds in different units across datasets
3. **Segmentation reliability**: No validation of stroke phase detection
4. **Missing metadata**: Calibration constants, trial IDs not documented

### Medium Priority
1. **Path dependencies**: Hard-coded paths in scripts
2. **Version control**: Data files not in git (stored in Dropbox)
3. **Documentation**: Limited inline documentation in analysis scripts

### Low Priority
1. **Code organization**: Scripts scattered across root directory
2. **Legacy code**: Old analysis scripts not clearly marked
3. **Testing**: Minimal automated validation

## Recommendations

### Immediate Actions
1. Document coordinate frames and units
2. Centralize stroke segmentation logic
3. Add validation for stroke detection
4. Create unit consistency checks

### Medium-term
1. Reorganize code into logical directories
2. Add comprehensive documentation
3. Implement automated testing
4. Standardize data file naming

### Long-term
1. Migrate to version-controlled data storage
2. Implement configuration management
3. Add continuous integration
4. Create user documentation

## Evidence Needed

To resolve identified gaps, the following evidence is required:
1. **Coordinate frame documentation**: Technical drawings or calibration notes
2. **Unit specifications**: Original experimental protocol documents
3. **Segmentation validation**: Manual verification of stroke detection accuracy
4. **Calibration data**: Force sensor calibration constants and procedures

