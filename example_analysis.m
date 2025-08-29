%% Example Analysis Script for Sea Lion Fore Flipper Study
% This script demonstrates how to use the setup_data_paths function
% and run analysis on the experimental data

function example_analysis()
    % Setup data paths first
    setup_data_paths();
    
    % Get global variables
    global SEALION_DATA_BASE_DIR;
    
    fprintf('Running example analysis...\n');
    
    % Example: Load and analyze data from a specific experiment
    try
        % Load data from one of the experiment folders
        data_file = fullfile(SEALION_DATA_BASE_DIR, ...
            '20-Jan-2023_Full_Stroke_Flipper_Results', ...
            '20-Jan-2023_results_FullStroke.mat');
        
        if exist(data_file, 'file')
            fprintf('Loading data from: %s\n', data_file);
            load(data_file);
            
            % Display basic information about the loaded data
            if exist('results', 'var')
                fprintf('Experiment type: %s\n', results.experiment_type);
                fprintf('Date: %s\n', results.date);
                fprintf('Number of experiments: %d\n', length(results.exp_num));
                
                % Example: Plot some basic data
                if isfield(results, 'data') && length(results.data) > 0
                    figure('Name', 'Example Force Data');
                    subplot(2,1,1);
                    plot(results.data(1).data(:,1)); % Thrust data
                    title('Thrust Force (Example)');
                    ylabel('Force (N)');
                    
                    subplot(2,1,2);
                    plot(results.data(1).data(:,2)); % Lift data
                    title('Lift Force (Example)');
                    ylabel('Force (N)');
                    xlabel('Sample Number');
                end
            else
                fprintf('No results structure found in the data file.\n');
            end
        else
            fprintf('Data file not found: %s\n', data_file);
            fprintf('Please check that the data files are in the correct Dropbox location.\n');
        end
        
    catch ME
        fprintf('Error during analysis: %s\n', ME.message);
        fprintf('Make sure the data files are accessible and the paths are correct.\n');
    end
    
    fprintf('\nExample analysis complete!\n');
    fprintf('You can now run more complex analysis scripts like:\n');
    fprintf('- Full_MEAN_Plotter_2023_11_7.m\n');
    fprintf('- Power_MEAN_Plotter_2023_12_19.m\n');
    fprintf('- Paddle_MEAN_Plotter_2023_11_1.m\n');
end
