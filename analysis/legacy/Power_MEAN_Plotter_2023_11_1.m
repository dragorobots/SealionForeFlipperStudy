% Relocated on 2025-09-09 from Power_MEAN_Plotter_2023_11_1.m to analysis/legacy/Power_MEAN_Plotter_2023_11_1.m as part of repo reorg.
% NOTE: This is an older version, superseded by Power_MEAN_Plotter_2023_12_19.m

% Add paths to data and helper functions
addpath('../data/raw/Raw_Experimental_Data/14-Oct-2022_Power_Stroke_Flipper_Results')
addpath('../data/raw/Raw_Experimental_Data/07-Oct-2022_Power_Stroke_Flipper_Results')
addpath('../src/helpers')

% Load datasets
load("../data/raw/Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat")
results_1=results;
load("../data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat")
results_2=results;

% [Legacy analysis code - use Power_MEAN_Plotter_2023_12_19.m instead]

fprintf('Legacy Power Stroke analysis complete.\n');

