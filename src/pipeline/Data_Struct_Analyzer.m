function Data_Struct_Analyzer()
% Data_Struct_Analyzer - Comprehensive analysis of all data structs
% This script loads and analyzes all data files in Master_Data_Set_Backup
% to provide detailed information about their structure and contents

clear all
clc
close all

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

% Initialize summary structure
summary = struct();

for i = 1:length(data_files)
    fprintf('=' * ones(1, 60));
    fprintf('\n');
    fprintf('FILE %d/%d: %s\n', i, length(data_files), data_files{i});
    fprintf('CATEGORY: %s\n', file_categories{i});
    fprintf('=' * ones(1, 60));
    fprintf('\n');
    
    try
        % Load the data file
        data_path = fullfile('Master_Data_Set_Backup', data_files{i});
        load(data_path);
        
        % Analyze the loaded data
        analyze_data_struct(data_files{i}, file_categories{i});
        
        % Store summary info
        summary(i).filename = data_files{i};
        summary(i).category = file_categories{i};
        summary(i).loaded_successfully = true;
        
    catch ME
        fprintf('ERROR loading %s: %s\n', data_files{i}, ME.message);
        summary(i).filename = data_files{i};
        summary(i).category = file_categories{i};
        summary(i).loaded_successfully = false;
        summary(i).error = ME.message;
    end
    
    fprintf('\n');
end

% Display overall summary
fprintf('=' * ones(1, 80));
fprintf('\n');
fprintf('OVERALL SUMMARY\n');
fprintf('=' * ones(1, 80));
fprintf('\n');

for i = 1:length(summary)
    status = 'SUCCESS';
    if ~summary(i).loaded_successfully
        status = 'FAILED';
    end
    fprintf('%s: %s (%s)\n', status, summary(i).filename, summary(i).category);
end

fprintf('\nAnalysis complete!\n');

end

function analyze_data_struct(filename, category)
% Analyze individual data struct and display detailed information

% Check what variables were loaded
vars = who;
fprintf('Variables loaded: %s\n', strjoin(vars, ', '));

% Find the main results variable
if ismember('results', vars)
    main_var = 'results';
else
    % Look for other common variable names
    for i = 1:length(vars)
        if contains(vars{i}, 'result', 'IgnoreCase', true)
            main_var = vars{i};
            break;
        end
    end
    if ~exist('main_var', 'var')
        main_var = vars{1}; % Use first variable if no results found
    end
end

fprintf('Main data variable: %s\n', main_var);

% Get the main data structure
main_data = eval(main_var);

% Display basic structure information
fprintf('\n--- STRUCTURE ANALYSIS ---\n');
fprintf('Data type: %s\n', class(main_data));
fprintf('Size: %s\n', mat2str(size(main_data)));

if isstruct(main_data)
    fprintf('Fields: %s\n', strjoin(fieldnames(main_data), ', '));
    
    % Analyze each field
    fields = fieldnames(main_data);
    for i = 1:length(fields)
        field_name = fields{i};
        field_data = main_data.(field_name);
        
        fprintf('\n  Field: %s\n', field_name);
        fprintf('    Type: %s\n', class(field_data));
        fprintf('    Size: %s\n', mat2str(size(field_data)));
        
        if isstruct(field_data)
            fprintf('    Sub-fields: %s\n', strjoin(fieldnames(field_data), ', '));
        elseif iscell(field_data)
            fprintf('    Cell array with %d elements\n', numel(field_data));
            if numel(field_data) > 0
                fprintf('    First element type: %s\n', class(field_data{1}));
                if isstruct(field_data{1})
                    fprintf('    First element fields: %s\n', strjoin(fieldnames(field_data{1}), ', '));
                end
            end
        elseif isnumeric(field_data)
            if numel(field_data) <= 10
                fprintf('    Values: %s\n', mat2str(field_data));
            else
                fprintf('    Range: [%.3f, %.3f]\n', min(field_data(:)), max(field_data(:)));
                fprintf('    Mean: %.3f\n', mean(field_data(:)));
            end
        end
    end
end

% Look for specific experimental parameters
fprintf('\n--- EXPERIMENTAL PARAMETERS ---\n');
if isstruct(main_data)
    % Check for common parameter fields
    param_fields = {'parameters', 'period_settings', 'y_amp_settings', ...
                   'roll_pow_ang_settings', 'Flow_Speed_settings', ...
                   'exp_num', 'data', 'zeros'};
    
    for i = 1:length(param_fields)
        if isfield(main_data, param_fields{i})
            param_data = main_data.(param_fields{i});
            fprintf('%s: %s (size: %s)\n', param_fields{i}, class(param_data), mat2str(size(param_data)));
            
            if isnumeric(param_data) && numel(param_data) <= 20
                fprintf('  Values: %s\n', mat2str(param_data));
            elseif isstruct(param_data) && numel(param_data) <= 5
                fprintf('  Structure with %d elements\n', numel(param_data));
            elseif iscell(param_data)
                fprintf('  Cell array with %d elements\n', numel(param_data));
            end
        end
    end
end

% Analyze data content if available
fprintf('\n--- DATA CONTENT ANALYSIS ---\n');
if isfield(main_data, 'data') && iscell(main_data.data)
    fprintf('Data field contains %d experiments\n', length(main_data.data));
    if length(main_data.data) > 0
        first_data = main_data.data{1};
        if isfield(first_data, 'data')
            data_matrix = first_data.data;
            fprintf('First experiment data size: %s\n', mat2str(size(data_matrix)));
            fprintf('Data columns likely represent: [Thrust, Lift, Arduino_signal]\n');
            if size(data_matrix, 2) >= 2
                fprintf('Thrust range: [%.3f, %.3f] N\n', min(data_matrix(:,1)), max(data_matrix(:,1)));
                fprintf('Lift range: [%.3f, %.3f] N\n', min(data_matrix(:,2)), max(data_matrix(:,2)));
            end
        end
    end
end

% Check for zeros/baseline data
if isfield(main_data, 'zeros') && iscell(main_data.zeros)
    fprintf('Zeros/baseline data available for %d experiments\n', length(main_data.zeros));
end

% Display file size information
file_info = dir(fullfile('Master_Data_Set_Backup', filename));
fprintf('\n--- FILE INFORMATION ---\n');
fprintf('File size: %.2f MB\n', file_info.bytes / (1024^2));
fprintf('Last modified: %s\n', file_info.date);

end


