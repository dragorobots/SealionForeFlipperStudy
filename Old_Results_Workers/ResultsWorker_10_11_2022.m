clear
clc
close all
addpath('07-Oct-2022_Power_Stroke_Flipper_Results\')
load("07-Oct-2022_results_PowerStroke.mat")

%% Power Stroke


period=[1.75,2.25];
y_amp=[-60, -75, -90];
roll=[-90,-75,-60,-55,-50,-45,-40,-35,-30,-15,0];
%roll_pow_ang_settings=[0];
Flow_Speed=[28,70];

% Loop order Flow, Speed, Yaw, Roll

num_experiments=length(results.data);
force_scale=2.22;
for i=1:num_experiments
    % settings(i,:)=results(i).parameters;
    zeros=results.zeros(i).zeros;
    data=results.data(i).data;
    filtered_data=Data_Filters(data);
    zeroed_data=filtered_data-mean(zeros(500:1000,:));
    thr(i,:)=zeroed_data(:,1)*force_scale;
    lift1(i,:)=zeroed_data(:,2)*force_scale;
    ard(i,:)=data(:,3);
end

%% Align Traces
first_skip=700;
for k=1:length(results.data)
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
true_index=true_index(:,1:10);

%%
z=1;
for i=1:2:length(true_index(1,:))-1
    for j=1:length(true_index(:,1))
        diff(z)=true_index(j,i)-true_index(j,i+1);
        z=z+1;

    end
end

plot(diff)

%% Rename Variables
close all
period=results.period_settings;
y_amp=results.y_amp_settings;
roll_pow_ang=results.roll_pow_ang_settings;
flow_pow=results.Flow_Speed_settings;

%%
set=1;
set_length=length(roll_pow_ang);
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
                        thrust(z)=mean(thr(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j)+trace_length-1));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        % hold on
                        % plot(traces_thr(z,:))
                        % hold off
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
            
            figure
            plot(roll_pow_ang,[mean_thr(jj,:).period])
            title(strcat(num2str(kk),'',num2str(k)))
            set=set+set_length;

            jj=jj+1;
        end
    end


end

%% unpack structs
for i=1:11
    for j=1:12
        mean_thr_new(j,i)=mean_thr(j,i).period;
        std_error_new_thr(j,i)=std_error_thr(j,i).period;

        mean_lift_new(j,i)=mean_lift(j,i).period;
        std_error_new_lift(j,i)=std_error_lift(j,i).period;
    end
end

%% Plot All
close all
plot_yaw([1,3],roll_pow_ang,.05,1.75,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+3,roll_pow_ang,.05,2.25,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+6,roll_pow_ang,.1,1.75,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+9,roll_pow_ang,.1,2.25,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)


%%
close all
set_num=8;
clear thrust_traces lift_traces thrust_traces_std lift_traces_std
for j=1:11
    thrust_traces(j,:)      = mean_traces_thr(set_num,j);
    lift_traces(j,:)        = mean_traces_lift(set_num,j);
    thrust_traces_std(j,:)  = std_traces_thr(set_num,j);
    lift_traces_std(j,:)    = std_traces_lift(set_num,j);
end

for j=1:length(roll_pow_ang)
    Angle_of_attack(j)=round(AoA_Calc_Func(roll_pow_ang(j),.1,1.75));
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
for j=1:11
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
for j=1:11
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
for j=1:11
    hold on
    plot(thrust_traces(j,:).period,lift_traces(j,:).period,...
        'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms,'LineWidth',1.5)

end

for j=1:11
    quiver(0,0,mean(thrust_traces(j,:).period),mean(lift_traces(j,:).period),...
        'LineWidth',5,'color',colors{j})
end

hold off
xlim([-1,4])
ylim([-1,4])
xlabel('Thrust')
ylabel('lift')
title('2D forces at flipper speed= 1.75s and flow speed= 0.1m/s')
legend(strsplit(num2str(-roll_pow_ang)))

%%

function plot_yaw(points,roll_pow_ang,Flow_Speed,Flipper_Speed,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

c1=[228,26,28]/255;
c2=[55,126,184]/255;
c3=[77,175,74]/255;
colors=[c1;c2;c3];

curve_fit=2;
x1=linspace(0,90,1000);

for j=1:length(roll_pow_ang)
    Angle_of_attack(j)=round(AoA_Calc_Func(roll_pow_ang(j),Flow_Speed,Flipper_Speed));
end

% Inner layout
figure
t1 = tiledlayout(1,1);
ax2 = axes(t1);
ax2.FontSize=16;
ax2.XAxisLocation = 'top';
ax2.YTick=[];
ax2.XLim=[min(Angle_of_attack) max(Angle_of_attack)];
ax2.XTick=min(Angle_of_attack):10:max(Angle_of_attack);
s={'  '};
fig_title=strcat('Thrust @ Flow Speed=',num2str(Flow_Speed),'m/s',s,'Flipper Speed=',num2str(Flipper_Speed),'s');
title(fig_title,'FontSize',14)

xlabel('AoA');
ax1 = axes(t1);
ax1.XAxisLocation = 'bottom';
ax1.FontSize=16;
j=1;
for i=points(1):points(2)

    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(j,:),'Color',colors(j,:),'LineWidth',2)


    p=polyfit(-roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(j,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(j,:),'LineWidth',2)

    xlabel('Flipper Roll Angle','FontSize',16);
    ylim([0,2.5])
    ylabel('Thrust (N)','FontSize',16);
    j=j+1;
end

% Inner layout
figure
t2 = tiledlayout(1,1);
ax2 = axes(t2);
ax2.FontSize=16;
ax2.XAxisLocation = 'top';
ax2.YTick=[];
ax2.XLim=[min(Angle_of_attack) max(Angle_of_attack)];
ax2.XTick=min(Angle_of_attack):10:max(Angle_of_attack);
s={'  '};
fig_title=strcat('Lift @ Flow Speed=',num2str(Flow_Speed),'m/s',s,'Flipper Speed=',num2str(Flipper_Speed),'s');
title(fig_title,'FontSize',14)

xlabel('AoA');
ax1 = axes(t2);
ax1.XAxisLocation = 'bottom';
ax1.FontSize=16;
j=1;
for i=points(1):points(2)

    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(j,:),'Color',colors(j,:),'LineWidth',2)

    p=polyfit(-roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(j,:),'LineWidth',2)

    xlabel('Flipper Roll Angle','FontSize',16);
    ylim([0,2.5])
    ylabel('Lift (N)','FontSize',16);
    j=j+1;
end

end

