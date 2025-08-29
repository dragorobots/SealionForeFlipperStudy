clear
clc
close all
load("14-Oct-2022_results_PowerStroke.mat")

period=[1.75,2.25];
y_amp=[-60, -75, -90];
roll=[-90,-75,-60,-55,-50,-45,-40,-35,-30,-15,0];
%roll_pow_ang_settings=[0];
Flow_Speed=[100,0];

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
%     figure
%     plot(ard(i,:))

end
%%


%% Fix arduino signal by bounding it

for i=1:num_experiments
    for j=1:length(ard)
        if ard(i,j)<2
            ard(i,j)=1;
        end
        if ard(i,j)>2
            ard(i,j)=10;
        end

    end

end

plot(ard(1,:),'-o')
%% Align Traces
first_skip=700;
for k=1:length(results.data)
    j=1;
    zz=1;
    ep=1;
    mat=ard(k,:);

    if mat(first_skip)==1
        for i=first_skip:length(mat)-1
            
            p1=mat(i);
            p2=mat(i+1);

            if logical(mod(j,2))
                if p2-p1 >= 1 && (i-ep)>200
                    true_index(k,j)=i;
                    j=j+1;
                    sp=i;
                end
            end

            if logical(~mod(j,2))
                
                if p2-p1 <= -1 && (i-sp)>50
                    true_index(k,j)=i;
                    j=j+1;
                    ep=i;
                end
            end
        end
    else
        first_skip=first_skip+1;
    end
    
end

%%
z=1;
for i=1:2:11
    for j=1:length(true_index(:,1))
        diff(j,i)=true_index(j,i)-true_index(j,i+1);
        z=z+1;

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
extra_points=[-23,-29];
jj=1;
for a=flow_pow
    for k=1:length(period)
        for kk=y_amp
            ii=1;

            for i=set:set+set_length-1
                clear traces_thr thrust traces_lift lift2
                z=1;

                for j=1:2:10

                    if j==1
                        thrust(z)=mean(thr(i,true_index(i,j):true_index(i,j+1)+extra_points(k)));
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j+1)+extra_points(k));
                        lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j+1)+extra_points(k)));
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j+1)+extra_points(k));
                        trace_length=length(traces_thr(z,:)+extra_points(k));
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
for i=1:11
    for j=1:12
        mean_thr_new(j,i)=mean_thr(j,i).period;
        std_error_new_thr(j,i)=std_error_thr(j,i).period;

        mean_lift_new(j,i)=mean_lift(j,i).period;
        std_error_new_lift(j,i)=std_error_lift(j,i).period;
    end
end

%% Plot All

plot_yaw([1,3],roll_pow_ang,.15,1.75,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+3,roll_pow_ang,.15,2.25,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+6,roll_pow_ang,0,1.75,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

plot_yaw([1,3]+9,roll_pow_ang,0,2.25,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)


%%
close all
i=2:3:12;
clear thrust_traces lift_traces thrust_traces_std lift_traces_std
for j=1:11
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
for j=1:11
    hold on
    x=linspace(0,1,length(thrust_traces(j,:).period));
    shadedErrorBar(x,thrust_traces(j,:).period,thrust_traces_std(j,:).period, ...
        'lineprops',{'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms})
    hold off
end
title('Thrust Traces')
legend(strsplit(num2str(roll_pow_ang)))

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
legend(strsplit(num2str(roll_pow_ang)))
%%
figure

hold on
for j=1:11
    plot(thrust_traces(j,:).period,lift_traces(j,:).period,...
        'color',colors{j},...
        'markerfacecolor',colors{j},'markersize',ms)
end

for j=1:11
    quiver(0,0,mean(thrust_traces(j,:).period),mean(lift_traces(j,:).period),...
        'LineWidth',3,'color',colors{j})
end
hold off

xlim([-1,2])
ylim([-1,2])

legend(strsplit(num2str(roll_pow_ang)))

%%

function plot_yaw(points,roll_pow_ang,Flow_Speed,Flipper_Speed,...
    mean_thr_new,std_error_new_thr,mean_lift_new,std_error_new_lift)

c1=[228,26,28]/255;
c2=[55,126,184]/255;
c3=[77,175,74]/255;
colors=[c1;c2;c3];

for j=1:length(roll_pow_ang)
    Angle_of_attack(j)=round(AoA_Calc_Func(roll_pow_ang(j),Flow_Speed,Flipper_Speed));
end

% Inner layout
figure
t1 = tiledlayout(1,1);
ax2 = axes(t1);
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
j=1;
for i=points(1):points(2)

    hold on
    errorbar(-roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(j,:),'Color',colors(j,:),'LineWidth',2)
    xlabel('Flipper Roll Angle')
    ylim([0,2.5])
    ylabel('Thrust (N)');
    j=j+1;
end

% Inner layout
figure
t2 = tiledlayout(1,1);
ax2 = axes(t2);
ax2.XAxisLocation = 'top';
ax2.YTick=[];
ax2.XLim=[min(Angle_of_attack) max(Angle_of_attack)];
ax2.XTick=min(Angle_of_attack):10:max(Angle_of_attack);
s={'  '};
fig_title=strcat('Thrust @ Flow Speed=',num2str(Flow_Speed),'m/s',s,'Flipper Speed=',num2str(Flipper_Speed),'s');
title(fig_title,'FontSize',14)

xlabel('AoA');
ax1 = axes(t2);
ax1.XAxisLocation = 'bottom';
j=1;
for i=points(1):points(2)

    hold on
    errorbar(-roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(j,:),'Color',colors(j,:),'LineWidth',2)
    xlabel('Flipper Roll Angle')
    ylim([0,2.5])
    ylabel('Thrust (N)');
    j=j+1;
end

end
