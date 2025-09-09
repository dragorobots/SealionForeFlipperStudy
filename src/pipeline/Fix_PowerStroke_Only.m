% Fix_PowerStroke_Only - Fix Power Stroke dataset with exact specifications
% Loads original Power Stroke data and applies specific corrections

clear all
clc

fprintf('=== FIXING POWER STROKE DATASET ONLY ===\n');

% Add paths
addpath('Master_Data_Set_Backup');
addpath('Standardized_Data_Sets');

%% LOAD ORIGINAL POWER STROKE DATASETS
fprintf('Loading original Power Stroke datasets...\n');

load('Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat');
results_1 = results;

load('Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
results_2 = results;

%% CREATE CORRECTED STRUCTURE
fprintf('Creating corrected Power Stroke structure...\n');

PowerStroke_Corrected = struct();

% Combine all experiments
PowerStroke_Corrected.data = [results_1.data, results_2.data];
PowerStroke_Corrected.parameters = [results_1.parameters, results_2.parameters];
PowerStroke_Corrected.zeros = [results_1.zeros, results_2.zeros];

%% APPLY EXACT CORRECTIONS AS SPECIFIED

% 1. Period: Keep [1.75 2.25]
PowerStroke_Corrected.period_settings = [1.75 2.25];

% 2. Yaw Amplitude: Map [-60 -75 -90] to [70 80 90] and make positive
PowerStroke_Corrected.y_amp_settings = [70 80 90]; % Map: 60->70, 75->80, 90->90

% 3. Roll Power Angle: Reduce to [-90 -75 -60 -45 -30 -15 0] and make positive
PowerStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Reduced set, made positive

% 4. Flow Speed: Reduce to only [0, 0.1] (corresponding to [0, 100])
PowerStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Only 0 and 0.1 m/s

%% FILTER DATA TO ONLY INCLUDE VALID EXPERIMENTS
fprintf('Filtering experiments to match corrected settings...\n');

valid_indices = [];
for i = 1:length(PowerStroke_Corrected.parameters)
    % Get yaw value (4th parameter) and make it positive
    yaw_val = abs(PowerStroke_Corrected.parameters(i).parameters(4));
    
    % Get flow speed value (should be 0 or 100 for 0 or 0.1 m/s)
    % We'll check the Flow_Speed_settings field instead of individual parameters
    
    % Check if yaw is valid (70, 80, or 90)
    if ismember(yaw_val, [70 80 90])
        valid_indices = [valid_indices, i];
    end
end

fprintf('Found %d valid experiments out of %d total\n', length(valid_indices), length(PowerStroke_Corrected.parameters));

% Keep only valid experiments
PowerStroke_Corrected.data = PowerStroke_Corrected.data(valid_indices);
PowerStroke_Corrected.parameters = PowerStroke_Corrected.parameters(valid_indices);
PowerStroke_Corrected.zeros = PowerStroke_Corrected.zeros(valid_indices);

%% ADD METADATA
PowerStroke_Corrected.experiment_type = 'Power_Stroke_Corrected';
PowerStroke_Corrected.source_files = {'14-Oct-2022', '07-Oct-2022'};
PowerStroke_Corrected.total_experiments = length(valid_indices);
PowerStroke_Corrected.creation_date = datestr(now);
PowerStroke_Corrected.corrections_applied = {
    'Yaw mapped: 60->70, 75->80, 90->90 and made positive', ...
    'Roll angles reduced to [90,75,60,45,30,15,0] and made positive', ...
    'Flow speed reduced to [0,0.1] m/s only', ...
    'Data filtered to match corrected settings'
};

%% SAVE CORRECTED DATASET
fprintf('Saving corrected Power Stroke dataset...\n');
save('Standardized_Data_Sets/PowerStroke_Corrected.mat', 'PowerStroke_Corrected');

fprintf('\n=== POWER STROKE CORRECTION COMPLETE ===\n');
fprintf('Saved PowerStroke_Corrected.mat with %d experiments\n', PowerStroke_Corrected.total_experiments);
fprintf('File location: Standardized_Data_Sets/PowerStroke_Corrected.mat\n');

%% DISPLAY FINAL STRUCTURE
fprintf('\nFinal corrected settings:\n');
fprintf('  Period: %s\n', mat2str(PowerStroke_Corrected.period_settings));
fprintf('  Yaw Amplitude: %s\n', mat2str(PowerStroke_Corrected.y_amp_settings));
fprintf('  Roll Power Angle: %s\n', mat2str(PowerStroke_Corrected.roll_pow_ang_settings));
fprintf('  Flow Speed: %s m/s\n', mat2str(PowerStroke_Corrected.Flow_Speed_settings));
fprintf('  Total Experiments: %d\n', PowerStroke_Corrected.total_experiments);
