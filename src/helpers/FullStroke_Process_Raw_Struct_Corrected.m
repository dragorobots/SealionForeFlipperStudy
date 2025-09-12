function FullStroke_Process_Raw_Struct_Corrected()
% FullStroke_Process_Raw_Struct_Corrected - Process and prune Full Stroke data
% 
% This script processes the Full Stroke datasets from 20-Jan and 30-Jan 2023,
% pruning the data based on specific parameter criteria and combining them
% into a single organized structure.
%
% Target Parameters:
% - Stroke period: 2.25s only
% - Yaw amplitude: 70, 80, 90 degrees (remove 100)
% - Paddle transition: all values (0.5, 0.55, 0.6)
% - Roll power angle: all values
% - Flow speed: 0 m/s (from 30-Jan) and 0.1 m/s (from 20-Jan)

clear all
clc
close all

fprintf('=== FULL STROKE DATA PROCESSING (CORRECTED) ===\n');
fprintf('Processing and pruning Full Stroke datasets...\n\n');

% Create output directory
output_dir = 'data/processed/2025-01-27_ProcessedData';
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
    fprintf('Created output directory: %s\n', output_dir);
end

% Add paths to data
addpath('data/raw/Master_Data_Set_Backup');

%% Load the Full Stroke datasets
fprintf('Loading Full Stroke datasets...\n');

% Load 20-Jan dataset (Flow speed 0.1 m/s)
fprintf('  Loading 20-Jan-2023 dataset...\n');
load('20-Jan-2023_results_FullStroke.mat');
data_20Jan = results;
fprintf('    Loaded: 20-Jan dataset with %d experiments\n', length(data_20Jan.data));

% Load 30-Jan dataset (Flow speed 0 m/s)
fprintf('  Loading 30-Jan-2023 dataset...\n');
load('30-Jan-2023_results_FullStroke.mat');
data_30Jan = results;
fprintf('    Loaded: 30-Jan dataset with %d experiments\n', length(data_30Jan.data));

%% Define target parameters for pruning
target_params = struct();
target_params.period = 2.25;  % Only 2.25s period
target_params.y_amp = [70, 80, 90];  % Remove 100 degrees
target_params.paddle_trans = [0.5, 0.55, 0.6];  % All paddle transitions
target_params.flow_speeds = [0, 0.1];  % 0 from 30-Jan, 0.1 from 20-Jan

fprintf('\nTarget parameters for pruning:\n');
fprintf('  Period: %.2f s\n', target_params.period);
fprintf('  Yaw amplitudes: %s degrees\n', mat2str(target_params.y_amp));
fprintf('  Paddle transitions: %s\n', mat2str(target_params.paddle_trans));
fprintf('  Flow speeds: %s m/s\n', mat2str(target_params.flow_speeds));

%% Process 20-Jan dataset (Flow speed 0.1 m/s)
fprintf('\n=== PROCESSING 20-JAN DATASET (Flow speed 0.1 m/s) ===\n');
[pruned_20Jan, valid_indices_20] = prune_dataset_corrected(data_20Jan, target_params, 0.1);
fprintf('20-Jan dataset: %d/%d experiments selected\n', length(valid_indices_20), length(data_20Jan.data));

%% Process 30-Jan dataset (Flow speed 0 m/s)
fprintf('\n=== PROCESSING 30-JAN DATASET (Flow speed 0 m/s) ===\n');
[pruned_30Jan, valid_indices_30] = prune_dataset_corrected(data_30Jan, target_params, 0);
fprintf('30-Jan dataset: %d/%d experiments selected\n', length(valid_indices_30), length(data_30Jan.data));

%% Combine the pruned datasets
fprintf('\n=== COMBINING PRUNED DATASETS ===\n');

% Initialize combined structure
combined_data = struct();
combined_data.data = {};
combined_data.zeros = {};
combined_data.parameters = {};

% Add 20-Jan data (Flow speed 0.1)
fprintf('Adding 20-Jan data (Flow speed 0.1 m/s)...\n');
for i = 1:length(pruned_20Jan.data)
    combined_data.data{end+1} = pruned_20Jan.data{i};
    combined_data.zeros{end+1} = pruned_20Jan.zeros{i};
    combined_data.parameters{end+1} = pruned_20Jan.parameters{i};
end

% Add 30-Jan data (Flow speed 0)
fprintf('Adding 30-Jan data (Flow speed 0 m/s)...\n');
for i = 1:length(pruned_30Jan.data)
    combined_data.data{end+1} = pruned_30Jan.data{i};
    combined_data.zeros{end+1} = pruned_30Jan.zeros{i};
    combined_data.parameters{end+1} = pruned_30Jan.parameters{i};
end

%% Add metadata to combined structure
combined_data.metadata = struct();
combined_data.metadata.experiment_type = 'Full Stroke';
combined_data.metadata.processing_date = datestr(now, 'yyyy-mm-dd HH:MM:SS');
combined_data.metadata.source_datasets = {'20-Jan-2023_results_FullStroke.mat', '30-Jan-2023_results_FullStroke.mat'};
combined_data.metadata.target_parameters = target_params;
combined_data.metadata.total_experiments = length(combined_data.data);
combined_data.metadata.experiments_from_20Jan = length(valid_indices_20);
combined_data.metadata.experiments_from_30Jan = length(valid_indices_30);

%% Display summary
fprintf('\n=== PROCESSING SUMMARY ===\n');
fprintf('Total experiments in combined dataset: %d\n', combined_data.metadata.total_experiments);
fprintf('  From 20-Jan (0.1 m/s): %d experiments\n', combined_data.metadata.experiments_from_20Jan);
fprintf('  From 30-Jan (0 m/s): %d experiments\n', combined_data.metadata.experiments_from_30Jan);

% Display parameter distribution
fprintf('\nParameter distribution:\n');
periods = []; y_amps = []; paddle_trans = []; flow_speeds = []; roll_angles = [];

for i = 1:length(combined_data.parameters)
    params = combined_data.parameters{i}.parameters;
    periods = [periods, params(1)];  % period
    y_amps = [y_amps, params(2)];    % yaw amplitude
    paddle_trans = [paddle_trans, params(3)];  % paddle transition
    flow_speeds = [flow_speeds, params(4)];    % flow speed
    roll_angles = [roll_angles, params(5)];    % roll angle
end

fprintf('  Periods: %s\n', mat2str(unique(periods)));
fprintf('  Yaw amplitudes: %s degrees\n', mat2str(unique(y_amps)));
fprintf('  Paddle transitions: %s\n', mat2str(unique(paddle_trans)));
fprintf('  Flow speeds: %s m/s\n', mat2str(unique(flow_speeds)));
fprintf('  Roll angles: %s degrees\n', mat2str(unique(roll_angles)));

%% Save the processed data
output_filename = fullfile(output_dir, 'FullStroke_Processed_Corrected_2025-01-27.mat');
fprintf('\nSaving processed data to: %s\n', output_filename);

save(output_filename, 'combined_data', '-v7.3');

fprintf('Processing complete!\n');
fprintf('Output saved to: %s\n', output_filename);

end

function [pruned_data, valid_indices] = prune_dataset_corrected(data_struct, target_params, flow_speed)
% Prune dataset based on target parameters - CORRECTED VERSION
% Inputs:
%   data_struct - Original data structure
%   target_params - Target parameter values
%   flow_speed - Flow speed for this dataset
% Outputs:
%   pruned_data - Pruned data structure
%   valid_indices - Indices of valid experiments

fprintf('  Pruning dataset with flow speed %.1f m/s...\n', flow_speed);

% The data structure has arrays: data_struct.data, data_struct.parameters, data_struct.zeros
% Each index corresponds to one experiment
num_experiments = length(data_struct.data);
valid_indices = [];

% Debug: Show first few parameter values
fprintf('    Debug - First 3 experiments:\n');
for i = 1:min(3, num_experiments)
    params = data_struct.parameters(i).parameters;
    fprintf('      Exp %d: Period=%.2f, Yaw=%.0f, Paddle=%.2f, Flow=%.1f, Roll=%.0f\n', ...
        i, params(1), params(2), params(3), params(4), params(5));
end

% Check each experiment
for i = 1:num_experiments
    % Get parameters for this experiment
    params = data_struct.parameters(i).parameters;
    
    % Check if this experiment matches our criteria
    is_valid = true;
    
    % Check period (index 1 in parameters array)
    if abs(params(1) - target_params.period) > 0.01
        is_valid = false;
    end
    
    % Check yaw amplitude (index 2 in parameters array)
    if ~ismember(params(2), target_params.y_amp)
        is_valid = false;
    end
    
    % Check paddle transition (index 3 in parameters array)
    if ~ismember(params(3), target_params.paddle_trans)
        is_valid = false;
    end
    
    % Check flow speed (index 4 in parameters array)
    if abs(params(4) - flow_speed) > 0.01
        is_valid = false;
    end
    
    if is_valid
        valid_indices = [valid_indices, i];
    end
end

fprintf('    Found %d valid experiments out of %d total\n', length(valid_indices), num_experiments);

% Create pruned data structure
pruned_data = struct();
pruned_data.data = {};
pruned_data.zeros = {};
pruned_data.parameters = {};

% Extract valid experiments
for i = 1:length(valid_indices)
    exp_idx = valid_indices(i);
    
    % Copy data
    pruned_data.data{i} = data_struct.data(exp_idx);
    
    % Copy zeros
    pruned_data.zeros{i} = data_struct.zeros(exp_idx);
    
    % Copy parameters
    pruned_data.parameters{i} = data_struct.parameters(exp_idx);
end

end

