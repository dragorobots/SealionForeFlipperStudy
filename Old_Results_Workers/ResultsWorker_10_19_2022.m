clear all
clc
close all
addpath('19-Oct-2022_Power_Stroke_Flipper_Results\')
load("19-Oct-2022_results_PaddleStroke.mat")

%% Paddle Stroke (Extended Yaw Amplitude)


period_settings=[1.75,2.25];
y_amp_settings=[-60,-75,-90];
roll_paddle_ang_settings=[-90,-75,-60,-45,-30,-15, 0];
Flow_Speed_settings=[0,70];

% Loop order Flow, Speed, Yaw, Roll

num_experiments=length(results);

for i=1:num_experiments
    % settings(i,:)=results(i).parameters;
    zeros=results(i).zeros;
    data=results(i).data;
    filtered_data=Data_Filters(data);
    zeroed_data=filtered_data-mean(zeros(500:1000,:));
    thr(i,:)=zeroed_data(:,1);
    lift1(i,:)=zeroed_data(:,2);
    ard(i,:)=data(:,3);
    %      figure
    %      hold on
    %     subplot(1,2,1)
    %     plot(thr(i,:))
    %     subplot(1,2,2)
    %     plot(zeros(:,1:2))
    %     hold off
    %
    % figure
    % plot(ard(i,:))
end

%%
% figure
% plot((ard(1,:)),'-x')

%% Align Traces
first_skip=1000;
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
%true_index=true_index(:,1:10);

%%


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
                std_error_thr(jj,ii).period=std(thrust);
                mean_traces_thr(jj,ii).period=mean(traces_thr);
                std_traces_thr(jj,ii).period=std(traces_thr)/sqrt(4);

                mean_lift(jj,ii).period=mean(lift2);
                std_error_lift(jj,ii).period=std(lift2);
                mean_traces_lift(jj,ii).period=mean(traces_lift);
                std_traces_lift(jj,ii).period=std(traces_lift)/sqrt(4);

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
for i=1:7
    for j=1:12
        mean_thr_new(j,i)=mean_thr(j,i).period;
        std_error_new_thr(j,i)=std_error_thr(j,i).period;

        mean_lift_new(j,i)=mean_lift(j,i).period;
        std_error_new_lift(j,i)=std_error_lift(j,i).period;
    end
end

%% Roll Angle
c1=[228,26,28]/255;
c2=[55,126,184]/255;
c3=[77,175,74]/255;
colors=[c1;c2;c3];
figure('Renderer', 'painters', 'Position', [10 510 900 450])

for i=1:3

    subplot(2,2,1)
    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i,:),'Color',colors(i,:),'LineWidth',2)
    title('Thrust: Fast Flap Speed (1.75 s)')
    ylim([0 .9])


    subplot(2,2,2, 'NextPlot','add')
    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i,:),'Color',colors(i,:),'LineWidth',2)
    title('Lift: Fast Flap Speed (1.75 s)')
    ylim([-.6 .2])

end

for i=4:6

    subplot(2,2,3)
    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-3,:),'Color',colors(i-3,:),'LineWidth',2)
    title('Thrust: Slow Flap Speed (2.25 s)')
        ylim([0 .9])


    subplot(2,2,4, 'NextPlot','add')
    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-3,:),'Color',colors(i-3,:),'LineWidth',2)
    title('Lift: Slow Flap Speed (2.25 s)')
    ylim([-.6 .2])

end
legend({'60', '75', '90'})
currentFigure = gcf;
sgtitle('Flow Speed 0.1 m/s');

figure('Renderer', 'painters', 'Position', [1000 510 900 450])

for i=7:9

    subplot(2,2,1)
    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-6,:),'Color',colors(i-6,:),'LineWidth',2)
    title('Thrust: Fast Flap Speed (1.75 s)')
        ylim([0 .9])


    subplot(2,2,2, 'NextPlot','add')
    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-6,:),'Color',colors(i-6,:),'LineWidth',2)
    title('Lift: Fast Flap Speed (1.75 s)')
    ylim([-.6 .2])

end

for i=10:12

    subplot(2,2,3)
    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-9,:),'Color',colors(i-9,:),'LineWidth',2)
    title('Thrust: Slow Flap Speed (2.25 s)')
        ylim([0 .9])


    subplot(2,2,4, 'NextPlot','add')
    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-9,:),'Color',colors(i-9,:),'LineWidth',2)
    title('Lift: Slow Flap Speed (2.25 s)')
    ylim([-.6 .2])
end
legend({'60', '75', '90'})
currentFigure = gcf;
sgtitle('Flow Speed 0 m/s');


%%
close all
i=2:3:12;
clear thrust_traces lift_traces thrust_traces_std lift_traces_std
for j=1:7
    thrust_traces(j,:)      = mean_traces_thr(8,j);
    lift_traces(j,:)        = mean_traces_lift(8,j);
    thrust_traces_std(j,:)  = std_traces_thr(8,j);
    lift_traces_std(j,:)    = std_traces_lift(8,j);
end



%%
colors={[166,206,227]/255,...
    [31,120,180]/255,...
    [178,223,138]/255,...
    [51,160,44]/255,...
    [251,154,153]/255,...
    [227,26,28]/255,...
    [253,191,111]/255,...
    [255,127,0]/255,...
    [202,178,214]/255,...
    [106,61,154]/255,...
    [177,89,40]/255};
ms=1;
figure
for j=1:7
    hold on
    x=linspace(0,1,length(thrust_traces(j,:).period));
    shadedErrorBar(x,thrust_traces(j,:).period,thrust_traces_std(j,:).period, ...
        'lineprops',{'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms})
    hold off
end
title('Thrust Traces')
legend(strsplit(num2str(-roll_pow_ang)))

figure
for j=1:7
    hold on
    x=linspace(0,1,length(lift_traces(j,:).period));
    shadedErrorBar(x,lift_traces(j,:).period,lift_traces_std(j,:).period, ...
        'lineprops',{'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms})
    hold off
end
title('Lift Traces')
legend(strsplit(num2str(-roll_pow_ang)))
%%
figure

hold on
for j=1:7
    plot(thrust_traces(j,:).period,lift_traces(j,:).period,...
        'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms)
end

for j=1:7
    quiver(0,0,mean(thrust_traces(j,:).period),mean(lift_traces(j,:).period),...
        'LineWidth',3,'color',colors{j})
end
hold off

xlim([-.5,1.5])
ylim([-1.5,.5])

legend(strsplit(num2str(-roll_pow_ang)))