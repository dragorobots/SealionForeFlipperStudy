clear
clc
close all
addpath('14-Oct-2022_Power_Stroke_Flipper_Results\')
load("14-Oct-2022_results_PowerStroke.mat")
results_1=results;
addpath('07-Oct-2022_Power_Stroke_Flipper_Results\')
load("07-Oct-2022_results_PowerStroke.mat")
results_2=results;

period=[1.75,2.25];
y_amp=[-60, -75, -90]*-1;
roll_pow_ang=[-90,-75,-60,-55,-50,-45,-40,-35,-30,-15,0]*-1;
%roll_pow_ang_settings=[0];
Flow_Speed=[0,28,70];
%%
% Loop order Flow, Speed, Yaw, Roll

num_experiments=length(results_1.data)+length(results_2.data);
force_scale=2.22;
j=1;
for i=67:num_experiments
    if i <= length(results_1.data)
        zeros=results_1.zeros(i).zeros;
        data=results_1.data(i).data;

        filtered_data=Data_Filters(data);
        zeroed_data=filtered_data-mean(zeros(500:1000,:));
        thr(j,:)=zeroed_data(:,1)*force_scale;
        lift1(j,:)=zeroed_data(:,2)*force_scale;
        ard(j,:)=filtered_data(:,3);
        params(j,:)=abs(results_1.parameters(i).parameters);

    else
        i=i-length(results_1.data);
        zeros=results_2.zeros(i).zeros;
        data=results_2.data(i).data;
        filtered_data=Data_Filters(data);
        zeroed_data=filtered_data-mean(zeros(500:1000,:));
        thr(j,:)=zeroed_data(:,1)*force_scale;
        lift1(j,:)=zeroed_data(:,2)*force_scale;
        ard(j,:)=data(:,3);
        params(j,:)=abs(results_2.parameters(i).parameters);
    end
    j=j+1;
end

num_experiments=length(params);



%% Fix arduino signal by bounding it

for i=1:num_experiments
    for j=1:length(ard)
        if ard(i,j)<2
            ard(i,j)=1.5;
        end
        if ard(i,j) >= 2
            ard(i,j)=10;
        end

    end

end


%% Align Traces
first_skip=700;
for k=1:66
    j=1;
    zz=1;

    mat=ard(k,:);
    for i=first_skip:length(mat)-1
        p1=mat(i);
        p2=mat(i+1);
        if j==1
            if abs(p1-p2)>8
                true_index(k,j)=i;
                j=j+1;
            end
        else
            if abs(p1-p2)>8 && abs(true_index(k,j-1)-i) > 5
                true_index(k,j)=i;
                j=j+1;
            end

        end


    end

end


for k=67:num_experiments
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

%%
set=1;
set_length=length(roll_pow_ang);
extra_points2=40;
jj=1;
for a=Flow_Speed
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
                        trace_length=trace_length-extra_points+extra_points2;
                        thrust(z)=mean(thr(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                    else
                        thrust(z)=mean(thr(i,true_index(i,j):(true_index(i,j)+trace_length-1)));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        % hold on
                        % plot(traces_thr(z,:))
                        % hold off
                    end
                    z=z+1;
                end
                mean_thr_struct(jj,ii).period=mean(thrust);
                std_error_thr_struct(jj,ii).period=std(thrust);
                mean_traces_thr(jj,ii).period=mean(traces_thr);
                std_traces_thr(jj,ii).period=std(traces_thr)/sqrt(4);

                mean_lift_struct(jj,ii).period=mean(lift2);
                std_error_lift_struct(jj,ii).period=std(lift2);
                mean_traces_lift(jj,ii).period=mean(traces_lift);
                std_traces_lift(jj,ii).period=std(traces_lift)/sqrt(4);

                ii=ii+1;

            end

            % figure
            % plot(roll_pow_ang,[mean_lift_struct(jj,:).period])
            jj=jj+1;
            set=set+set_length;
        end

    end


end

%% unpack structs
z=1;
for j=1:18
    for i=1:11
        mean_thrust(j,i)=mean_thr_struct(j,i).period;
        std_thrust(j,i)=std_error_thr_struct(j,i).period;

        thr_traces(j,i)=mean_traces_thr(j,i);
        thr_traces_std(z)=std_traces_thr(j,i);

        mean_lift(j,i)=mean_lift_struct(j,i).period;
        std_lift(z)=std_error_lift_struct(j,i).period;
        lift_traces(j,i)=mean_traces_lift(j,i);
        lift_traces_std(z)=std_traces_lift(j,i);
        z=z+1;
    end
    parameters(j,:)=params(i*j,:);
end

%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%**************************************************************************
%% Plot Trace Comparison for Roll Angle
% Params index 155-165 or z=15 i=1:11
% Fast speed, 90 degree yaw, fast flow speed

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


center_index_A=15;
center_index_B=6;

LW=2;
LW_center=3;

leng=220;
height=400;
index=[1,2,3,6,9,10,11];
z=15;
f1=figure('Renderer', 'painters', 'Position', [10 10 leng height]);

j=1;
for i=flip(index)
    subplot(2,1,1)
    hold on
    period=length(thr_traces(z,i).period)/250;
    x=linspace(0,period,length(thr_traces(z,i).period));
    plot(x,thr_traces(z,i).period,'color',colors{j},'LineWidth',LW)
    %yline(mean(thr_traces(z,i).period),'--','color',colors{j},'LineWidth',2)
    roll_mean_thr(j)=mean(thr_traces(z,i).period);

    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})

    j=j+1;
end


subplot(2,1,1)
plot(x,thr_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


j=1;
for i=flip(index)
    subplot(2,1,2)

    hold on

    period=length(lift_traces(z,i).period)/250;
    x=linspace(0,period,length(lift_traces(z,i).period));
    plot(x,lift_traces(z,i).period,'color',colors{j},'LineWidth',LW)

    roll_mean_lift(j)=mean(lift_traces(z,i).period);

    [M,I]=max(lift_traces(z,i).period);
    roll_max_lift(j)=M;
    roll_max_lift_ind(j)=x(I)/x(end);


    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})
    j=j+1;
end

subplot(2,1,2)
plot(x,lift_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


% legend(['90' char(176)],['75' char(176)],['60' char(176)],...
%     ['45' char(176)],['30' char(176)],['15' char(176)],...
%     ['0' char(176)])
fontsize(f1, 16, "points")
fontname('Times New Roman')
%% Plot Trace Comparison for Yaw
% Fast speed, 45 degree roll, fast flow speed
i=6;
index=13:15;

j=1;
f2=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
for z=index
    subplot(2,1,1)
    hold on
    period=length(thr_traces(z,i).period)/250;
    x=linspace(0,period,length(thr_traces(z,i).period));
    plot(x,thr_traces(z,i).period,'color',colors{j},'LineWidth',LW)

    mean((lift_traces(z,i).period))
    [M,I]=max(lift_traces(z,i).period);
    yaw_max_lift(j)=M;
    yaw_max_lift_ind(j)=x(I)/x(end);
    
    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})
    j=j+1;

end

subplot(2,1,1)
plot(x,thr_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)
    hold on

    period=length(lift_traces(z,i).period)/250;
    x=linspace(0,period,length(lift_traces(z,i).period));
    plot(x,lift_traces(z,i).period,'color',colors{j},'LineWidth',LW)

    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)

    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})
    j=j+1;
end

subplot(2,1,2)
plot(x,lift_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

% legend(['60' char(176)],['75' char(176)],['90' char(176)])
fontsize(f2, 16, "points")
fontname('Times New Roman')
%% Plot Trace Comparison for Flow Speed
% Fast speed, 45 degree roll, 90 yaw
i=6;
index=[3,9,15];

j=1;
f3=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
for z=index
    subplot(2,1,1)
    hold on
    period=length(thr_traces(z,i).period)/250;
    x=linspace(0,period,length(thr_traces(z,i).period));
    plot(x,thr_traces(z,i).period,'color',colors{j},'LineWidth',LW)
    
    mean(thr_traces(z,i).period);

    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})
    j=j+1;
end


subplot(2,1,1)
plot(x,thr_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)

    hold on

    period=length(lift_traces(z,i).period)/250;
    x=linspace(0,period,length(lift_traces(z,i).period));
    plot(x,lift_traces(z,i).period,'color',colors{j},'LineWidth',LW)

    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)


    mean((lift_traces(z,i).period))
    [M,I]=max(lift_traces(z,i).period);
    fs_max_lift(j)=M;
    fs_max_lift_ind(j)=x(I)/x(end);


    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})
    j=j+1;
end

subplot(2,1,2)
plot(x,lift_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


% legend('0 m/s','0.05 m/s','0.1 m/s')

fontsize(f3, 16, "points")
fontname('Times New Roman')

%% Plot Trace Comparison for flipper speed
% mid flow speed, 45 degree roll, 90 yaw
i=6;
index=flip([15,18]);

j=1;
f4=figure('Renderer', 'painters', 'Position', [10 10 leng height]);
for z=index
    subplot(2,1,1)

    hold on
    period=length(thr_traces(z,i).period)/250;
    x=linspace(0,period,length(thr_traces(z,i).period));
    plot(x,thr_traces(z,i).period,'color',colors{j},'LineWidth',LW)

    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})


    j=j+1;

end

subplot(2,1,1)
plot(x,thr_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off

j=1;
for z=index
    subplot(2,1,2)

    hold on

    period=length(lift_traces(z,i).period)/250;
    x=linspace(0,period,length(lift_traces(z,i).period));
    plot(x,lift_traces(z,i).period,'color',colors{j},'LineWidth',LW)



     mean((lift_traces(z,i).period))
    [M,I]=max(lift_traces(z,i).period);
    freq_max_lift(j)=M;
    freq_max_lift_ind(j)=x(I)/x(end);


    xlim([0 .66])
    ylim([-1 4])
    yticks(-1:1:4)
    xticks(0:.33:.66)
    xticklabels({'0','0.33','0.66'})

    j=j+1;
end

subplot(2,1,2)
plot(x,lift_traces(center_index_A,center_index_B).period,'color',center_color,'LineWidth',LW_center)
hold off


% legend('0.44 Hz','0.57 Hz')
fontsize(f4, 16, "points")
fontname('Times New Roman')


%% 2D Graphs

i=6;
z=15;


lower_bound=-1;
upper_bound=3;
thr_trace_master=thr_traces(z,i).period;
lift_trace_master=lift_traces(z,i).period;


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

yticks(-1:3)
yticklabels({'-1','0','1','2','3'})

xticks(-1:3)
xticklabels({'-1','0','1','2','3'})

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
xlim([0 .7])
yticks(-1:3)
yticklabels({'-1','0','1','2','3'})

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
xlim([0 .7])

yticks(-1:3)
yticklabels({'-1','0','1','2','3'})

xticks([0,.25,.5,.7])
xticklabels({'0','0.25','0.5','0.7'})

title('Lift')
xlabel('Time (s)')
ylabel('Force (N)')


fontsize(f5, 16, "points")
fontname('Times New Roman')

save('Power_Traces','lift_trace_master','thr_trace_master')