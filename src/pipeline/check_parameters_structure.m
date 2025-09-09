% Check parameters structure in datasets
clear all
clc

% Check Full Stroke
load('Master_Data_Set_Backup/20-Jan-2023_results_FullStroke.mat');
fprintf('Full Stroke parameters:\n');
fprintf('  Type: %s\n', class(results.parameters));
fprintf('  Size: [%s]\n', num2str(size(results.parameters)));
if iscell(results.parameters)
    fprintf('  First element: %s, size [%s]\n', class(results.parameters{1}), num2str(size(results.parameters{1})));
    fprintf('  First element values: [%s]\n', num2str(results.parameters{1}));
else
    fprintf('  Values: [%s]\n', num2str(results.parameters));
end
fprintf('\n');

% Check Power Stroke
load('Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat');
fprintf('Power Stroke parameters:\n');
fprintf('  Type: %s\n', class(results.parameters));
fprintf('  Size: [%s]\n', num2str(size(results.parameters)));
if iscell(results.parameters)
    fprintf('  First element: %s, size [%s]\n', class(results.parameters{1}), num2str(size(results.parameters{1})));
    fprintf('  First element values: [%s]\n', num2str(results.parameters{1}));
else
    fprintf('  Values: [%s]\n', num2str(results.parameters));
end
fprintf('\n');

% Check Paddle Stroke
load('Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat');
fprintf('Paddle Stroke parameters:\n');
fprintf('  Type: %s\n', class(results));
fprintf('  Size: [%s]\n', num2str(size(results)));
if isstruct(results) && numel(results) > 1
    fprintf('  First experiment parameters: %s, size [%s]\n', class(results(1).parameters), num2str(size(results(1).parameters)));
    fprintf('  First experiment parameters values: [%s]\n', num2str(results(1).parameters));
end
