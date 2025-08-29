%% Flow Test

clear all
clc

motor_power=28;    
Ard_FT=Arduino_Activator('COM8');
disp('Flow Tank Ard Connected...')

disp("Synching Matlab with Flow tank...")
pause(45); % Needs long pause

% shake 1
Arduino_Handshake(Ard_FT)
writeline(Ard_FT,num2str(motor_power));
disp(readline(Ard_FT))
pause(1);
Arduino_Handshake(Ard_FT)
pause(.1);
disp("Flow Circulating...")