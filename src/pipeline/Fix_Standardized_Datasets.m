% Fix_Standardized_Datasets - Fix issues in standardized datasets
% Corrects yaw amplitudes, roll angles, flow speeds, and data structure issues
% Saves corrected versions to Standardized_Data_Sets folder

clear all
clc
close all

fprintf('=== FIXING STANDARDIZED DATASETS ===\n');
fprintf('Correcting data issues and saving fixed versions...\n\n');

% Add paths
addpath('Standardized_Data_Sets');

%% FIX FULL STROKE DATASET
fprintf('Fixing Full Stroke dataset...\n');
fix_full_stroke();

%% FIX PADDLE STROKE DATASET
fprintf('Fixing Paddle Stroke dataset...\n');
fix_paddle_stroke();

%% FIX POWER STROKE DATASET
fprintf('Fixing Power Stroke dataset...\n');
fix_power_stroke();

fprintf('\nAll datasets fixed and saved!\n');

function fix_full_stroke()
    % Load the original dataset
    load('Standardized_Data_Sets/FullStroke_Standardized.mat');
    
    % Create corrected structure
    FullStroke_Corrected = FullStroke_Standardized;
    
    % Fix Yaw Amplitude: truncate off 100, make entries positive
    FullStroke_Corrected.y_amp_settings = [70 80 90]; % Remove -100, make positive
    
    % Fix Roll Power Angle: make entries positive
    FullStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Make positive
    
    % Fix Flow Speed: order as [0, 0.1] (corresponding to [0, 100])
    FullStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Order: 0 first, then 0.1
    
    % Filter data to only include experiments with yaw 70, 80, 90
    valid_yaw_indices = [];
    for i = 1:length(FullStroke_Corrected.parameters)
        yaw_val = abs(FullStroke_Corrected.parameters(i).parameters(4)); % Yaw is 4th parameter
        if ismember(yaw_val, [70 80 90])
            valid_yaw_indices = [valid_yaw_indices, i];
        end
    end
    
    % Debug: check what yaw values we actually have
    fprintf('    Found yaw values: ');
    for i = 1:min(10, length(FullStroke_Corrected.parameters))
        yaw_val = abs(FullStroke_Corrected.parameters(i).parameters(4));
        fprintf('%.0f ', yaw_val);
    end
    fprintf('\n');
    
    % Keep only valid experiments
    FullStroke_Corrected.data = FullStroke_Corrected.data(valid_yaw_indices);
    FullStroke_Corrected.parameters = FullStroke_Corrected.parameters(valid_yaw_indices);
    FullStroke_Corrected.zeros = FullStroke_Corrected.zeros(valid_yaw_indices);
    
    % Update metadata
    FullStroke_Corrected.total_experiments = length(valid_yaw_indices);
    FullStroke_Corrected.creation_date = datestr(now);
    FullStroke_Corrected.corrections_applied = {'Yaw truncated to [70,80,90]', 'Roll angles made positive', 'Flow speed reordered to [0,0.1]'};
    
    % Save corrected dataset
    save('Standardized_Data_Sets/FullStroke_Corrected.mat', 'FullStroke_Corrected');
    fprintf('  Saved FullStroke_Corrected.mat with %d experiments\n', FullStroke_Corrected.total_experiments);
end

function fix_paddle_stroke()
    % Load the original dataset
    load('Standardized_Data_Sets/PaddleStroke_Standardized.mat');
    
    % Create corrected structure
    PaddleStroke_Corrected = PaddleStroke_Standardized;
    
    % Fix Yaw Amplitude: 60->70, 75->80, 90, make entries positive
    PaddleStroke_Corrected.y_amp_settings = [70 80 90]; % Map: 60->70, 75->80, 90->90
    
    % Fix Roll Power Angle: make entries positive
    PaddleStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Make positive
    
    % Fix Flow Speed: should be [0, 0.1] (corresponding to [0, 100])
    PaddleStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Update to [0, 0.1] m/s
    
    % Fix data structure issues - the data seems to be in wrong format
    % Load original file to get correct structure
    load('Master_Data_Set_Backup/19-Oct-2022_results_PaddleStroke.mat');
    
    % Create properly structured data
    PaddleStroke_Corrected.data = results.data;
    PaddleStroke_Corrected.parameters = results.parameters;
    PaddleStroke_Corrected.zeros = results.zeros;
    
    % Update metadata
    PaddleStroke_Corrected.total_experiments = numel(results.data);
    PaddleStroke_Corrected.creation_date = datestr(now);
    PaddleStroke_Corrected.corrections_applied = {'Yaw mapped: 60->70, 75->80, 90->90', 'Roll angles made positive', 'Flow speed corrected to [0,0.1]', 'Data structure fixed'};
    
    % Save corrected dataset
    save('Standardized_Data_Sets/PaddleStroke_Corrected.mat', 'PaddleStroke_Corrected');
    fprintf('  Saved PaddleStroke_Corrected.mat with %d experiments\n', PaddleStroke_Corrected.total_experiments);
end

function fix_power_stroke()
    % Load the original dataset
    load('Standardized_Data_Sets/PowerStroke_Standardized.mat');
    
    % Create corrected structure
    PowerStroke_Corrected = PowerStroke_Standardized;
    
    % Fix Yaw Amplitude: 60->70, 75->80, 90, make entries positive
    PowerStroke_Corrected.y_amp_settings = [70 80 90]; % Map: 60->70, 75->80, 90->90
    
    % Fix Roll Power Angle: reduce to [-90 -75 -60 -45 -30 -15 0] and make positive
    PowerStroke_Corrected.roll_pow_ang_settings = [90 75 60 45 30 15 0]; % Reduced set, made positive
    
    % Fix Flow Speed: reduce to only [0, 0.1] (corresponding to [0, 100])
    PowerStroke_Corrected.Flow_Speed_settings = [0 0.1]; % Only 0 and 0.1 m/s
    
    % Filter data to only include experiments with correct yaw and flow speed
    valid_indices = [];
    for i = 1:length(PowerStroke_Corrected.parameters)
        yaw_val = abs(PowerStroke_Corrected.parameters(i).parameters(4)); % Yaw is 4th parameter
        flow_val = PowerStroke_Corrected.Flow_Speed_settings(1); % Get flow speed from parameters
        
        % Check if yaw is valid and flow speed is 0 or 100 (0.1 m/s)
        if ismember(yaw_val, [70 80 90]) && (flow_val == 0 || flow_val == 100)
            valid_indices = [valid_indices, i];
        end
    end
    
    % Keep only valid experiments
    PowerStroke_Corrected.data = PowerStroke_Corrected.data(valid_indices);
    PowerStroke_Corrected.parameters = PowerStroke_Corrected.parameters(valid_indices);
    PowerStroke_Corrected.zeros = PowerStroke_Corrected.zeros(valid_indices);
    
    % Update metadata
    PowerStroke_Corrected.total_experiments = length(valid_indices);
    PowerStroke_Corrected.creation_date = datestr(now);
    PowerStroke_Corrected.corrections_applied = {'Yaw mapped: 60->70, 75->80, 90->90', 'Roll angles reduced and made positive', 'Flow speed reduced to [0,0.1]'};
    
    % Save corrected dataset
    save('Standardized_Data_Sets/PowerStroke_Corrected.mat', 'PowerStroke_Corrected');
    fprintf('  Saved PowerStroke_Corrected.mat with %d experiments\n', PowerStroke_Corrected.total_experiments);
end
