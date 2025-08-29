%% Here is the parameters you can change
period_settings=[1.75,2.35];
paddle_tran=[.5 .55 .6];
y_amp_settings=[-70 -80 -90 -100];
roll_pow_ang_settings=[-90,-75,-60,-45,-30,-15, 0];

%% Default Kinematics 
Period=period_settings(1);
yaw_start=paddle_tran(1);
y_amp=y_amp_settings(3);
roll_pow_ang=roll_pow_ang_settings(4);
%%

Num_Pts=200;

% Pitch Settings
p_amp=82;
pitch_power_start=.4;
pitch_power_end=.6;
pitch_return1=.99;
pitch_return2=.999;

% Yaw Settings
yaw1=.4;
yaw2=yaw_start;

% Raw Settings
recovery_roll=-90;
roll_paddle_ang=0;
roll_power_start=.4;
roll_power_end=yaw_start;
roll_paddle=yaw_start+.05;

% 1 means yes to graphs
% 0 means no to graphs
graphs=1;

[pitch,yaw,roll,~,~,~,TS]=flipper_trajs_simulation_2(Num_Pts,Period, ...
    p_amp,y_amp,recovery_roll, roll_pow_ang, roll_paddle_ang, ...
    pitch_power_start, pitch_power_end, pitch_return1, pitch_return2, ...
    yaw1, yaw2, roll_power_start, roll_power_end, roll_paddle, ...
    graphs);
