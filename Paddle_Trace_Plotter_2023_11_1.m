clear all
clc
close all
addpath('19-Oct-2022_Power_Stroke_Flipper_Results\')
load("19-Oct-2022_results_PaddleStroke.mat")

%% Paddle Stroke (Extended Yaw Amplitude)


period_settings=[1.75,2.25];
y_amp_settings=-[-60,-75,-90];
roll_paddle_ang_settings=-[-90,-75,-60,-45,-30,-15, 0];
Flow_Speed_settings=[0,70];

% Loop order Flow, Speed, Yaw, Roll
%
num_experiments=length(results);
force_scale=2.22;
for i=1:num_experiments
    % settings(i,:)=results(i).parameters;
    zeros=results(i).zeros;
    data=results(i).data;

    filtered_data=Data_Filters(data);
    zeroed_data=filtered_data-mean(zeros(500:1000,:));
    thr(i,:)=zeroed_data(:,1)*force_scale;
    lift1(i,:)=zeroed_data(:,2)*force_scale;
    ard(i,:)=data(:,3);
    params(i,:)=abs(results(i).parameters);

end

%% Align Traces
first_skip=1;
for k=1:length(results)
    j=1;
    zz=1;

    mat=ard(k,:);
    for i=first_skip:length(mat)-1
        p1=mat(i);
        p2=mat(i+1);
        if abs(p1-p2)>2
            true_index(k,j)=i;
            j=j+1;
        end


    end
end

%% Rename Variables
close all
period=results.period_settings;
y_amp=results.y_amp_settings;
roll_pow_ang=results.roll_pow_ang_settings;
flow_pow=results.Flow_Speed_settings;

%%
set=1;
set_length=length(roll_pow_ang);
extra_points=0;
jj=1;
for a=flow_pow
    for k=period
        for kk=y_amp
            ii=1;

            for i=set:set+set_length-1
                clear traces_thr thrust traces_lift lift2
                z=1;

                for j=1:2:10

                    if j==1
                        trace_length=true_index(i,j+1)-true_index(i,j);
                        extra_points=round(trace_length/5);
                        trace_length=trace_length-extra_points;
                        thrust(z)=mean(thr(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                    else
                        thrust(z)=mean(thr(i,true_index(i,j):(true_index(i,j)+trace_length-1)));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        %                         hold on
                        %                         plot(traces(z,:))
                        %                         hold off
                    end
                    z=z+1;
                end
                mean_thr(jj,ii).period=mean(thrust);
                mean_traces_thr(jj,ii).period=mean(traces_thr);

                mean_lift(jj,ii).period=mean(lift2);
                mean_traces_lift(jj,ii).period=mean(traces_lift);

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

%% unpack structs
for j=1:12
    for i=1:7
        mean_thr_new(j,i)=mean_thr(j,i).period;

        mean_lift_new(j,i)=mean_lift(j,i).period;
    end
    parameters(j,:)=params(i*j,:);
end


%% Plot Trace Comparison for Roll Angle
% Params index 15-21 or z=2 i=1:7
% Fast speed, 90 degree yaw, middle flow speed

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


center_index_A=9;
center_index_B=7;

LW=2;
LW_center=3;


roll_pow_ang=abs(roll_pow_ang);
index=1:7;

leng=220;
height=400;


z=9;
f1=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
j=1;

for i=flip(index)
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_roll(j,:)=[roll_pow_ang(i) M I/length(x) avg];


    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)
    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    ax=gca;
    ax.FontSize=12;

    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


j=1;
for i=flip(index)
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)
    
    [M,I]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_roll(j,:)=[roll_pow_ang(i) M I/length(x) avg];


    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)

    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    ax=gca;
    ax.FontSize=12;
    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


% legend(['90' char(176)],['75' char(176)],['60' char(176)],...
%        ['45' char(176)],['30' char(176)],['15' char(176)],...
%        ['0' char(176)])
fontsize(f1, 14, "points")
fontname('Times New Roman')

%% Plot Trace Comparison for Yaw Angle
% Params index 15-21 or z=2 i=1:7
% Fast speed, 45 degree roll, middle flow speed

i=7;
index=[7,8,9];
f2=figure('Renderer', 'painters', 'Position', [10 10 leng height]);

j=1;
for z=index
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    
    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_yaw(j,:)=[roll_pow_ang(i) M I/length(x) avg];

    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)

    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    j=j+1;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


j=1;
for z=index
    subplot(2,1,2)
    hold on
    period=length(mean_traces_lift(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)
    
    [M,I]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_yaw(j,:)=[roll_pow_ang(i) M I/length(x) avg];

    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)

    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    j=j+1;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off



% legend(['60' char(176)],['75' char(176)],['90' char(176)])
fontsize(f2, 14, "points")
fontname('Times New Roman')
%% Plot Trace Comparison for flow speed
% Params index 15-21 or z=2 i=1:7
% 90 degree yaw, 45 degree roll, fast flipper speed

i=7;
index=[3,9];
f3=figure('Renderer', 'painters', 'Position', [10 10 leng height]);

j=1;
for z=index
    subplot(2,1,1)
    hold on
    period=length(mean_traces_thr(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)

    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_flow(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];

    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)
    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})

    j=j+2;
end

subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off
j=1;
for z=index
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)

[M,I]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_flow(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];





    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)
    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})

    j=j+2;
end

subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

% legend('0 m/s','0.1 m/s')
fontsize(f3, 14, "points")
fontname('Times New Roman')
%% Plot Trace Comparison for flipper speed
% Params index 15-21 or z=2 i=1:7
% 90 degree yaw, 45 degree roll, middle flow speed

i=7;
index=flip([9,12]);
f4=figure('Renderer', 'painters', 'Position', [10 10 leng height]);

j=1;
for z=index
    subplot(2,1,1)

    hold on
    period=length(mean_traces_thr(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_thr(z,i).period));
    plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',LW)
    
    [M,I]=max(mean_traces_thr(z,i).period);
    avg=mean(mean_traces_thr(z,i).period);
    thr_flip(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];


    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)

    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    ax=gca;
    ax.FontSize=12;

    j=j+1;
end

period=length(mean_traces_thr(center_index_A,center_index_B).period)/250;
x=linspace(0,period,length(mean_traces_thr(center_index_A,center_index_B).period));
subplot(2,1,1)
plot(x,mean_traces_thr(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


j=1;
for z=index
    subplot(2,1,2)

    hold on
    period=length(mean_traces_lift(z,i).period)/250;
    x=linspace(0,period,length(mean_traces_lift(z,i).period));
    plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',LW)

[M,I]=min(mean_traces_lift(z,i).period);
    avg=mean(mean_traces_lift(z,i).period);
    lift_flip(j,:)=[roll_pow_ang(i) M I/length(x) avg length(x)];




    xlim([0 .75])
    ylim([-3 4])
    yticks(-2:2:4)

    xticks(0:.25:.75)
    xticklabels({'0','0.25','0.50','0.75'})
    j=j+1;
end

period=length(mean_traces_thr(center_index_A,center_index_B).period)/250;
x=linspace(0,period,length(mean_traces_thr(center_index_A,center_index_B).period));
subplot(2,1,2)
plot(x,mean_traces_lift(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

% legend('0.57 Hz','0.44 Hz')
fontsize(f4, 14, "points")
fontname('Times New Roman')

%% 2D Graphs
i=center_index_B;
z=center_index_A;

lower_bound=-4;
upper_bound=4;
thr_trace_master=mean_traces_thr(z,i).period;
lift_trace_master=mean_traces_lift(z,i).period;


f5=figure('Renderer', 'painters', 'Position', [10 10 400 900]);


subplot(3,1,1)
hold on
plot(thr_trace_master,lift_trace_master,'color',center_color,'LineWidth',LW_center)
quiver(0,0,mean(thr_trace_master),mean(lift_trace_master),'LineWidth',1)
xline(0,'k')
yline(0,'k')

xlim([lower_bound upper_bound])
ylim([lower_bound upper_bound])
hold off

% yticks(-1:3)
% yticklabels({'-1','0','1','2','3'})
% 
% xticks(-1:3)
% xticklabels({'-1','0','1','2','3'})

title('2D Force')
xlabel('Thrust (N)')
ylabel('Lift (N)')







subplot(3,1,2)
hold on
plot(x,thr_trace_master,'color',center_color,'LineWidth',LW_center)
yline(mean(thr_trace_master),'--','color','r','LineWidth',2)
yline(0,'k')

hold off
ylim([lower_bound upper_bound])
xlim([0 max(x)])

xticks([0,.25,.5,.7])
xticklabels({'0','0.25','0.5','0.7'})

title('Thrust')
xlabel('Time (s)')
ylabel('Force (N)')


subplot(3,1,3)
hold on
plot(x,lift_trace_master,'color',center_color,'LineWidth',LW_center)
yline(mean(lift_trace_master),'--','color','r','LineWidth',2)
yline(0,'k')

hold off
ylim([lower_bound upper_bound])
xlim([0 max(x)])

xticks([0,.25,.5,.7])
xticklabels({'0','0.25','0.5','0.7'})

title('Lift')
xlabel('Time (s)')
ylabel('Force (N)')


fontsize(f5, 16, "points")
fontname('Times New Roman')

save('Paddle_Traces','lift_trace_master','thr_trace_master')