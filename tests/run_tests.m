% Test runner for Sea Lion Fore Flipper Study
% Run this script to execute all tests

function run_tests()
    fprintf('=== RUNNING SEA LION FOREFLIPPER TESTS ===\n');
    
    % Test 1: Stroke segmentation validation
    test_stroke_segmentation();
    
    % Test 2: Unit consistency
    test_unit_consistency();
    
    % Test 3: Import functionality
    test_import_functionality();
    
    % Test 4: Data structure validation
    test_data_structure();
    
    fprintf('\nAll tests completed.\n');
end

function test_stroke_segmentation()
    fprintf('Testing stroke segmentation...\n');
    
    % Load a sample dataset
    try
        if exist('Standardized_Data_Sets/FullStroke_Standardized.mat', 'file')
            load('Standardized_Data_Sets/FullStroke_Standardized.mat');
            
            % Check that we have stroke data
            if isfield(FullStroke_Standardized, 'data') && ~isempty(FullStroke_Standardized.data)
                fprintf('  ✓ Stroke data loaded successfully\n');
                
                % Check for consistent timing
                if isfield(FullStroke_Standardized, 'period_settings')
                    periods = FullStroke_Standardized.period_settings;
                    if length(periods) >= 2 && all(periods > 0)
                        fprintf('  ✓ Stroke periods are consistent (%.2f, %.2f s)\n', periods(1), periods(2));
                    else
                        fprintf('  ⚠ Warning: Stroke periods may be inconsistent\n');
                    end
                end
            else
                fprintf('  ✗ Error: No stroke data found\n');
            end
        else
            fprintf('  ⚠ Warning: Standardized dataset not found, skipping segmentation test\n');
        end
    catch ME
        fprintf('  ✗ Error in stroke segmentation test: %s\n', ME.message);
    end
end

function test_unit_consistency()
    fprintf('Testing unit consistency...\n');
    
    % Check configuration files for unit declarations
    try
        if exist('config_paths.m', 'file')
            config = config_paths();
            
            % Check sampling rate
            if isfield(config, 'sampling_rate') && config.sampling_rate == 500
                fprintf('  ✓ Sampling rate consistent (500 Hz)\n');
            else
                fprintf('  ⚠ Warning: Sampling rate may be inconsistent\n');
            end
            
            % Check flow speeds
            if isfield(config, 'flow_speeds')
                flow_speeds = config.flow_speeds;
                if all(flow_speeds >= 0) && all(flow_speeds <= 1)
                    fprintf('  ✓ Flow speeds in reasonable range (m/s)\n');
                else
                    fprintf('  ⚠ Warning: Flow speeds may have unit issues\n');
                end
            end
        else
            fprintf('  ⚠ Warning: config_paths.m not found, skipping unit test\n');
        end
    catch ME
        fprintf('  ✗ Error in unit consistency test: %s\n', ME.message);
    end
end

function test_import_functionality()
    fprintf('Testing import functionality...\n');
    
    % Test key function imports
    functions_to_test = {
        'AoA_Calc_Func',
        'Data_Filters_Full', 
        'shadedErrorBar',
        'flipper_trajs'
    };
    
    for i = 1:length(functions_to_test)
        func_name = functions_to_test{i};
        if exist([func_name '.m'], 'file')
            fprintf('  ✓ %s.m found\n', func_name);
        else
            fprintf('  ✗ %s.m not found\n', func_name);
        end
    end
end

function test_data_structure()
    fprintf('Testing data structure validation...\n');
    
    % Test data structure analyzer
    try
        if exist('Data_Struct_Analyzer.m', 'file')
            fprintf('  ✓ Data_Struct_Analyzer.m available\n');
            
            % Check if we can run it (without actually running to avoid output)
            fprintf('  ✓ Data structure validation tools available\n');
        else
            fprintf('  ⚠ Warning: Data_Struct_Analyzer.m not found\n');
        end
        
        % Check for required data directories
        required_dirs = {
            'Master_Data_Set_Backup',
            'Standardized_Data_Sets',
            'Raw_Experimental_Data'
        };
        
        for i = 1:length(required_dirs)
            dir_name = required_dirs{i};
            if exist(dir_name, 'dir')
                fprintf('  ✓ %s directory found\n', dir_name);
            else
                fprintf('  ✗ %s directory missing\n', dir_name);
            end
        end
        
    catch ME
        fprintf('  ✗ Error in data structure test: %s\n', ME.message);
    end
end

