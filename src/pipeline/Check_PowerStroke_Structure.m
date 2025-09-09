% Check_PowerStroke_Structure - Examine the actual structure of Power Stroke data
% This will help us understand how to properly filter the experiments

clear all
clc

fprintf('=== CHECKING POWER STROKE STRUCTURE ===\n');

% Add paths
addpath('Master_Data_Set_Backup');

%% LOAD ORIGINAL POWER STROKE DATASETS
fprintf('Loading original Power Stroke datasets...\n');

load('Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat');
results_1 = results;

load('Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
results_2 = results;

%% EXAMINE STRUCTURE
fprintf('\n=== STRUCTURE ANALYSIS ===\n');

% Check first few experiments from each dataset
fprintf('14-Oct-2022 dataset:\n');
fprintf('  Number of experiments: %d\n', length(results_1.data));
if length(results_1.parameters) > 0
    fprintf('  First experiment parameters: %s\n', mat2str(results_1.parameters(1).parameters));
    fprintf('  Number of parameter elements: %d\n', length(results_1.parameters(1).parameters));
end

fprintf('\n07-Oct-2022 dataset:\n');
fprintf('  Number of experiments: %d\n', length(results_2.data));
if length(results_2.parameters) > 0
    fprintf('  First experiment parameters: %s\n', mat2str(results_2.parameters(1).parameters));
    fprintf('  Number of parameter elements: %d\n', length(results_2.parameters(1).parameters));
end

%% CHECK FLOW SPEED SETTINGS
fprintf('\n=== FLOW SPEED SETTINGS ===\n');
fprintf('14-Oct-2022 Flow Speed: %s\n', mat2str(results_1.Flow_Speed_settings));
fprintf('07-Oct-2022 Flow Speed: %s\n', mat2str(results_2.Flow_Speed_settings));

%% CHECK YAW AND ROLL SETTINGS
fprintf('\n=== YAW AND ROLL SETTINGS ===\n');
fprintf('14-Oct-2022 Yaw: %s\n', mat2str(results_1.y_amp_settings));
fprintf('14-Oct-2022 Roll: %s\n', mat2str(results_1.roll_pow_ang_settings));
fprintf('07-Oct-2022 Yaw: %s\n', mat2str(results_2.y_amp_settings));
fprintf('07-Oct-2022 Roll: %s\n', mat2str(results_2.roll_pow_ang_settings));

%% SAMPLE PARAMETER VALUES
fprintf('\n=== SAMPLE PARAMETER VALUES ===\n');
fprintf('First 5 experiments from 14-Oct-2022:\n');
for i = 1:min(5, length(results_1.parameters))
    fprintf('  Exp %d: %s\n', i, mat2str(results_1.parameters(i).parameters));
end

fprintf('\nFirst 5 experiments from 07-Oct-2022:\n');
for i = 1:min(5, length(results_2.parameters))
    fprintf('  Exp %d: %s\n', i, mat2str(results_2.parameters(i).parameters));
end
