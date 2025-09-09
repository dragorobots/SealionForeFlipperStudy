%% Matlab FLipper Test

%% Initialize the Arduino
clear Ard_SL
Ard_SL=Arduino_Activator('COM11');
disp('Robot Ard Connected...')

Num_Pts=200;
Period=1;
y_amp=-90;
roll_paddle_ang=0;

% Pitch Settings
p_amp=82;
pitch_power_start=.4;
pitch_power_end=.6;
pitch_return1=.99;
pitch_return2=.999;


% Yaw Settings
yaw1=.4;
yaw2=.6;

% Raw Settings
recovery_roll=-90;
roll_pow_ang=roll_paddle_ang;
roll_power_start=.4;
roll_power_end=.55;
roll_paddle_end=.99;
roll_paddle=.9;



% 1 means yes to graphs
% 0 means no to graphs
graphs=0;


[pitch,yaw,roll,~,~,~,TS]=flipper_trajs_simulation_2(Num_Pts,Period, ...
    p_amp,y_amp,recovery_roll, roll_pow_ang, roll_paddle_ang, ...
    pitch_power_start, pitch_power_end, pitch_return1, pitch_return2, ...
    yaw1, yaw2, roll_power_start, roll_power_end, roll_paddle_end, ...
    graphs);

% adjust pitch yaw and roll for motors
TS=round(Period*1000000/Num_Pts);
pitch=pitch*.9;
yaw=yaw*.9;
roll=roll*.9;

%% Separtating Paddle Stroke and creating return

clear pitch_pow yaw_pow roll_pow
pitch_pow=  pitch(Num_Pts*pitch_power_end:Num_Pts*roll_paddle_end);
yaw_pow  =  yaw(Num_Pts*pitch_power_end:Num_Pts*roll_paddle_end);
roll_pow =  roll(Num_Pts*pitch_power_end:Num_Pts*roll_paddle_end);

pow_leng=length(pitch_pow);
pitch_return=[linspace(pitch_pow(end),pitch_pow(end),100),...
    linspace(pitch_pow(end),pitch_pow(1),100),...
    linspace(pitch_pow(1),pitch_pow(1),200-length(pitch_pow))];
pitch_pow=[pitch_pow,pitch_return];

yaw_return=[linspace(yaw_pow(end),yaw_pow(end),100),...
    linspace(yaw_pow(end),yaw_pow(1),100),...
    linspace(yaw_pow(1),yaw_pow(1),200-length(yaw_pow))];
yaw_pow=[yaw_pow,yaw_return];


roll_return=[linspace(roll_pow(end),roll_pow(end),100),...
    linspace(roll_pow(end),roll_pow(1),100),...
    linspace(roll_pow(1),roll_pow(1),200-length(roll_pow))];
roll_pow=-[roll_pow,roll_return];

figure
subplot(1,3,1)
plot(pitch_pow)

subplot(1,3,2)
plot(yaw_pow)

subplot(1,3,3)
plot(roll_pow)
%%
figure('Renderer', 'painters', 'Position', [1200 600 600 300])
subplot(1,3,1)
plot(pitch_pow)
title('Pitch')

subplot(1,3,2)
plot(yaw_pow)
title('Yaw')

subplot(1,3,3)
plot(roll_pow)
title('Roll')

%% Upload Trajectory and Parameters to Arduino
Num_Pts=length(roll_pow);
pause(12);
% shake 1
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(Num_Pts));
disp(readline(Ard_SL))
pause(1);

% shake 1.5
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(round(pow_leng*1.25)));
disp(readline(Ard_SL))
pause(1);

% shake 2
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(TS));
disp(readline(Ard_SL))
pause(1);

% shake 3
Arduino_Handshake(Ard_SL)
pause(.001);
callback_pitch=linspace(777,777,Num_Pts);
disp('uploading pitch...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(pitch_pow(i))));
    callback_pitch(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_pitch(i)))
    pause(.001);
end

% shake 4
Arduino_Handshake(Ard_SL)
callback_yaw=linspace(777,777,Num_Pts);
disp('uploading yaw...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(yaw_pow(i))));
    callback_yaw(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_yaw(i)))
    pause(.001);
end

% shake 5
Arduino_Handshake(Ard_SL)
callback_roll=linspace(777,777,Num_Pts);
disp('uploading roll...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(roll_pow(i))));
    callback_roll(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_roll(i)))
    pause(.001);
end

figure('Renderer', 'painters', 'Position', [1200 100 600 300])
subplot(1,3,1)
plot(callback_pitch)
title("Callback Pitch")

subplot(1,3,2)
plot(callback_yaw)
title("Callback Yaw")

subplot(1,3,3)
plot(callback_roll)
title("Callback Roll")

disp("Uploaded Experiment Data to Arduino")
disp("-----------------------------------")

%% Get Zero Data Time
% shake 6
Arduino_Handshake(Ard_SL)
pause(6);
%% The Main Operating Loop

% Shake 7
Arduino_Handshake(Ard_SL)
disp("Currently Conducting an experiment")
disp("------------------------------------")

disp("------------------------------------")



%% Collect data in trial
pause(30);
