% Debug script to understand data structure and write to file
clear all
clc

% Open output file
fid = fopen('debug_output.txt', 'w');
fprintf(fid, 'Starting debug...\n');

% Add paths
addpath('data/raw/Master_Data_Set_Backup');

try
    % Load 20-Jan dataset
    fprintf(fid, 'Loading 20-Jan dataset...\n');
    load('20-Jan-2023_results_FullStroke.mat');
    fprintf(fid, 'Dataset loaded successfully\n');
    
    % Check structure
    fprintf(fid, 'Results type: %s\n', class(results));
    fprintf(fid, 'Results size: %s\n', mat2str(size(results)));
    
    if isstruct(results)
        fields = fieldnames(results);
        fprintf(fid, 'Fields: %s\n', strjoin(fields, ', '));
        
        % Check data field
        if isfield(results, 'data')
            fprintf(fid, 'Data field type: %s\n', class(results.data));
            fprintf(fid, 'Data field size: %s\n', mat2str(size(results.data)));
        end
        
        % Check parameters field
        if isfield(results, 'parameters')
            fprintf(fid, 'Parameters field type: %s\n', class(results.parameters));
            fprintf(fid, 'Parameters field size: %s\n', mat2str(size(results.parameters)));
            
            if length(results.parameters) > 0
                fprintf(fid, 'First parameter type: %s\n', class(results.parameters(1)));
                if isstruct(results.parameters(1))
                    param_fields = fieldnames(results.parameters(1));
                    fprintf(fid, 'First parameter fields: %s\n', strjoin(param_fields, ', '));
                    
                    if isfield(results.parameters(1), 'parameters')
                        fprintf(fid, 'First parameter values: %s\n', mat2str(results.parameters(1).parameters));
                    end
                end
            end
        end
        
        % Check zeros field
        if isfield(results, 'zeros')
            fprintf(fid, 'Zeros field type: %s\n', class(results.zeros));
            fprintf(fid, 'Zeros field size: %s\n', mat2str(size(results.zeros)));
        end
    end
    
    fprintf(fid, 'Debug complete!\n');
    
catch ME
    fprintf(fid, 'Error: %s\n', ME.message);
    fprintf(fid, 'Stack trace:\n');
    for i = 1:length(ME.stack)
        fprintf(fid, '  %s (line %d)\n', ME.stack(i).name, ME.stack(i).line);
    end
end

fclose(fid);
clear

