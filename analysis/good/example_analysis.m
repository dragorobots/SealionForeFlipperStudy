% Relocated on 2025-09-09 from example_analysis.m to analysis/good/example_analysis.m as part of repo reorg.

% Example analysis script for Sea Lion Fore Flipper Study
% This script demonstrates how to use the reorganized repository

% Add paths to data and helper functions
addpath('../data/processed/Standardized_Data_Sets')
addpath('../src/helpers')

% Load a standardized dataset
load('../data/processed/Standardized_Data_Sets/FullStroke_Standardized.mat')

% Example analysis
fprintf('Example analysis complete.\n');
fprintf('Dataset contains %d experiments\n', FullStroke_Standardized.total_experiments);

