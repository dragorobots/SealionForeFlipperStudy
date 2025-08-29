# Sea Lion Fore Flipper Study

A MATLAB-based experimental analysis system for studying sea lion-inspired flipper propulsion in Autonomous Underwater Vehicles (AUVs).

## Overview

This repository contains the MATLAB analysis code for a comprehensive study of bio-inspired flipper propulsion systems. The project involves experimental testing of a 3-DOF robotic flipper system in a controlled flow tank environment to understand the hydrodynamics and performance characteristics of sea lion swimming mechanisms.

## Repository Structure

```
├── Data_Collecting_Functions/     # Automated data collection scripts
├── Old_Results_Workers/          # Legacy analysis scripts
├── Stuff_For_Shraman/           # Specialized analysis tools
├── *.m                          # Main analysis and control scripts
└── README.md                    # This file
```

## Key Components

### Control System
- **Arduino Communication**: Real-time control of 3-DOF flipper system
- **Trajectory Generation**: Spline-based motion planning for bio-inspired swimming
- **Flow Tank Control**: Automated flow speed and motor control

### Data Analysis
- **Signal Processing**: Filtering, alignment, and statistical analysis
- **Performance Metrics**: Thrust, lift, and efficiency calculations
- **Visualization**: Heat maps, trace plots, and statistical visualizations

### Experimental Protocols
- **Power Stroke Analysis**: High-force propulsion phase
- **Paddle Stroke Analysis**: Transition/recovery phase
- **Full Stroke Analysis**: Complete swimming cycle

## Data Files

**Note**: Data files (`.mat`, `.MP4`, etc.) are stored separately in Dropbox and are not included in this repository. The MATLAB scripts are configured to reference data files using relative paths from the Dropbox location.

### Data Structure (in Dropbox)
```
├── *_Flipper_Results/           # Experimental results by date
├── Flipper_Videos/             # Video recordings
├── *.mat                       # Force measurement data
└── html/                       # Documentation and figures
```

## Setup Instructions

1. **Clone this repository**:
   ```bash
   git clone https://github.com/dragorobots/SealionForeFlipperStudy.git
   cd SealionForeFlipperStudy
   ```

2. **Set up data path**: Update the data path in MATLAB scripts to point to your Dropbox data location:
   ```matlab
   % Example: Update paths in analysis scripts
   data_path = 'C:\Users\yourname\Dropbox\36 Sea Lion AUV\Sealion_FlowTank\2022_10_06_Experiments_Folder\';
   ```

3. **Required MATLAB Toolboxes**:
   - Signal Processing Toolbox
   - Statistics and Machine Learning Toolbox
   - Data Acquisition Toolbox (for real-time experiments)

## Main Scripts

### Control and Data Collection
- `Matlab_Flipper_Test.m` - Main flipper control and testing
- `Single_Stroke_Data_Collector.m` - Automated data collection
- `Test_Flow_Tank.m` - Flow tank control system

### Trajectory Generation
- `flipper_trajs.m` - Basic trajectory generation
- `flipper_trajs_constrained.m` - Constrained trajectory optimization
- `Traj_Builder_Constrained.m` - Advanced trajectory builder

### Data Analysis
- `Full_MEAN_Plotter_2023_11_7.m` - Full stroke analysis and visualization
- `Power_MEAN_Plotter_2023_12_19.m` - Power stroke analysis
- `Paddle_MEAN_Plotter_2023_11_1.m` - Paddle stroke analysis
- `*_HeatMap_Plotter_*.m` - Performance heat map generation

### Signal Processing
- `Data_Filters_Full.m` - Signal filtering and processing
- `AoA_Calc_Func.m` - Angle of Attack calculations

## Experimental Parameters

### Variable Parameters
- **Flow speeds**: 0, 0.05, 0.1 m/s
- **Stroke periods**: 1.75s, 2.25s
- **Yaw amplitudes**: -70°, -80°, -90°, -100°
- **Roll angles**: 0° to 90° (7 different angles)
- **Power/paddle transitions**: 50%, 55%, 60% of stroke cycle

### Measurement System
- **Sampling rate**: 500 Hz
- **Force measurements**: Thrust and lift forces
- **Synchronization**: Arduino-based timing signals

## Usage Examples

### Running Analysis
```matlab
% Load and analyze full stroke data
addpath('20-Jan-2023_Full_Stroke_Flipper_Results')
load("20-Jan-2023_results_FullStroke.mat")
% Run analysis scripts...
```

### Generating Trajectories
```matlab
% Generate constrained trajectory
[pitch, yaw, roll, TS] = Traj_Builder_Constrained(Action, Num_Pts);
```

## Research Applications

This work contributes to:
- **Bio-inspired robotics**: Understanding sea lion swimming mechanics
- **AUV propulsion**: Developing efficient underwater vehicle systems
- **Hydrodynamics research**: Studying unsteady flow phenomena
- **Control systems**: Real-time trajectory execution and optimization

## Citation

If you use this code in your research, please cite the associated publications.

## License

[Add your license information here]

## Contact

[Add contact information here]

## Acknowledgments

This research was conducted as part of the Sea Lion AUV project, focusing on bio-inspired propulsion systems for autonomous underwater vehicles.
