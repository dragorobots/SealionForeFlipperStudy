% Simple test to understand data structure
clear all
clc

fprintf('Starting simple test...\n');

% Add paths
addpath('data/raw/Master_Data_Set_Backup');

% Load 20-Jan dataset
fprintf('Loading 20-Jan dataset...\n');
load('20-Jan-2023_results_FullStroke.mat');
fprintf('Dataset loaded successfully\n');

% Check structure
fprintf('Results type: %s\n', class(results));
fprintf('Results size: %s\n', mat2str(size(results)));

if isstruct(results)
    fields = fieldnames(results);
    fprintf('Fields: %s\n', strjoin(fields, ', '));
    
    % Check data field
    if isfield(results, 'data')
        fprintf('Data field type: %s\n', class(results.data));
        fprintf('Data field size: %s\n', mat2str(size(results.data)));
    end
    
    % Check parameters field
    if isfield(results, 'parameters')
        fprintf('Parameters field type: %s\n', class(results.parameters));
        fprintf('Parameters field size: %s\n', mat2str(size(results.parameters)));
        
        if length(results.parameters) > 0
            fprintf('First parameter type: %s\n', class(results.parameters(1)));
            if isstruct(results.parameters(1))
                param_fields = fieldnames(results.parameters(1));
                fprintf('First parameter fields: %s\n', strjoin(param_fields, ', '));
                
                if isfield(results.parameters(1), 'parameters')
                    fprintf('First parameter values: %s\n', mat2str(results.parameters(1).parameters));
                end
            end
        end
    end
end

fprintf('Test complete!\n');
clear

