clear all
clc
close all
addpath('20-Jan-2023_Full_Stroke_Flipper_Results')
addpath('23-Jan-2023_Full_Stroke_Flipper_Results')
addpath('30-Jan-2023_Full_Stroke_Flipper_Results')
load("20-Jan-2023_results_FullStroke.mat")
results_1=results;
load("23-Jan-2023_results_FullStroke.mat")
results_2=results;
load("30-Jan-2023_results_FullStroke.mat")
results_3=results;
%% Full Stroke

period_settings=[1.75 2.25];
paddle_tran=[.5 .55 .6];
y_amp_settings=-[-70 -80 -90 -100];
roll_pow_ang_settings=-[-90,-75,-60,-45,-30,-15, 0];
Flow_Speed_settings=results.Flow_Speed_settings; %0, 0.05, 0.1
Fs=500;



%% Unload Result Struct
% Loop order Flow, Speed, Yaw, Roll

num_experiments=length(results.exp_num);
for z=1:3
    i1=1;
    for i=(num_experiments*(z-1)+1):num_experiments*z
        if z==1
            results=results_1;
        end
        if z==2
            results=results_2;
        end
        if z==3
            results=results_3;
        end

        % settings(i,:)=results(i).parameters;
        zeros=results.zeros(i1).zeros*2.22; % convert to newtons
        data=results.data(i1).data*2.22; % convert to newtons
        filtered_data=Data_Filters_Full(data);
        zeroed_data=filtered_data-mean(zeros(500:1000,:));
        thr(i,:)=zeroed_data(:,1);
        lift1(i,:)=zeroed_data(:,2);
        ard(i,:)=data(:,3);
        params(i,:)=[abs(results.parameters(i1).parameters), ...
            results.Flow_Speed_settings];
        % figure
        % plot(thr(i,:))

        i1=i1+1;
    end
end


%% Align Traces
first_skip=500;
num_experiments=num_experiments*3;
for k=1:num_experiments
    j=1;
    zz=1;
    on_flag=0;

    mat=ard(k,:);

    % figure
    % plot(ard(k,:))

    for i=first_skip:length(mat)-1
        p1=mat(i);
        p2=mat(i+1);
        if (p1-p2)<-1 && on_flag==0
            true_index(k,j)=i;
            on_flag=1;
            j=j+1;
        end

        if (p1-p2)>1 && on_flag==1
            true_index(k,j)=i;
            on_flag=0;
            j=j+1;
        end
    end
end

%%  Index Set-up
z=1;
true_index=true_index(:,2:11);

j=1;
diff=[];
for i=1:2:10
    diff_1=true_index(:,i)-true_index(:,i+1);
    diff=[diff diff_1];
    j=j+1;
end

for i=1:2:length(true_index(1,:))-1
    for j=1:length(true_index(:,1))
        diff(z)=true_index(j,i)-true_index(j,i+1);
        z=z+1;

    end
end


%% Rename Variables
close all
period=results.period_settings;
y_amp=results.y_amp_settings;
roll_pow_ang=results.roll_pow_ang_settings;
%flow_pow=;

%% Create Means and Layer Traces

set=1;
set_length=length(roll_pow_ang);
extra_points=[-220,-283];
recovery_percent=.3;

%extra_points=-220;
jj=1;

for a=[.1, .05 0]
    kp=0;
    for k=period
        kp=kp+1;
        for aa=paddle_tran
            for kk=y_amp
                ii=1;

                for i=set:set+set_length-1
                    clear traces_thrust_temp mean_thrust_temp traces_lift_temp mean_lift_temp
                    z=1;

                    for j=1:2:10
                        p1=true_index(i,j)+round((true_index(i,j+1)-true_index(i,j))*recovery_percent);
                        p2=true_index(i,j+1)+extra_points(kp);

                        if j==1
                            trace_length=p2-p1;
                            mean_thrust_temp(z)=    mean(thr(i,p1:p2));
                            traces_thrust_temp(z,:)=thr(i,p1:p2);
                            mean_lift_temp(z)=      mean(lift1(i,p1:p2));
                            traces_lift_temp(z,:)=  lift1(i,p1:p2);

                        else
                            mean_thrust_temp(z)=    mean(thr(i,p1:p1+trace_length));
                            traces_thrust_temp(z,:)=thr(i,p1:p1+trace_length);
                            mean_lift_temp(z)=      mean(lift1(i,p1:p1+trace_length));
                            traces_lift_temp(z,:)=  lift1(i,p1:p1+trace_length);

                        end
                        z=z+1;
                    end
                    mean_thr(jj,ii).period=mean(mean_thrust_temp);

                    mean_traces_thr(jj,ii).period=mean(traces_thrust_temp);

                    mean_lift(jj,ii).period=mean(mean_lift_temp);

                    mean_traces_lift(jj,ii).period=mean(traces_lift_temp);

                    ii=ii+1;

                end
                jj=jj+1;
                %         figure
                %         plot(roll_pow_ang,mean_thr)
                %        title(strcat(num2str(kk),'',num2str(k)))
                set=set+set_length;
            end
        end
    end


end

%% Graphs for Roll
% Params index 155-165 or z=15 i=1:11
% Fast speed, 90 degree yaw, fast flow speed, mid-smooth transition

close all
clc

colors={[106,61,154]/255, ...
    [255,127,0]/255, ...
    [166,206,227]/255, ...
    [31,120,180]/255, ...
    [177,89,40]/255, ...
    [251,154,153]/255, ...
    [202,178,214]/255,...
    [115,115,115]/255};

center_color=[51,160,44]/255;


center_index_A=11;
center_index_B=4;

LW=2;
LW_center=3;


roll_pow_ang=abs(roll_pow_ang);
index=1:7;
Thrust_Bounds=[-1.5 4.5];
Lift_Bounds=[-3 4];
leng=200;
height=400;

F_Size=15;


z=11;
f1=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for i=flip(index)
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)

    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_roll(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];

    xlim([0 1.2])
    ylim([Thrust_Bounds(1) Thrust_Bounds(2)])
    yticks(-1.5:1.5:4.5)
    xticks(0:.4:1.2)

    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


j=1;
for i=flip(index)
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)

    
    % [M,I]=max(mean_traces_lift(z,i).period);
    % avg=mean(mean_traces_lift(z,i).period);
    % lift_roll(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];


    [M,I]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_roll_min(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];




    xlim([0 1.2])
    ylim([Lift_Bounds(1) Lift_Bounds(2)])

    xticks(0:.4:1.2)
    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

% legend(['90' char(176)],['75' char(176)],['60' char(176)],...
%         ['45' char(176)],['30' char(176)],['15' char(176)],...
%         ['0' char(176)])
fontsize(f1, F_Size, "points")
fontname('Times New Roman')

%% Graphs for Yaw
% Params index 155-165 or z=15 i=1:11
% Fast speed, 45 degree yaw, fast flow speed, mid-smooth transition

roll_pow_ang=abs(roll_pow_ang);
i=4;
index=[5,6,7]+4;
f2=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for z=index
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    xlim([0 1.2])
    ylim([Thrust_Bounds(1) Thrust_Bounds(2)])

    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_yaw(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];



    yticks(-1.5:1.5:4.5)
    xticks(0:.4:1.2)

    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)

    [Max,I_Max]=max(mean_traces_lift(z,i).period);
    [Min,I_Min]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_yaw(j,:)=[Max I_Max/length(x) Min I_Min/length(x) avg];


    xlim([0 1.2])
    ylim([Lift_Bounds(1) Lift_Bounds(2)])
    xticks(0:.4:1.2)

    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

%legend(['70' char(176)],['80' char(176)],['90' char(176)],['100' char(176)])
fontsize(f2, F_Size, "points")
fontname('Times New Roman')

%% Graphs for flow speed
% Params index 155-165 or z=15 i=1:11
% Fast speed, 90 degree yaw, 45 degree roll, mid-smooth transition

roll_pow_ang=abs(roll_pow_ang);
i=4;
index=flip([6,30,54]+5);
f3=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for z=index
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    xlim([0 1.2])
    ylim([Thrust_Bounds(1) Thrust_Bounds(2)])
    xticks(0:.4:1.2)
    yticks(-1.5:1.5:4.5)

        [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_fs(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];



    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)
    xlim([0 1.2])
    ylim([Lift_Bounds(1) Lift_Bounds(2)])
    xticks(0:.4:1.2)

    
    [Max,I_Max]=max(mean_traces_lift(z,i).period);
    [Min,I_Min]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_yaw(j,:)=[Max I_Max/length(x) Min I_Min/length(x) avg];

    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

%legend('0.1 m/s','0.05 m/s','0 m/s')
fontsize(f3, F_Size, "points")
fontname('Times New Roman')

%% Graphs for flipper speed
% Params index 155-165 or z=15 i=1:11
% Fast speed, 90 degree yaw, 45 degree roll, mid-smooth transition

roll_pow_ang=abs(roll_pow_ang);
i=4;
index=flip([7,19]+4);
f4=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for z=index
    subplot(2,1,1)

    hold on
    period=length(mean_traces_thr(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    xlim([0 1.2])
    ylim([Thrust_Bounds(1) Thrust_Bounds(2)])

    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_flip(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];


    xticks(0:.4:1.2)
    yticks(-1.5:1.5:4.5)

    j=j+1;
end

period=length(mean_traces_thr(center_index_A,center_index_B).period)/500;
x=linspace(0,period,length(mean_traces_thr(center_index_A,center_index_B).period));
subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)
    hold on
    period=length(mean_traces_lift(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)
    xlim([0 1.2])
    ylim([Lift_Bounds(1) Lift_Bounds(2)])
    xticks(0:.4:1.2)


    [Max,I_Max]=max(mean_traces_lift(z,i).period);
    [Min,I_Min]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_yaw(j,:)=[Max I_Max/length(x) Min I_Min/length(x) avg];


    j=j+1;
end
period=length(mean_traces_thr(center_index_A,center_index_B).period)/500;
x=linspace(0,period,length(mean_traces_thr(center_index_A,center_index_B).period));

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

%legend('0.57 Hz','0.44 Hz')
fontsize(f4, F_Size, "points")
fontname('Times New Roman')

%% Graphs for transition
% Fast speed, 90 degree yaw, 45 degree roll, fast flow speed
roll_pow_ang=abs(roll_pow_ang);
i=4;
index=[3,7,11];
f5=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for z=index
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    

    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_trans(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];



    xlim([0 1.2])
    ylim([Thrust_Bounds(1) Thrust_Bounds(2)])
    xticks(0:.4:1.2)
    yticks(-1.5:1.5:4.5)

    mean(mean_traces_thr(z,i).period)

    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/500;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)

    xlim([0 1.2])
    ylim([Lift_Bounds(1) Lift_Bounds(2)])

    xticks(0:.4:1.2)
    

    [Max,I_Max]=max(mean_traces_lift(z,i).period);
    [Min,I_Min]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_yaw(j,:)=[Max I_Max/length(x) Min I_Min/length(x) avg];




    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


%legend('Smooth','Mid-Smooth','Choppy')
fontsize(f5, F_Size, "points")
fontname('Times New Roman')

%% 2D Graphs
i=center_index_B;
z=center_index_A;

Thrust_Bounds=[-3 3];
Lift_Bounds=[-3 3];
thr_trace_master=mean_traces_thr(z,i).period;
lift_trace_master=mean_traces_lift(z,i).period;

f6=figure('Renderer', 'painters', 'Position', [10 10 400 900]);

subplot(3,1,1)
hold on
plot(thr_trace_master,lift_trace_master,'color',center_color,'LineWidth',LW_center)
quiver(0,0,mean(thr_trace_master),mean(lift_trace_master),'LineWidth',1)
xline(0,'k')
yline(0,'k')

xlim(Thrust_Bounds)
ylim(Lift_Bounds)
hold off

title('2D Force')
xlabel('Thrust (N)')
ylabel('Lift (N)')

ylim(Lift_Bounds)
xlim(Thrust_Bounds)
xticks([-3,-1.5,0,1.5,3])
yticks([-3,-1.5,0,1.5,3])



subplot(3,1,2)
hold on
plot(x,thr_trace_master,'color',center_color,'LineWidth',LW_center)
yline(mean(thr_trace_master),'--','color','r','LineWidth',2)
yline(0,'k')

hold off
ylim(Thrust_Bounds)
xlim([0 max(x)])

xticks([0,.25,.5,.75,1])
xticklabels({'0','0.25','0.5','0.75','1'})
yticks([-3,-1.5,0,1.5,3])

xlabel('Time (s)')
ylabel('Force (N)')
title('Thrust')
subplot(3,1,3)
hold on
plot(x,lift_trace_master,'color',center_color,'LineWidth',LW_center)
yline(mean(lift_trace_master),'--','color','r','LineWidth',2)
yline(0,'k')

hold off
ylim(Lift_Bounds)
xlim([0 max(x)])

xticks([0,.25,.5,.75,1])
xticklabels({'0','0.25','0.5','0.75','1'})
yticks([-3,-1.5,0,1.5,3])

xlabel('Time (s)')
ylabel('Force (N)')
title('Lift')

fontsize(f6, 16, "points")
fontname('Times New Roman')

save('Full_Traces','lift_trace_master','thr_trace_master')
