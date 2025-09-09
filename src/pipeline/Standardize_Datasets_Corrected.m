% Standardize_Datasets_Corrected - Create corrected standardized datasets
% Based on user requirements for curated power, paddle, and full stroke data
% with corrected settings as specified

clear all
clc
close all

fprintf('=== CREATING CORRECTED STANDARDIZED DATASETS ===\n');
fprintf('Processing datasets with corrected settings...\n\n');

% Add paths
addpath('Master_Data_Set_Backup');
addpath('Standardized_Data_Sets');

%% CREATE CORRECTED FULL STROKE DATASET
fprintf('Processing Full Stroke datasets...\n');
create_corrected_full_stroke();

%% CREATE CORRECTED PADDLE STROKE DATASET  
fprintf('Processing Paddle Stroke datasets...\n');
create_corrected_paddle_stroke();

%% CREATE CORRECTED POWER STROKE DATASET
fprintf('Processing Power Stroke datasets...\n');
create_corrected_power_stroke();

fprintf('\nCorrected standardization complete! Check Standardized_Data_Sets folder.\n');

function create_corrected_full_stroke()
    % Create corrected Full Stroke dataset with:
    % - Yaw Amplitude: [70 80 90] (positive, truncated from [-70 -80 -90 -100])
    % - Flow Speed: [0 0.1] (ordered 0 first, then 0.1, from [0.1 0.05 0])
    
    % Load all three Full Stroke datasets
    load('Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat');
    results_1 = results;
    
    load('Master_Data_Set_Backup/23-Jan-2023_results_FullStroke.mat');
    results_2 = results;
    
    load('Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat');
    results_3 = results;
    
    % Create corrected standardized structure
    FullStroke_Corrected = struct();
    
    % Combine all experiments
    FullStroke_Corrected.data = [results_1.data, results_2.data, results_3.data];
    FullStroke_Corrected.parameters = [results_1.parameters, results_2.parameters, results_3.parameters];
    FullStroke_Corrected.zeros = [results_1.zeros, results_2.zeros, results_3.zeros];
    
    % Apply corrected settings
    FullStroke_Corrected.period_settings = results_1.period_settings; % Keep as is: [1.75 2.25]
    FullStroke_Corrected.y_amp_settings = [70 80 90]; % Corrected: positive, truncated from [-70 -80 -90 -100]
    FullStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Corrected: positive values
    FullStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Corrected: ordered 0 first, then 0.1
    
    % Add metadata
    FullStroke_Corrected.experiment_type = 'Full_Stroke';
    FullStroke_Corrected.source_files = {'20-Jan-2023', '23-Jan-2023', '30-Jan-2023'};
    FullStroke_Corrected.total_experiments = length(FullStroke_Corrected.data);
    FullStroke_Corrected.creation_date = datestr(now);
    
    % Save corrected dataset
    save('Standardized_Data_Sets/FullStroke_Corrected.mat', 'FullStroke_Corrected');
    fprintf('  Saved FullStroke_Corrected.mat with %d experiments\n', FullStroke_Corrected.total_experiments);
    fprintf('    Yaw Amplitude: [70 80 90]\n');
    fprintf('    Roll Power Angle: [90 75 60 45 30 15 0]\n');
    fprintf('    Flow Speed: [0 0.1]\n');
end

function create_corrected_paddle_stroke()
    % Create corrected Paddle Stroke dataset with:
    % - Yaw Amplitude: [70 80 90] (positive, corrected from [-60 -75 -90])
    % - Flow Speed: [0 0.1] (corrected from [0 70] which should be [0 100])
    
    load('Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat');
    
    % Create corrected standardized structure
    PaddleStroke_Corrected = struct();
    
    % Copy essential data (Paddle Stroke has different structure - single arrays, not cell arrays)
    PaddleStroke_Corrected.data = results.data; % [7500 x 3] numeric array
    PaddleStroke_Corrected.parameters = results.parameters; % [1 x 4] numeric array
    PaddleStroke_Corrected.zeros = results.zeros; % [1500 x 3] numeric array
    
    % Apply corrected settings
    PaddleStroke_Corrected.period_settings = results.period_settings; % Keep as is: [1.75 2.25]
    PaddleStroke_Corrected.y_amp_settings = [70 80 90]; % Corrected: positive, from [-60 -75 -90]
    PaddleStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Corrected: positive values
    PaddleStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Corrected: from [0 70] to [0 0.1]
    
    % Add metadata
    PaddleStroke_Corrected.experiment_type = 'Paddle_Stroke';
    PaddleStroke_Corrected.source_files = {'19-Oct-2022'};
    PaddleStroke_Corrected.total_experiments = 1; % Single experiment with 7500 data points
    PaddleStroke_Corrected.creation_date = datestr(now);
    
    % Save corrected dataset
    save('Standardized_Data_Sets/PaddleStroke_Corrected.mat', 'PaddleStroke_Corrected');
    fprintf('  Saved PaddleStroke_Corrected.mat with %d experiment (7500 data points)\n', PaddleStroke_Corrected.total_experiments);
    fprintf('    Yaw Amplitude: [70 80 90]\n');
    fprintf('    Roll Power Angle: [90 75 60 45 30 15 0]\n');
    fprintf('    Flow Speed: [0 0.1]\n');
end

function create_corrected_power_stroke()
    % Create corrected Power Stroke dataset with:
    % - Yaw Amplitude: [70 80 90] (positive, corrected from [-60 -75 -90])
    % - Roll Power Angle: [90 75 60 45 30 15 0] (positive, reduced from [-90 -75 -60 -55 -50 -45 -40 -35 -30 -15 0])
    % - Flow Speed: [0 0.1] (reduced from [100 0 28 70], ordered 0 first)
    
    load('Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat');
    results_1 = results;
    
    load('Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
    results_2 = results;
    
    % Create corrected standardized structure
    PowerStroke_Corrected = struct();
    
    % Combine all experiments
    PowerStroke_Corrected.data = [results_1.data, results_2.data];
    PowerStroke_Corrected.parameters = [results_1.parameters, results_2.parameters];
    PowerStroke_Corrected.zeros = [results_1.zeros, results_2.zeros];
    
    % Apply corrected settings
    PowerStroke_Corrected.period_settings = results_1.period_settings; % Keep as is: [1.75 2.25]
    PowerStroke_Corrected.y_amp_settings = [70 80 90]; % Corrected: positive, from [-60 -75 -90]
    PowerStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Corrected: positive, reduced set
    PowerStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Corrected: reduced from [100 0 28 70], ordered 0 first
    
    % Add metadata
    PowerStroke_Corrected.experiment_type = 'Power_Stroke';
    PowerStroke_Corrected.source_files = {'14-Oct-2022', '07-Oct-2022'};
    PowerStroke_Corrected.total_experiments = length(PowerStroke_Corrected.data);
    PowerStroke_Corrected.creation_date = datestr(now);
    
    % Save corrected dataset
    save('Standardized_Data_Sets/PowerStroke_Corrected.mat', 'PowerStroke_Corrected');
    fprintf('  Saved PowerStroke_Corrected.mat with %d experiments\n', PowerStroke_Corrected.total_experiments);
    fprintf('    Yaw Amplitude: [70 80 90]\n');
    fprintf('    Roll Power Angle: [90 75 60 45 30 15 0]\n');
    fprintf('    Flow Speed: [0 0.1]\n');
end
