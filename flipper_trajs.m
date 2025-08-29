function  [pitch,yaw,roll,TS]=flipper_trajs(Num_Pts,Period,p_amp,p_p1,p_p2,...
    y_amp,y_p1,y_p2,r_amp,r_p1,r_p2,...
    roll_pow_timing,roll_pow_ang,...
    graphs)

%% Example inputs

TS=round(Period*1000000/Num_Pts);
%% Pitch

time_pitch=[0    p_p1    p_p2   0.7800    0.9900    1.0000];
pos_pitch=[0 0 1 1 0 0]*p_amp;

xx=linspace(0,1,Num_Pts);
p_p_y = pchip(time_pitch,pos_pitch,xx);
p_p_x=linspace(0,1,length(p_p_y));

%% Yaw
time_yaw=[0*y_p1    0.6042*y_p1    0.8750*y_p1    1.0000*y_p1    y_p2 ...
    y_p2+(1-y_p2)*1/3  y_p2+(1-y_p2)*2/3   1.0000];
pos_yaw=[0    0.3875    0.9000    1.0000    1 ...
    0.2750         0         0]*y_amp;

xx=linspace(0,1,Num_Pts);
y_p_y = pchip(time_yaw,pos_yaw,xx);
y_p_x=linspace(0,1,length(p_p_y));

%% Roll
roll_pow_ang=roll_pow_ang/r_amp;
roll_pow_timing=r_p1+roll_pow_timing;
time_roll=[0    0.5*r_p1     0.7429*r_p1     0.8286*r_p1     1.0000*r_p1 ...
    roll_pow_timing      r_p2  ...
    r_p2+(1-r_p2)*1/3    r_p2+(1-r_p2)*2/3    1.0000];

pos_roll=[0     1   1  1.0000   1.0000   roll_pow_ang  ...
    roll_pow_ang   roll_pow_ang   0   0]*r_amp;

xx=linspace(0,1,Num_Pts);
r_p_y = pchip(time_roll,pos_roll,xx);
r_p_x=linspace(0,1,length(r_p_y));

%% Graphs
if graphs==1
    figure
    hold on
    title("Flipper Pitch")
    plot(time_pitch, pos_pitch,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(p_p_x,p_p_y)
    hold off
    set(gca,'FontSize',16)
    legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')
    
    figure
    hold on
    title("Flipper Yaw")
    plot(time_yaw, pos_yaw,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(y_p_x,y_p_y)
    hold off
    set(gca,'FontSize',16)
    legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')
    
    figure
    hold on
    title('Flipper Roll')
    plot(time_roll, pos_roll,'--o','MarkerSize',10,'MarkerFaceColor','b')
    plot(r_p_x,r_p_y)
    hold off
    set(gca,'FontSize',16)
    legend('Spline Control Points','Splined Trajectory')
    xlabel('Time (s)')
    ylabel('Degrees (^o)')
end

%% Rename vars

pitch=p_p_y*0.9;
yaw=y_p_y*0.9;
roll=r_p_y*0.9;
end
