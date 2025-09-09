%% --------------------------Paddle Stroke -------------------------
%% Reset the Workspace
clear all
clc
close all


%% Intialize the Daq
s = daq('ni');  % Create a DAQ session for an NI device
s.Rate = 250;   % Set the sampling rate (Hz)

addinput(s,"Dev1",'ai0','Voltage');
addinput(s,"Dev1",'ai2','Voltage');
addinput(s,"Dev1",'ai4','Voltage');
%% Initialize Webcam
frame_rate=30;
time=5;
num_frames=5*frame_rate;

vid = videoinput('winvideo',1);
set(vid, 'FramesPerTrigger', Inf);
set(vid, 'ReturnedColorspace', 'rgb');
vid.FrameGrabInterval = 1;
disp('Webcam Connected')

%% Create the Trajectory
period_settings=[1.75,2.25];
y_amp_settings=[-60 -75 -90];
roll_pow_ang_settings=[-90,-75,-60,-45,-30,-15, 0];
Flow_Speed_settings=[0,70];

total_exps=length(period_settings)*length(y_amp_settings)*length(roll_pow_ang_settings)*length(Flow_Speed_settings);
estimated_time=((total_exps*90)/60)/60;


%% Results Set up

results.experiment_type='Paddle Stroke Study';
results.fin_type='Stiff Fin v1';
results.period_settings=period_settings;
results.y_amp_settings=y_amp_settings;
results.roll_pow_ang_settings=roll_pow_ang_settings;
results.Flow_Speed_settings=Flow_Speed_settings;
results.date=date;
results.sensor_order={'Lateral on ai0','Thrust on ai2','Arduino on ai4'};
results.param_names=['Period','Yaw amplitude','Roll angle','Motor power %'];

%%
for motor_power=Flow_Speed_settings
    clear Ard_FT
    z=1;
    Ard_FT=Arduino_Activator('COM8');
    disp('Flow Tank Ard Connected...')

    disp("Synching Matlab with Flow tank...")
    pause(30); % Needs long pause
    % shake 1
    Arduino_Handshake(Ard_FT)
    writeline(Ard_FT,num2str(motor_power));
    disp(readline(Ard_FT))
    pause(.001);
    disp("Flow Circulating...")

    for Period=period_settings
        for y_amp=y_amp_settings
            for roll_pow_ang=roll_pow_ang_settings

                tic;
                %% Initialize the Arduino
                clear Ard_SL
                Ard_SL=Arduino_Activator('COM11');
                disp('Robot Ard Connected...')

                Num_Pts=200;

                % Pitch Settings
                p_amp=82;
                pitch_power_start=.4;
                pitch_power_end=.6;
                pitch_return1=.8;
                pitch_return2=.9;

                % Yaw Settings
                yaw1=.4;
                yaw2=.6;

                % Raw Settings
                recovery_roll=-90;
                roll_paddle_ang=0;
                roll_power_start=.4;
                roll_power_end=.6;
                roll_paddle=.65;


                % 1 means yes to graphs
                % 0 means no to graphs
                graphs=1;


                [pitch,yaw,roll,TS]=flipper_trajs_simulation_2(Num_Pts,Period, ...
                    p_amp,y_amp,recovery_roll, roll_pow_ang, roll_paddle_ang, ...
                    pitch_power_start, pitch_power_end, pitch_return1, pitch_return2, ...
                    yaw1, yaw2, roll_power_start, roll_power_end, roll_paddle, ...
                    graphs);

                % adjust pitch yaw and roll for motors

                pitch=pitch*.9;
                yaw=yaw*.9;
                roll=roll*.9;

                %% Separtating Paddle Stroke and creating return

                clear pitch_pow yaw_pow roll_pow
                pitch_pow=  pitch(Num_Pts*pitch_power_end:Num_Pts*pitch_return2);
                yaw_pow  =  yaw(Num_Pts*pitch_power_end:Num_Pts*pitch_return2);
                roll_pow =  roll(Num_Pts*pitch_power_end:Num_Pts*pitch_return2);

                pow_leng=length(pitch_pow);
                pitch_return=[linspace(min(pitch_pow),min(pitch_pow),100),...
                    linspace(min(pitch_pow),max(pitch_pow),100),...
                    linspace(max(pitch_pow),max(pitch_pow),200-length(pitch_pow))];
                pitch_pow=[pitch_pow,pitch_return];
     
                yaw_return=[linspace(max(yaw_pow),max(yaw_pow),100),...
                    linspace(max(yaw_pow),min(yaw_pow),100),...
                    linspace(min(yaw_pow), min(yaw_pow),200-length(yaw_pow))];
                yaw_pow=[yaw_pow,yaw_return];


                if max(abs(roll_pow))>90
                    roll_return=linspace(min(roll_pow),max(roll_pow),100);
                    roll_return=[linspace(min(roll_pow),min(roll_pow),100)...
                        roll_return,...
                        linspace(max(roll_pow),max(roll_pow),200-length(roll_pow))];
                end

                if max(abs(roll_pow))<=90
                    roll_return=linspace(max(roll_pow),min(roll_pow),100);
                    roll_return=[linspace(max(roll_pow),max(roll_pow),100)...
                        roll_return,...
                        linspace(min(roll_pow),min(roll_pow),200-length(roll_pow))];
                end

                roll_pow=[roll_pow,roll_return];
%                 figure
%                 subplot(1,3,1)
%                 plot(pitch_pow)
% 
%                 subplot(1,3,2)
%                 plot(yaw_pow)
%                 
%                 subplot(1,3,3)
%                 plot(roll_pow)
                %% Upload Trajectory and Parameters to Arduino
                Num_Pts=length(roll_pow);
                pause(12);
                % shake 1
                Arduino_Handshake(Ard_SL)
                writeline(Ard_SL,num2str(Num_Pts));
                disp(readline(Ard_SL))
                pause(.001);

                % shake 1.5
                Arduino_Handshake(Ard_SL)
                writeline(Ard_SL,num2str(round(pow_leng*1.25)));
                disp(readline(Ard_SL))
                pause(.001);

                % shake 2
                Arduino_Handshake(Ard_SL)
                writeline(Ard_SL,num2str(TS));
                disp(readline(Ard_SL))
                pause(.001);

                % shake 3
                Arduino_Handshake(Ard_SL)
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

                %% Get Zero Data Time
                % shake 6
                Arduino_Handshake(Ard_SL)

                zeros = read(s, seconds(6), "OutputFormat", "Matrix");

                %% The Main Operating Loop

                % Shake 7
                Arduino_Handshake(Ard_SL)
                disp("Currently Conducting an experiment")
                disp("------------------------------------")
                disp(['Current Flow at',' ',num2str(motor_power)])
                disp(strcat("Period =", num2str(Period)))
                disp(strcat("Yaw =", num2str(y_amp)))
                disp(strcat("Roll =", num2str(roll_pow_ang)))
                disp([num2str(z) ' ' 'out of' ' ' num2str(total_exps) ' ' 'Experiments'])
                disp("------------------------------------")

                %% Record video at start of trial
                start(vid);
                tic;
                for iFrame = 1:num_frames
                    loop_start=toc;
                    loop_time=0;
                    I(iFrame)=im2frame(getsnapshot(vid));

                    while loop_time<=1/frame_rate
                        loop_time=toc-loop_start;
                        pause(.000001)
                    end

                    frame_leng(iFrame)=toc-loop_start;
                end
                elapsedTime = toc;
                timePerFrame = elapsedTime/num_frames;
                effectiveFrameRate = 1/timePerFrame;
                stop(vid);

                video.frames=I;
                video.fps=effectiveFrameRate;

                %% Collect data in trial
                data = read(s, seconds(30), "OutputFormat", "Matrix");

                %% Save off recorded data
                results(z).exp_num=z;
                results(z).zeros=zeros;
                results(z).data=data;
                videos(z).video=video;
                results(z).parameters=[Period,y_amp,roll_pow_ang,motor_power];

                z=z+1;

                toc
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

            end
        end
    end


    %%
    d=date;

    directory_name=strcat(d,"_Power_Stroke_Flipper_Results");
    if ~exist(directory_name, 'dir')
        mkdir(directory_name)
    end

    save(strcat(directory_name,"\",date,"_results_PaddleStroke.mat"),'results','-v7.3')
    save(strcat(directory_name,"\",date,"_videos_PaddleStroke.mat"),'videos','-v7.3')

end

%%
clear Ard_FT
Ard_FT=Arduino_Activator('COM8');

disp("Syncing with matlab to power down tank...")
pause(30);
% shake 1
Arduino_Handshake(Ard_FT)
writeline(Ard_FT,num2str(0));
disp(readline(Ard_FT));
pause(.001);
disp("Flow Stopped")
clear Ard_FT Ard_SL


