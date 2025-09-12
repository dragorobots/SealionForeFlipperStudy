% Script to examine the structure of Full Stroke datasets
% This will help us understand the data organization before reorganization

% Add path to data
addpath('data/raw/Master_Data_Set_Backup')

% Load the Full Stroke datasets
fprintf('Loading 20-Jan-2023 Full Stroke dataset...\n')
load('20-Jan-2023_results_FullStroke.mat')

% Get the variable name (should be the same as filename without extension)
var_name = who;
data_struct = eval(var_name{1});

fprintf('Dataset loaded: %s\n', var_name{1});
fprintf('Number of experiments: %d\n', length(data_struct.exp_num));

% Display the structure fields
fprintf('\n=== STRUCTURE FIELDS ===\n')
field_names = fieldnames(data_struct);
for i = 1:length(field_names)
    fprintf('%d. %s\n', i, field_names{i});
end

% Examine key fields
fprintf('\n=== KEY FIELD EXAMINATION ===\n')

% Check experiment type
fprintf('Experiment type: %s\n', data_struct.experiment_type);

% Check number of experiments
fprintf('Number of experiments: %d\n', length(data_struct.exp_num));

% Check parameters structure
fprintf('\nParameters field structure:\n');
if isfield(data_struct, 'parameters')
    param_fields = fieldnames(data_struct.parameters);
    fprintf('Parameter fields (%d total):\n', length(param_fields));
    for i = 1:min(10, length(param_fields))  % Show first 10
        fprintf('  %s\n', param_fields{i});
    end
    if length(param_fields) > 10
        fprintf('  ... and %d more\n', length(param_fields) - 10);
    end
end

% Check data structure
fprintf('\nData field structure:\n');
if isfield(data_struct, 'data')
    data_fields = fieldnames(data_struct.data);
    fprintf('Data fields (%d total):\n', length(data_fields));
    for i = 1:min(5, length(data_fields))  % Show first 5
        fprintf('  %s\n', data_fields{i});
    end
    if length(data_fields) > 5
        fprintf('  ... and %d more\n', length(data_fields) - 5);
    end
    
    % Check dimensions of first data field
    if length(data_fields) > 0
        first_field = data_fields{1};
        data_sample = data_struct.data.(first_field);
        fprintf('\nSample data dimensions (%s): %dx%d\n', first_field, size(data_sample,1), size(data_sample,2));
        fprintf('Data appears to be: %d time points x %d channels\n', size(data_sample,1), size(data_sample,2));
    end
end

% Check zeros structure
fprintf('\nZeros field structure:\n');
if isfield(data_struct, 'zeros')
    zeros_fields = fieldnames(data_struct.zeros);
    fprintf('Zeros fields (%d total):\n', length(zeros_fields));
    for i = 1:min(5, length(zeros_fields))  % Show first 5
        fprintf('  %s\n', zeros_fields{i});
    end
    if length(zeros_fields) > 5
        fprintf('  ... and %d more\n', length(zeros_fields) - 5);
    end
end

% Check some parameter values
fprintf('\n=== SAMPLE PARAMETER VALUES ===\n');
if isfield(data_struct, 'parameters')
    % Show first few parameter values
    param_names = fieldnames(data_struct.parameters);
    for i = 1:min(3, length(param_names))
        param_name = param_names{i};
        param_values = data_struct.parameters.(param_name);
        if length(param_values) <= 10
            fprintf('%s: %s\n', param_name, mat2str(param_values));
        else
            fprintf('%s: %s (first 5: %s)\n', param_name, mat2str(size(param_values)), mat2str(param_values(1:5)));
        end
    end
end

fprintf('\n=== SUMMARY ===\n');
fprintf('This dataset contains %d experiments\n', length(data_struct.exp_num));
fprintf('Each experiment has:\n');
fprintf('  - Parameters stored in parameters field\n');
fprintf('  - Zero measurements stored in zeros field\n');
fprintf('  - Time-series data stored in data field\n');
fprintf('  - Data appears to be %d time points x %d channels (lift, thrust, arduino)\n', size(data_sample,1), size(data_sample,2));

% Clear workspace
clear

