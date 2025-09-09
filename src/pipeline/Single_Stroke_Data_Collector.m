%% Reset the Workspace
clear all
clc
close all


%% Intialize the Daq
s = daq('ni');  % Create a DAQ session for an NI device
s.Rate = 500;   % Set the sampling rate (Hz)

% Set recording channels
addinput(s,"Dev1",'ai0','Voltage');
addinput(s,"Dev1",'ai2','Voltage');
addinput(s,"Dev1",'ai4','Voltage');
%% Initialize Webcam
frame_rate=30;
time=5;
num_frames=5*frame_rate;

% vid = videoinput('winvideo',1);
% set(vid, 'FramesPerTrigger', Inf);
% set(vid, 'ReturnedColorspace', 'rgb');
% vid.FrameGrabInterval = 1;
% disp('Webcam Connected')
%% Set up Flow Speed Calibration
load('Flow_Speed_10-100_10032022_NoScreens.mat')
X=linspace(0,100,11);
f=polyfit(V,X,2);

%% Experimental parameters


%% Results Set up
trial_name='Learned Stroke 02/23/2023';

results.experiment_type=trial_name;
results.fin_type='Stiff Fin v1';
results.date=date;
results.sensor_order={'Lateral on ai0','Thrust on ai2','Arduino on ai4'};
results.param_names=['Period','Yaw amplitude','Roll angle','Motor power percent'];

%%
% clear Ard_FT
% z=1;
% Flow_Speed=0;
% motor_power=round(polyval(f,Flow_Speed));
% % Connect Flow Tank Motors
% Ard_FT=Arduino_Activator('COM8');
% disp('Flow Tank Ard Connected...')
% 
% disp("Synching Matlab with Flow tank...")
% pause(30); % Needs long pause for motors to initialize the first time
% 
% % shake with flow arduino
% Arduino_Handshake(Ard_FT)
% writeline(Ard_FT,num2str(motor_power));
% disp(readline(Ard_FT))
% pause(.1);
% 
% Arduino_Handshake(Ard_FT)
% disp("Flow Circulating...")
% 
% tic;
% Initialize the sealion motors
clear Ard_SL
Ard_SL=Arduino_Activator('COM13');
disp('Robot Ard Connected...')

%% Trajectory Setup
Num_Pts=200;

%%
load('LR_15-Feb-2023_ExNum_1.mat')

[M,I]=maxk(Results.Reward,1);

[pitch,yaw,roll,TS]=Traj_Builder_Constrained(Results.Action(I,:),Num_Pts);
TS=round(TS*1000000);
% adjust pitch yaw and roll for motors

pitch=pitch*.9;
yaw=yaw*.9;
roll=roll*.9;

%% Full Stroke
% creates stroke with break to allow for pause between
% experiments
clear pitch_pow yaw_pow roll_pow

pow_leng=length(pitch);
pitch_pause=linspace(pitch(end),pitch(end),200);
pitch_pow=[pitch,pitch_pause];

yaw_pause=linspace(yaw(end),yaw(end),200);
yaw_pow=[yaw,yaw_pause];

roll_pause=linspace(roll(end),roll(end),200);
roll_pow=-[roll,roll_pause];
figure
subplot(1,3,1)
plot(pitch_pow)

subplot(1,3,2)
plot(yaw_pow)

subplot(1,3,3)
plot(roll_pow)
%% Upload Trajectory and Parameters to Arduino
Num_Pts=length(roll_pow);
pause(5); % Need this pause to make sure arduino is caught up

% shake 1
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(Num_Pts));
disp(readline(Ard_SL))
pause(.1);

% shake 2
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(round(pow_leng)));
disp(readline(Ard_SL))
pause(.1);

% shake 3
Arduino_Handshake(Ard_SL)
writeline(Ard_SL,num2str(TS));
disp(readline(Ard_SL))
pause(.1);

% shake 4
Arduino_Handshake(Ard_SL)
callback_pitch=linspace(777,777,Num_Pts);
disp('uploading pitch...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(pitch_pow(i))));
    callback_pitch(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_pitch(i)))
    pause(.001);
end

% shake 5
Arduino_Handshake(Ard_SL)
callback_yaw=linspace(777,777,Num_Pts);
disp('uploading yaw...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(yaw_pow(i))));
    callback_yaw(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_yaw(i)))
    pause(.001);
end

% shake 6
Arduino_Handshake(Ard_SL)
callback_roll=linspace(777,777,Num_Pts);
disp('uploading roll...')
for i=1:Num_Pts
    writeline(Ard_SL,num2str(round(roll_pow(i))));
    callback_roll(i)=str2double(readline(Ard_SL));
    %disp(num2str(callback_roll(i)))
    pause(.001);
end

figure
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

%% Get Zero Data
% shake 7
Arduino_Handshake(Ard_SL)
zeros = read(s, seconds(6), "OutputFormat", "Matrix");

%% The Main Operating Loop

% Shake 8
Arduino_Handshake(Ard_SL)
disp("Currently Conducting an experiment")
disp("------------------------------------")
% %disp(['Current Flow at',' ',num2str(motor_power)])
% disp(strcat("Period =", num2str(Period)))
% disp(strcat("Yaw =", num2str(y_amp)))
% disp(strcat("Roll =", num2str(roll_pow_ang)))
% disp([num2str(z) ' ' 'out of' ' ' num2str(total_exps) ' ' 'Experiments'])
% disp("------------------------------------")

%% Record video at start of trial
% start(vid);
% tic;
% for iFrame = 1:num_frames
%     loop_start=toc;
%     loop_time=0;
%     I(iFrame)=im2frame(getsnapshot(vid));
% 
%     while loop_time<=1/frame_rate
%         loop_time=toc-loop_start;
%         pause(.000001)
%     end
% 
%     frame_leng(iFrame)=toc-loop_start;
% end
% elapsedTime = toc;
% timePerFrame = elapsedTime/num_frames;
% effectiveFrameRate = 1/timePerFrame;
% stop(vid);
% 
% video.frames=I;
% video.fps=effectiveFrameRate;

%% Collect data in trial
data = read(s, seconds(30), "OutputFormat", "Matrix");

%% Save off recorded data

results.zeros.zeros=zeros;
results.data.data=data;
%videos(z).video=video;
%results.parameters(z).parameters=[Period,y_amp,roll_pow_ang,yaw_start];

%%

clear Ard
close all

figure
subplot(3,1,1)
plot(data(:,1))
title('LAT')

subplot(3,1,2)
plot(data(:,2))
title('THR')

subplot(3,1,3)
plot(data(:,3))
title('ARD')
toc



%%
d=date;

directory_name=strcat(d,"_Full_Stroke_Flipper_Results");
if ~exist(directory_name, 'dir')
    mkdir(directory_name)
end

save(strcat(directory_name,"\",date,"_results_FullStroke.mat"),'results','-v7.3')
%save(strcat(directory_name,"\",date,"_videos_FullStroke.mat"),'videos','-v7.3')


%%
% clear Ard_FT
% Ard_FT=Arduino_Activator('COM8');
% 
% disp("Syncing with matlab to power down tank...")
% pause(30);
% % shake 1
% Arduino_Handshake(Ard_FT)
% writeline(Ard_FT,num2str(0));
% disp(readline(Ard_FT));
% pause(.001);
% disp("Flow Stopped")
% clear Ard_FT Ard_SL
