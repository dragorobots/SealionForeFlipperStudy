% Debug script that writes to file
clear all
clc

% Open output file
fid = fopen('debug_results.txt', 'w');

try
    fprintf(fid, 'Starting debug...\n');
    
    % Load the processed data
    load('data/processed/2025-01-27_ProcessedData/FullStroke_Processed_2025-01-27.mat');
    
    fprintf(fid, 'Loaded combined_data successfully\n');
    fprintf(fid, 'Type: %s\n', class(combined_data));
    fprintf(fid, 'Fields: %s\n', strjoin(fieldnames(combined_data), ', '));
    
    % Check metadata
    if isfield(combined_data, 'metadata')
        fprintf(fid, '\nMetadata:\n');
        fprintf(fid, '  Experiment type: %s\n', combined_data.metadata.experiment_type);
        fprintf(fid, '  Total experiments: %d\n', combined_data.metadata.total_experiments);
        fprintf(fid, '  From 20-Jan: %d\n', combined_data.metadata.experiments_from_20Jan);
        fprintf(fid, '  From 30-Jan: %d\n', combined_data.metadata.experiments_from_30Jan);
    end
    
    % Check data structure
    fprintf(fid, '\nData structure:\n');
    fprintf(fid, '  Data field type: %s\n', class(combined_data.data));
    fprintf(fid, '  Data field length: %d\n', length(combined_data.data));
    
    fprintf(fid, '  Parameters field type: %s\n', class(combined_data.parameters));
    fprintf(fid, '  Parameters field length: %d\n', length(combined_data.parameters));
    
    fprintf(fid, '  Zeros field type: %s\n', class(combined_data.zeros));
    fprintf(fid, '  Zeros field length: %d\n', length(combined_data.zeros));
    
    % Check first few experiments
    if length(combined_data.parameters) > 0
        fprintf(fid, '\nFirst 3 experiments:\n');
        for i = 1:min(3, length(combined_data.parameters))
            if iscell(combined_data.parameters) && length(combined_data.parameters) >= i
                params = combined_data.parameters{i}.parameters;
                fprintf(fid, '  Exp %d: Period=%.2f, Yaw=%.0f, Paddle=%.2f, Flow=%.1f, Roll=%.0f\n', ...
                    i, params(1), params(2), params(3), params(4), params(5));
            end
        end
    else
        fprintf(fid, 'No parameters found!\n');
    end
    
    fprintf(fid, '\nDebug complete!\n');
    
catch ME
    fprintf(fid, 'Error: %s\n', ME.message);
    fprintf(fid, 'Stack trace:\n');
    for i = 1:length(ME.stack)
        fprintf(fid, '  %s (line %d)\n', ME.stack(i).name, ME.stack(i).line);
    end
end

fclose(fid);
clear

