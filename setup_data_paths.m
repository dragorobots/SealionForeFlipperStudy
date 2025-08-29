%% Setup Data Paths for Sea Lion Fore Flipper Study
% This script sets up the data paths to reference Dropbox data files
% Run this script before running any analysis scripts

function setup_data_paths()
    % Get the current script directory
    script_dir = fileparts(mfilename('fullpath'));
    
    % Define the base data directory (adjust this path as needed)
    % This should point to your Dropbox folder containing the data
    base_data_dir = 'C:\Users\andyc\Dropbox\36 Sea Lion AUV\Sealion_FlowTank\2022_10_06_Experiments_Folder';
    
    % Add the base data directory to MATLAB path
    addpath(base_data_dir);
    
    % Define specific data subdirectories
    data_dirs = {
        '07-Oct-2022_Power_Stroke_Flipper_Results';
        '11-Jan-2023_Full_Stroke_Flipper_Results';
        '14-Oct-2022_Power_Stroke_Flipper_Results';
        '19-Oct-2022_Power_Stroke_Flipper_Results';
        '20-Jan-2023_Full_Stroke_Flipper_Results';
        '23-Feb-2023_Full_Stroke_Flipper_Results';
        '23-Jan-2023_Full_Stroke_Flipper_Results';
        '25-Jan-2023_Full_Stroke_Flipper_Results_BAD_DATA';
        '27-Oct-2022_Power_Stroke_Flipper_Results';
        '30-Jan-2023_Full_Stroke_Flipper_Results';
        'Flipper_Videos';
        'html';
        'Results'
    };
    
    % Add each data directory to the path
    for i = 1:length(data_dirs)
        full_path = fullfile(base_data_dir, data_dirs{i});
        if exist(full_path, 'dir')
            addpath(full_path);
            fprintf('Added to path: %s\n', full_path);
        else
            fprintf('Warning: Directory not found: %s\n', full_path);
        end
    end
    
    % Set global variables for easy access
    global SEALION_DATA_BASE_DIR;
    global SEALION_SCRIPT_DIR;
    
    SEALION_DATA_BASE_DIR = base_data_dir;
    SEALION_SCRIPT_DIR = script_dir;
    
    fprintf('\nData paths setup complete!\n');
    fprintf('Base data directory: %s\n', base_data_dir);
    fprintf('Script directory: %s\n', script_dir);
    fprintf('\nYou can now run analysis scripts that reference data files.\n');
end
