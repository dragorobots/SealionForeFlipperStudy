% Relocated on 2025-09-09 from config_paths.m to config/config_paths.m as part of repo reorg.

%% Configuration File for Sea Lion Fore Flipper Study
% Edit this file to set your specific data paths

function config = config_paths()
    % ========================================
    % EDIT THESE PATHS FOR YOUR SYSTEM
    % ========================================
    
    % Base directory containing all experimental data
    % This should point to your Dropbox folder
    config.data_base_dir = 'C:\Users\andyc\Dropbox\36 Sea Lion AUV\Sealion_FlowTank\2022_10_06_Experiments_Folder';
    
    % Arduino COM ports (adjust as needed)
    config.arduino_sealion_port = 'COM13';  % Port for Sea Lion robot
    config.arduino_flowtank_port = 'COM8';  % Port for flow tank control
    
    % Data acquisition settings
    config.sampling_rate = 500;  % Hz
    config.recording_duration = 30;  % seconds
    
    % Flow tank settings
    config.flow_speeds = [0, 0.05, 0.1];  % m/s
    config.motor_power_range = [0, 100];  % percentage
    
    % Flipper control settings
    config.num_points = 200;  % Number of trajectory points
    config.period_range = [1.75, 2.25];  % seconds
    
    % Analysis settings
    config.filter_cutoff = 4;  % Hz
    config.zero_duration = 6;  % seconds for zero measurement
    
    % ========================================
    % DO NOT EDIT BELOW THIS LINE
    % ========================================
    
    % Validate that the data directory exists
    if ~exist(config.data_base_dir, 'dir')
        warning('Data directory not found: %s', config.data_base_dir);
        warning('Please update config_paths.m with the correct path to your data files.');
    end
    
    % Display configuration
    fprintf('Sea Lion Fore Flipper Study Configuration:\n');
    fprintf('Data directory: %s\n', config.data_base_dir);
    fprintf('Sea Lion Arduino port: %s\n', config.arduino_sealion_port);
    fprintf('Flow tank Arduino port: %s\n', config.arduino_flowtank_port);
    fprintf('Sampling rate: %d Hz\n', config.sampling_rate);
    fprintf('Flow speeds: %s m/s\n', mat2str(config.flow_speeds));
end

