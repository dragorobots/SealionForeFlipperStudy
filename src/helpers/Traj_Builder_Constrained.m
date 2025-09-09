% Relocated on 2025-09-09 from Traj_Builder_Constrained.m to src/helpers/Traj_Builder_Constrained.m as part of repo reorg.

function [pitch,yaw,roll,TS]=Traj_Builder_Constrained(Action,Num_Pts)

% Build Trajectory
Period=Action(1)+1.75; %1.75 2.75
graphs=0;

% Pitch Settings
p_amp=Action(2)*89+1; %1-90
pitch_power_start=Action(3)*.35+0.05; %0.05-0.4
pitch_power_end=Action(4)*.4+.4; %.4-.8
pitch_return1=Action(5)*.1+.8; %.8-.9
pitch_return2=Action(6)*.09+.9; %.9-.99
pitch_start_pos=Action(7)*.9; % 0-.9

% Yaw Settings
y_amp=-(Action(8)*100+20); % Needs to be negative
yaw1=Action(9)*.3+.1;
yaw2=Action(10)*.3+.45;
yaw_start=Action(11)*.9;

% Roll Settings
recovery_roll=-Action(12)*90;%-90-0
roll_pow_ang=-Action(13)*90; %-90-0
roll_paddle_ang=-Action(14)*90; %-90-0
roll_power_start=Action(15)*.35+.05; %.05-.4
roll_power_end=Action(16)*.4+.4; %.4-.8
roll_paddle=roll_power_end+.05;

% Produce Trajectories
[pitch,yaw,roll,TS]=flipper_trajs_constrained(Num_Pts,Period, ...
    p_amp,y_amp,recovery_roll, roll_pow_ang, roll_paddle_ang, ...
    pitch_power_start, pitch_power_end, pitch_return1, pitch_return2,...
    pitch_start_pos, yaw1, yaw2,yaw_start, roll_power_start, ...
    roll_power_end, roll_paddle, graphs);
end

