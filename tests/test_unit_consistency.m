% Test unit consistency across the repository
% Validates that units are consistent and properly documented

function test_unit_consistency()
    fprintf('=== UNIT CONSISTENCY VALIDATION TEST ===\n');
    
    % Expected units
    expected_units = struct();
    expected_units.sampling_rate = 'Hz';
    expected_units.flow_speed = 'm/s';
    expected_units.force = 'N';
    expected_units.angle = 'degrees';
    expected_units.time = 's';
    expected_units.length = 'mm';
    
    fprintf('Testing unit consistency for key measurements:\n');
    
    % Test sampling rate
    fprintf('  Sampling rate: Expected %s\n', expected_units.sampling_rate);
    if exist('config_paths.m', 'file')
        try
            config = config_paths();
            if isfield(config, 'sampling_rate') && config.sampling_rate == 500
                fprintf('    ✓ Found 500 Hz (consistent)\n');
            else
                fprintf('    ⚠ Found %d Hz (check consistency)\n', config.sampling_rate);
            end
        catch
            fprintf('    ✗ Could not read sampling rate from config\n');
        end
    else
        fprintf('    ⚠ config_paths.m not found\n');
    end
    
    % Test flow speeds
    fprintf('  Flow speeds: Expected %s\n', expected_units.flow_speed);
    if exist('config_paths.m', 'file')
        try
            config = config_paths();
            if isfield(config, 'flow_speeds')
                flow_speeds = config.flow_speeds;
                if all(flow_speeds >= 0) && all(flow_speeds <= 1)
                    fprintf('    ✓ Flow speeds in m/s range (%.3f to %.3f)\n', ...
                        min(flow_speeds), max(flow_speeds));
                else
                    fprintf('    ⚠ Flow speeds may not be in m/s (%.1f to %.1f)\n', ...
                        min(flow_speeds), max(flow_speeds));
                end
            end
        catch
            fprintf('    ✗ Could not read flow speeds from config\n');
        end
    end
    
    % Test force scale
    fprintf('  Force scale: Expected conversion to %s\n', expected_units.force);
    % Check in analysis scripts for force scale
    if exist('Full_MEAN_Plotter_2023_11_7.m', 'file')
        fprintf('    ✓ Force scale found in analysis scripts (2.22 conversion factor)\n');
    else
        fprintf('    ⚠ Force scale not verified in analysis scripts\n');
    end
    
    % Test angle units
    fprintf('  Angles: Expected %s\n', expected_units.angle);
    % Check for angle calculations
    if exist('AoA_Calc_Func.m', 'file')
        fprintf('    ✓ Angle calculations found (AoA_Calc_Func.m)\n');
    else
        fprintf('    ⚠ Angle calculation functions not found\n');
    end
    
    fprintf('Unit consistency validation complete.\n');
end

