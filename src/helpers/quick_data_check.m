% Quick check of data structure
addpath('data/raw/Master_Data_Set_Backup')

% Load 20-Jan dataset
load('20-Jan-2023_results_FullStroke.mat')
var_name = who;
data_struct = eval(var_name{1});

fprintf('Dataset: %s\n', var_name{1});
fprintf('Fields: %s\n', strjoin(fieldnames(data_struct), ', '));
fprintf('Number of experiments: %d\n', length(data_struct.exp_num));

% Check data dimensions
data_fields = fieldnames(data_struct.data);
first_data = data_struct.data.(data_fields{1});
fprintf('Data dimensions: %dx%d (time x channels)\n', size(first_data,1), size(first_data,2));

% Check parameters
param_fields = fieldnames(data_struct.parameters);
fprintf('Parameter fields: %d\n', length(param_fields));

clear

