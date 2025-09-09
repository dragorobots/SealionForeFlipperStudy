% Relocated on 2025-09-09 from Standardize_Datasets.m to src/pipeline/Standardize_Datasets.m as part of repo reorg.

% Standardize_Datasets - Consolidate and standardize all experiment data
% Creates clean, single .mat files for Power, Paddle, and Full Stroke experiments
% with only essential experimental variables

clear all
clc
close all

fprintf('=== DATASET STANDARDIZATION ===\n');
fprintf('Creating standardized datasets...\n\n');

% Add paths
addpath('../data/raw/Master_Data_Set_Backup');
addpath('../data/processed/Standardized_Data_Sets');

%% STANDARDIZE FULL STROKE DATASETS
fprintf('Processing Full Stroke datasets...\n');
standardize_full_stroke();

%% STANDARDIZE PADDLE STROKE DATASETS  
fprintf('Processing Paddle Stroke datasets...\n');
standardize_paddle_stroke();

%% STANDARDIZE POWER STROKE DATASETS
fprintf('Processing Power Stroke datasets...\n');
standardize_power_stroke();

fprintf('\nStandardization complete! Check Standardized_Data_Sets folder.\n');

function standardize_full_stroke()
    % Consolidate all Full Stroke experiments into one standardized file
    
    % Load all three Full Stroke datasets
    load('../data/raw/Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat');
    results_1 = results;
    
    load('../data/raw/Master_Data_Set_Backup/23-Jan-2023_results_FullStroke.mat');
    results_2 = results;
    
    load('../data/raw/Master_Data_Set_Backup/30-Jan-2023_results_FullStroke.mat');
    
    results_3 = results;
    
    % Create standardized structure
    FullStroke_Standardized = struct();
    
    % Combine all experiments
    FullStroke_Standardized.data = [results_1.data, results_2.data, results_3.data];
    FullStroke_Standardized.parameters = [results_1.parameters, results_2.parameters, results_3.parameters];
    FullStroke_Standardized.zeros = [results_1.zeros, results_2.zeros, results_3.zeros];
    
    % Keep essential settings (they should be the same across all)
    FullStroke_Standardized.period_settings = results_1.period_settings;
    FullStroke_Standardized.y_amp_settings = results_1.y_amp_settings;
    FullStroke_Standardized.roll_pow_ang_settings = results_1.roll_pow_ang_settings;
    FullStroke_Standardized.Flow_Speed_settings = [results_1.Flow_Speed_settings, results_2.Flow_Speed_settings, results_3.Flow_Speed_settings];
    
    % Add metadata
    FullStroke_Standardized.experiment_type = 'Full_Stroke';
    FullStroke_Standardized.source_files = {'20-Jan-2023', '23-Jan-2023', '30-Jan-2023'};
    FullStroke_Standardized.total_experiments = length(FullStroke_Standardized.data);
    FullStroke_Standardized.creation_date = datestr(now);
    
    % Save standardized dataset
    save('../data/processed/Standardized_Data_Sets/FullStroke_Standardized.mat', 'FullStroke_Standardized');
    fprintf('  Saved FullStroke_Standardized.mat with %d experiments\n', FullStroke_Standardized.total_experiments);
end

function standardize_paddle_stroke()
    % Standardize Paddle Stroke dataset
    
    load('../data/raw/Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat');
    
    % Create standardized structure
    PaddleStroke_Standardized = struct();
    
    % Copy essential data
    PaddleStroke_Standardized.data = results.data;
    PaddleStroke_Standardized.parameters = results.parameters;
    PaddleStroke_Standardized.zeros = results.zeros;
    
    % Keep essential settings
    PaddleStroke_Standardized.period_settings = results.period_settings;
    PaddleStroke_Standardized.y_amp_settings = results.y_amp_settings;
    PaddleStroke_Standardized.roll_pow_ang_settings = results.roll_pow_ang_settings;
    PaddleStroke_Standardized.Flow_Speed_settings = results.Flow_Speed_settings;
    
    % Add metadata
    PaddleStroke_Standardized.experiment_type = 'Paddle_Stroke';
    PaddleStroke_Standardized.source_files = {'19-Oct-2022'};
    PaddleStroke_Standardized.total_experiments = numel(results.data);
    PaddleStroke_Standardized.creation_date = datestr(now);
    
    % Save standardized dataset
    save('../data/processed/Standardized_Data_Sets/PaddleStroke_Standardized.mat', 'PaddleStroke_Standardized');
    fprintf('  Saved PaddleStroke_Standardized.mat with %d experiments\n', PaddleStroke_Standardized.total_experiments);
end

function standardize_power_stroke()
    % Consolidate Power Stroke datasets
    
    load('../data/raw/Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat');
    results_1 = results;
    
    load('../data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
    results_2 = results;
    
    % Create standardized structure
    PowerStroke_Standardized = struct();
    
    % Combine all experiments
    PowerStroke_Standardized.data = [results_1.data, results_2.data];
    PowerStroke_Standardized.parameters = [results_1.parameters, results_2.parameters];
    PowerStroke_Standardized.zeros = [results_1.zeros, results_2.zeros];
    
    % Keep essential settings
    PowerStroke_Standardized.period_settings = results_1.period_settings;
    PowerStroke_Standardized.y_amp_settings = results_1.y_amp_settings;
    PowerStroke_Standardized.roll_pow_ang_settings = results_1.roll_pow_ang_settings;
    PowerStroke_Standardized.Flow_Speed_settings = [results_1.Flow_Speed_settings, results_2.Flow_Speed_settings];
    
    % Add metadata
    PowerStroke_Standardized.experiment_type = 'Power_Stroke';
    PowerStroke_Standardized.source_files = {'14-Oct-2022', '07-Oct-2022'};
    PowerStroke_Standardized.total_experiments = length(PowerStroke_Standardized.data);
    PowerStroke_Standardized.creation_date = datestr(now);
    
    % Save standardized dataset
    save('../data/processed/Standardized_Data_Sets/PowerStroke_Standardized.mat', 'PowerStroke_Standardized');
    fprintf('  Saved PowerStroke_Standardized.mat with %d experiments\n', PowerStroke_Standardized.total_experiments);
end

