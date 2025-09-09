function  [pitch,yaw,roll,control_pitch,control_yaw,control_roll,TS]=...
    flipper_trajs_simulation_2(Num_Pts,Period, ...
    p_amp,y_amp,recovery_roll, roll_pow_ang, roll_paddle_ang, ...
    pitch_power_start, pitch_power_end, pitch_return1, pitch_return2, ...
    yaw1, yaw2, roll_power_start, roll_power_end, roll_paddle, ...
    graphs)

%% Example inputs

TS=round(Period*1000000/Num_Pts);
%% Pitch

time_pitch=[0, pitch_power_start, pitch_power_end, pitch_return1, pitch_return2, 1.0000];
pos_pitch=[0 0 1 1 0 0]*p_amp;

control_pitch=[time_pitch;pos_pitch];
xx=linspace(0,1,Num_Pts);
p_p_y = pchip(time_pitch,pos_pitch,xx);
p_p_x=linspace(0,1,length(p_p_y));

%% Yaw
yaw_forward=[0    0.6043    0.8750    1.0000];
time_yaw=[yaw_forward*yaw1   yaw2 yaw2+(1-yaw2)*1/3  yaw2+(1-yaw2)*2/3   1.0000];
pos_yaw=[0, 0.3875, 0.9, 1, 1, 0.275, 0, 0]*y_amp;

control_yaw=[time_yaw;pos_yaw];
xx=linspace(0,1,Num_Pts);
y_p_y = pchip(time_yaw,pos_yaw,xx);
y_p_x=linspace(0,1,length(p_p_y));

%% Roll

initial_roll=[0 0.5 0.7429 0.8286 1];
time_roll=[initial_roll*roll_power_start, roll_power_start+.075,  ...
    roll_power_end, roll_paddle, 1.0000];

pos_roll=[0, recovery_roll, recovery_roll, recovery_roll, recovery_roll, ...
    roll_pow_ang, roll_pow_ang, roll_paddle_ang, 0];

control_roll=[time_roll;pos_roll];
xx=linspace(0,1,Num_Pts);
r_p_y = pchip(time_roll,pos_roll,xx);
r_p_x=linspace(0,1,length(r_p_y));

%% Graphs
if graphs==1
    figure
    subplot(3,1,1)
    hold on
    title("Flipper Pitch")
    plot(time_pitch, pos_pitch,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(p_p_x,p_p_y)
    hold off
    set(gca,'FontSize',16)
    %legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')

    subplot(3,1,2)
    hold on
    title("Flipper Yaw")
    plot(time_yaw, pos_yaw,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(y_p_x,y_p_y)
    hold off
    set(gca,'FontSize',16)
    %legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')

    subplot(3,1,3)
    hold on
    title('Flipper Roll')
    plot(time_roll, pos_roll,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(r_p_x,r_p_y)
    hold off
    set(gca,'FontSize',16)
    %legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')
end

%% Rename vars

pitch=p_p_y;
yaw=y_p_y;
roll=r_p_y;
end
