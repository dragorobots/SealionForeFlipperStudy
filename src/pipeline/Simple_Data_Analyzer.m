% Simple_Data_Analyzer - Quick analysis of all data structs
% This script loads and analyzes all data files in Master_Data_Set_Backup

clear all
clc

fprintf('=== DATA STRUCT ANALYZER ===\n');
fprintf('Analyzing all data files in Master_Data_Set_Backup folder...\n\n');

% Add path to backup folder
addpath('Master_Data_Set_Backup');

% List of all data files
data_files = {
    '20-Jan-2023_results_FullStroke.mat', ...
    '23-Jan-2023_results_FullStroke.mat', ...
    '30-Jan-2023_results_FullStroke.mat', ...
    '19-Oct-2022_results_PaddleStroke.mat', ...
    '14-Oct-2022_results_PowerStroke.mat', ...
    '07-Oct-2022_results_PowerStroke.mat'
};

% File categories
file_categories = {
    'Full Stroke', ...
    'Full Stroke', ...
    'Full Stroke', ...
    'Paddle Stroke', ...
    'Power Stroke', ...
    'Power Stroke'
};

for i = 1:length(data_files)
    fprintf('============================================================\n');
    fprintf('FILE %d/%d: %s\n', i, length(data_files), data_files{i});
    fprintf('CATEGORY: %s\n', file_categories{i});
    fprintf('============================================================\n');
    
    try
        % Load the data file
        data_path = fullfile('Master_Data_Set_Backup', data_files{i});
        load(data_path);
        
        % Check what variables were loaded
        vars = who;
        fprintf('Variables loaded: %s\n', strjoin(vars, ', '));
        
        % Find the main results variable
        if ismember('results', vars)
            main_var = 'results';
        else
            main_var = vars{1}; % Use first variable
        end
        
        fprintf('Main data variable: %s\n', main_var);
        
        % Get the main data structure
        main_data = eval(main_var);
        
        % Display basic structure information
        fprintf('\n--- STRUCTURE ANALYSIS ---\n');
        fprintf('Data type: %s\n', class(main_data));
        fprintf('Size: %s\n', mat2str(size(main_data)));
        
        if isstruct(main_data)
            fields = fieldnames(main_data);
            fprintf('Fields: %s\n', strjoin(fields, ', '));
            
            % Analyze key fields
            if isfield(main_data, 'data')
                fprintf('\nDATA FIELD:\n');
                fprintf('  Type: %s\n', class(main_data.data));
                fprintf('  Size: %s\n', mat2str(size(main_data.data)));
                if iscell(main_data.data) && length(main_data.data) > 0
                    fprintf('  Number of experiments: %d\n', length(main_data.data));
                    if isfield(main_data.data{1}, 'data')
                        data_size = size(main_data.data{1}.data);
                        fprintf('  Data matrix size per experiment: %s\n', mat2str(data_size));
                    end
                end
            end
            
            if isfield(main_data, 'parameters')
                fprintf('\nPARAMETERS FIELD:\n');
                fprintf('  Type: %s\n', class(main_data.parameters));
                fprintf('  Size: %s\n', mat2str(size(main_data.parameters)));
            end
            
            if isfield(main_data, 'zeros')
                fprintf('\nZEROS FIELD:\n');
                fprintf('  Type: %s\n', class(main_data.zeros));
                fprintf('  Size: %s\n', mat2str(size(main_data.zeros)));
            end
            
            % Check for settings fields
            settings_fields = {'period_settings', 'y_amp_settings', 'roll_pow_ang_settings', 'Flow_Speed_settings'};
            for j = 1:length(settings_fields)
                if isfield(main_data, settings_fields{j})
                    settings_data = main_data.(settings_fields{j});
                    fprintf('\n%s:\n', upper(settings_fields{j}));
                    fprintf('  Values: %s\n', mat2str(settings_data));
                end
            end
        end
        
        % Display file size information
        file_info = dir(fullfile('Master_Data_Set_Backup', data_files{i}));
        fprintf('\n--- FILE INFORMATION ---\n');
        fprintf('File size: %.2f MB\n', file_info.bytes / (1024^2));
        
    catch ME
        fprintf('ERROR loading %s: %s\n', data_files{i}, ME.message);
    end
    
    fprintf('\n');
end

fprintf('Analysis complete!\n');


