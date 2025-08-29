function [Angle_of_attack, vel_mag]=AoA_Calc_Func(roll_angle,flow_speed,flipper_period)

flipper_length=190.5;

for i =1:length(roll_angle)

Num_Pts=150;
Period=flipper_period;
p_amp=90; p_p1=.4; p_p2=.6;
pow_leng=(p_p2-p_p1)*Num_Pts;
y_amp=-90; y_p1=.3; y_p2=.6;
r_amp=-90; r_p1=.4; r_p2=.6;
roll_pow_timing=.1; roll_pow_ang=roll_angle(i); graphs=0;

[pitch,yaw,roll,TS]=flipper_trajs(Num_Pts,Period,p_amp,p_p1,p_p2,...
    y_amp,y_p1,y_p2,r_amp,r_p1,r_p2,...
    roll_pow_timing,roll_pow_ang,...
    0);

pitch_pow=pitch(length(pitch)*p_p1:length(pitch)*p_p2);
time_step=TS/1000000; diff_pitch=diff(pitch_pow)/time_step;

flipper_speed=(diff_pitch*(pi/180))*flipper_length*(2/3)/1000;
% Flipper Angle

vel_mag=sqrt(mean(flipper_speed)^2 + (flow_speed)^2);
Flipper_Angle=roll_angle(i);


%Combined_Flow_Direction=(atand(mean(flipper_speed)/flow_speed));

Combined_Flow_Direction=(atand(flow_speed/mean(flipper_speed)));


Angle_of_attack(i)=Flipper_Angle-Combined_Flow_Direction;
end
end

% figure
% hold on
% plot(roll_angle,AoA,'o','MarkerFaceColor','b','MarkerSize',10)
% plot(roll_angle,Combined_Flow_Direction,'s','MarkerFaceColor','m','MarkerSize',10)
% plot(roll_angle,roll_angle,'^','MarkerFaceColor','g','MarkerSize',10)
% set(gca,'FontSize',16)
% ylabel('Degrees (^o)')
% xlabel('Flipper Roll Angle')
% legend('AoA','Combined Flow Angle','Flipper Angle')
% grid on
% hold off
%%
% figure
% hold on
%
% x2=0+(1*cosd(-Flipper_Angle));
% y2=0+(1*sind(-Flipper_Angle));
% plot([0 x2],[0 y2],'LineWidth',3)
%
% x3=0+(1*cosd(-Combined_Flow_Direction));
% y3=0+(1*sind(-Combined_Flow_Direction));
% plot([0 x3],[0 y3],'LineWidth',3)
%
% title(['Angle of Attack =',num2str(AoA)])
% xlim([0,1])
% ylim([-1,1])
%
% hold off



