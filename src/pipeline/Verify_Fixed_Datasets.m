% Verify_Fixed_Datasets - Check the corrected standardized datasets
% This script loads and displays information about the fixed datasets

clear all
clc

fprintf('=== VERIFYING FIXED DATASETS ===\n\n');

% Add path to standardized datasets
addpath('Standardized_Data_Sets');

% Check each fixed dataset
datasets = {'FullStroke_Fixed', 'PaddleStroke_Fixed', 'PowerStroke_Fixed'};

for i = 1:length(datasets)
    fprintf('==========================================\n');
    fprintf('DATASET: %s\n', datasets{i});
    fprintf('==========================================\n');
    
    try
        % Load the dataset
        load([datasets{i} '.mat']);
        data_struct = eval(datasets{i});
        
        % Display basic info
        fprintf('Experiment Type: %s\n', data_struct.experiment_type);
        fprintf('Total Experiments: %d\n', data_struct.total_experiments);
        fprintf('Source Files: %s\n', strjoin(data_struct.source_files, ', '));
        fprintf('Creation Date: %s\n', data_struct.creation_date);
        fprintf('Corrections: %s\n', data_struct.corrections);
        
        % Display corrected settings
        fprintf('\nCORRECTED SETTINGS:\n');
        fprintf('  Period: %s\n', mat2str(data_struct.period_settings));
        fprintf('  Yaw Amplitude: %s\n', mat2str(data_struct.y_amp_settings));
        fprintf('  Roll Power Angle: %s\n', mat2str(data_struct.roll_pow_ang_settings));
        fprintf('  Flow Speed: %s m/s\n', mat2str(data_struct.Flow_Speed_settings));
        
        % Display data structure info
        fprintf('\nData Structure:\n');
        fprintf('  Data field size: %s\n', mat2str(size(data_struct.data)));
        fprintf('  Parameters field size: %s\n', mat2str(size(data_struct.parameters)));
        fprintf('  Zeros field size: %s\n', mat2str(size(data_struct.zeros)));
        
        % Check if data is accessible
        if isfield(data_struct.data(1), 'data')
            sample_data = data_struct.data(1).data;
            fprintf('  Sample data size: %s\n', mat2str(size(sample_data)));
            fprintf('  Data columns: %d (likely [Thrust, Lift, Arduino])\n', size(sample_data, 2));
        end
        
        fprintf('\n');
        
    catch ME
        fprintf('ERROR loading %s: %s\n', datasets{i}, ME.message);
    end
end

fprintf('Verification complete!\n');
