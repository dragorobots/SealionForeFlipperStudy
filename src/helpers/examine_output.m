% Examine the output file to see what was created
clear all
clc

fprintf('Examining output file...\n');

% Load the processed data
load('data/processed/2025-01-27_ProcessedData/FullStroke_Processed_2025-01-27.mat');

fprintf('Loaded combined_data successfully\n');
fprintf('Type: %s\n', class(combined_data));
fprintf('Fields: %s\n', strjoin(fieldnames(combined_data), ', '));

% Check metadata
if isfield(combined_data, 'metadata')
    fprintf('\nMetadata:\n');
    fprintf('  Experiment type: %s\n', combined_data.metadata.experiment_type);
    fprintf('  Total experiments: %d\n', combined_data.metadata.total_experiments);
    fprintf('  From 20-Jan: %d\n', combined_data.metadata.experiments_from_20Jan);
    fprintf('  From 30-Jan: %d\n', combined_data.metadata.experiments_from_30Jan);
end

% Check data structure
fprintf('\nData structure:\n');
fprintf('  Data field type: %s\n', class(combined_data.data));
fprintf('  Data field length: %d\n', length(combined_data.data));

fprintf('  Parameters field type: %s\n', class(combined_data.parameters));
fprintf('  Parameters field length: %d\n', length(combined_data.parameters));

fprintf('  Zeros field type: %s\n', class(combined_data.zeros));
fprintf('  Zeros field length: %d\n', length(combined_data.zeros));

% Check first few experiments
if length(combined_data.parameters) > 0
    fprintf('\nFirst 3 experiments:\n');
    for i = 1:min(3, length(combined_data.parameters))
        if iscell(combined_data.parameters) && length(combined_data.parameters) >= i
            params = combined_data.parameters{i}.parameters;
            fprintf('  Exp %d: Period=%.2f, Yaw=%.0f, Paddle=%.2f, Flow=%.1f, Roll=%.0f\n', ...
                i, params(1), params(2), params(3), params(4), params(5));
        end
    end
end

fprintf('\nExamination complete!\n');
clear

