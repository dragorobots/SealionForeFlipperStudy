% Simple_Fix_Datasets - Simple approach to fix standardized datasets
% Directly corrects the settings and saves new versions

clear all
clc

fprintf('=== SIMPLE DATASET FIX ===\n');

% Add paths
addpath('Standardized_Data_Sets');
addpath('Master_Data_Set_Backup');

%% FIX FULL STROKE - Load original and recreate with correct settings
fprintf('Fixing Full Stroke dataset...\n');

% Load all three original Full Stroke datasets
load('Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat');
results_1 = results;

load('Master_Data_Set_Backup/23-Jan-2023_results_FullStroke.mat');
results_2 = results;

load('Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat');
results_3 = results;

% Create corrected structure
FullStroke_Fixed = struct();

% Combine all experiments
FullStroke_Fixed.data = [results_1.data, results_2.data, results_3.data];
FullStroke_Fixed.parameters = [results_1.parameters, results_2.parameters, results_3.parameters];
FullStroke_Fixed.zeros = [results_1.zeros, results_2.zeros, results_3.zeros];

% Fix settings
FullStroke_Fixed.period_settings = [1.75 2.25];
FullStroke_Fixed.y_amp_settings = [70 80 90]; % Only 70, 80, 90, positive
FullStroke_Fixed.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Positive values
FullStroke_Fixed.Flow_Speed_settings = [0 0.1]; % 0 and 0.1 m/s

% Add metadata
FullStroke_Fixed.experiment_type = 'Full_Stroke_Fixed';
FullStroke_Fixed.source_files = {'20-Jan-2023', '23-Jan-2023', '30-Jan-2023'};
FullStroke_Fixed.total_experiments = length(FullStroke_Fixed.data);
FullStroke_Fixed.creation_date = datestr(now);
FullStroke_Fixed.corrections = 'Yaw: [70,80,90], Roll: positive, Flow: [0,0.1]';

% Save
save('Standardized_Data_Sets/FullStroke_Fixed.mat', 'FullStroke_Fixed');
fprintf('  Saved FullStroke_Fixed.mat with %d experiments\n', FullStroke_Fixed.total_experiments);

%% FIX PADDLE STROKE - Load original and recreate
fprintf('Fixing Paddle Stroke dataset...\n');

load('Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat');

PaddleStroke_Fixed = struct();
PaddleStroke_Fixed.data = results.data;
PaddleStroke_Fixed.parameters = results.parameters;
PaddleStroke_Fixed.zeros = results.zeros;

% Fix settings
PaddleStroke_Fixed.period_settings = [1.75 2.25];
PaddleStroke_Fixed.y_amp_settings = [70 80 90]; % Map: 60->70, 75->80, 90->90
PaddleStroke_Fixed.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Positive values
PaddleStroke_Fixed.Flow_Speed_settings = [0 0.1]; % 0 and 0.1 m/s

% Add metadata
PaddleStroke_Fixed.experiment_type = 'Paddle_Stroke_Fixed';
PaddleStroke_Fixed.source_files = {'19-Oct-2022'};
PaddleStroke_Fixed.total_experiments = numel(results.data);
PaddleStroke_Fixed.creation_date = datestr(now);
PaddleStroke_Fixed.corrections = 'Yaw: [70,80,90], Roll: positive, Flow: [0,0.1]';

% Save
save('Standardized_Data_Sets/PaddleStroke_Fixed.mat', 'PaddleStroke_Fixed');
fprintf('  Saved PaddleStroke_Fixed.mat with %d experiments\n', PaddleStroke_Fixed.total_experiments);

%% FIX POWER STROKE - Load original and recreate
fprintf('Fixing Power Stroke dataset...\n');

load('Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat');
results_1 = results;

load('Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
results_2 = results;

PowerStroke_Fixed = struct();
PowerStroke_Fixed.data = [results_1.data, results_2.data];
PowerStroke_Fixed.parameters = [results_1.parameters, results_2.parameters];
PowerStroke_Fixed.zeros = [results_1.zeros, results_2.zeros];

% Fix settings
PowerStroke_Fixed.period_settings = [1.75 2.25];
PowerStroke_Fixed.y_amp_settings = [70 80 90]; % Map: 60->70, 75->80, 90->90
PowerStroke_Fixed.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Reduced set, positive
PowerStroke_Fixed.Flow_Speed_settings = [0 0.1]; % Only 0 and 0.1 m/s

% Add metadata
PowerStroke_Fixed.experiment_type = 'Power_Stroke_Fixed';
PowerStroke_Fixed.source_files = {'14-Oct-2022', '07-Oct-2022'};
PowerStroke_Fixed.total_experiments = length(PowerStroke_Fixed.data);
PowerStroke_Fixed.creation_date = datestr(now);
PowerStroke_Fixed.corrections = 'Yaw: [70,80,90], Roll: reduced positive set, Flow: [0,0.1]';

% Save
save('Standardized_Data_Sets/PowerStroke_Fixed.mat', 'PowerStroke_Fixed');
fprintf('  Saved PowerStroke_Fixed.mat with %d experiments\n', PowerStroke_Fixed.total_experiments);

fprintf('\nAll datasets fixed and saved!\n');
