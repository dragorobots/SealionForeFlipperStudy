% Test script to understand the actual data structure
clear all
clc

% Add paths
addpath('data/raw/Master_Data_Set_Backup');

% Load 20-Jan dataset
fprintf('Loading 20-Jan dataset...\n');
load('20-Jan-2023_results_FullStroke.mat');
var_name = who;
data_struct = eval(var_name{1});

fprintf('Dataset loaded: %s\n', var_name{1});
fprintf('Fields: %s\n', strjoin(fieldnames(data_struct), ', '));

% Check if data is in a cell array or struct
if isfield(data_struct, 'data')
    fprintf('Data field exists\n');
    if iscell(data_struct.data)
        fprintf('Data is a cell array with %d elements\n', length(data_struct.data));
        if length(data_struct.data) > 0
            first_data = data_struct.data{1};
            fprintf('First data element type: %s\n', class(first_data));
            if isstruct(first_data)
                fprintf('First data element fields: %s\n', strjoin(fieldnames(first_data), ', '));
            end
        end
    elseif isstruct(data_struct.data)
        fprintf('Data is a struct with %d fields\n', length(fieldnames(data_struct.data)));
        data_fields = fieldnames(data_struct.data);
        if length(data_fields) > 0
            first_field = data_fields{1};
            first_data = data_struct.data.(first_field);
            fprintf('First data field (%s) type: %s\n', first_field, class(first_data));
            if isnumeric(first_data)
                fprintf('First data dimensions: %dx%d\n', size(first_data,1), size(first_data,2));
            end
        end
    end
end

% Check parameters structure
if isfield(data_struct, 'parameters')
    fprintf('Parameters field exists\n');
    if isstruct(data_struct.parameters)
        param_fields = fieldnames(data_struct.parameters);
        fprintf('Parameters has %d fields\n', length(param_fields));
        if length(param_fields) > 0
            first_param = data_struct.parameters.(param_fields{1});
            fprintf('First parameter type: %s\n', class(first_param));
            if isstruct(first_param)
                fprintf('First parameter fields: %s\n', strjoin(fieldnames(first_param), ', '));
            end
        end
    end
end

% Check zeros structure
if isfield(data_struct, 'zeros')
    fprintf('Zeros field exists\n');
    if isstruct(data_struct.zeros)
        zeros_fields = fieldnames(data_struct.zeros);
        fprintf('Zeros has %d fields\n', length(zeros_fields));
    end
end

clear

