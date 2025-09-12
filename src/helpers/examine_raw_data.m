% Examine raw data structure to understand parameter format
clear all
clc

% Create output file
fid = fopen('raw_data_examination.txt', 'w');

try
    fprintf(fid, 'Examining raw data structure...\n');
    
    % Add paths
    addpath('data/raw/Master_Data_Set_Backup');
    
    % Load 20-Jan dataset
    fprintf(fid, 'Loading 20-Jan dataset...\n');
    load('20-Jan-2023_results_FullStroke.mat');
    data_struct = results;
    
    fprintf(fid, 'Dataset loaded successfully\n');
    fprintf(fid, 'Number of experiments: %d\n', length(data_struct.data));
    
    % Check parameter structure
    fprintf(fid, '\nParameter structure:\n');
    fprintf(fid, 'Parameters field type: %s\n', class(data_struct.parameters));
    fprintf(fid, 'Parameters field size: %s\n', mat2str(size(data_struct.parameters)));
    
    if length(data_struct.parameters) > 0
        fprintf(fid, 'First parameter type: %s\n', class(data_struct.parameters(1)));
        if isstruct(data_struct.parameters(1))
            fprintf(fid, 'First parameter fields: %s\n', strjoin(fieldnames(data_struct.parameters(1)), ', '));
            
            if isfield(data_struct.parameters(1), 'parameters')
                params = data_struct.parameters(1).parameters;
                fprintf(fid, 'First parameter values: %s\n', mat2str(params));
                fprintf(fid, 'Parameter array length: %d\n', length(params));
            end
        end
    end
    
    % Show first 5 experiments
    fprintf(fid, '\nFirst 5 experiments:\n');
    for i = 1:min(5, length(data_struct.parameters))
        if isstruct(data_struct.parameters(i)) && isfield(data_struct.parameters(i), 'parameters')
            params = data_struct.parameters(i).parameters;
            fprintf(fid, '  Exp %d: %s\n', i, mat2str(params));
        end
    end
    
    % Check data structure
    fprintf(fid, '\nData structure:\n');
    fprintf(fid, 'Data field type: %s\n', class(data_struct.data));
    fprintf(fid, 'Data field size: %s\n', mat2str(size(data_struct.data)));
    
    if length(data_struct.data) > 0
        fprintf(fid, 'First data element type: %s\n', class(data_struct.data(1)));
        if isstruct(data_struct.data(1))
            fprintf(fid, 'First data element fields: %s\n', strjoin(fieldnames(data_struct.data(1)), ', '));
        end
    end
    
    % Check zeros structure
    fprintf(fid, '\nZeros structure:\n');
    fprintf(fid, 'Zeros field type: %s\n', class(data_struct.zeros));
    fprintf(fid, 'Zeros field size: %s\n', mat2str(size(data_struct.zeros)));
    
    if length(data_struct.zeros) > 0
        fprintf(fid, 'First zeros element type: %s\n', class(data_struct.zeros(1)));
        if isstruct(data_struct.zeros(1))
            fprintf(fid, 'First zeros element fields: %s\n', strjoin(fieldnames(data_struct.zeros(1)), ', '));
        end
    end
    
    fprintf(fid, '\nExamination complete!\n');
    
catch ME
    fprintf(fid, 'Error: %s\n', ME.message);
    fprintf(fid, 'Stack trace:\n');
    for i = 1:length(ME.stack)
        fprintf(fid, '  %s (line %d)\n', ME.stack(i).name, ME.stack(i).line);
    end
end

fclose(fid);
clear

