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


%% Plot Trace Comparison for Flow Speed
close all
clc
colors={[165,0,38]/255,...
    [215,48,39]/255,...
    [253,174,97]/255,...
    [171,217,233]/255,...
    [116,173,209]/255,...
    [69,117,180]/255,...
    [49,54,149]/255,...
    [255,127,0]/255,...
    [202,178,214]/255,...
    [106,61,154]/255,...
    [177,89,40]/255};
roll_pow_ang=abs(roll_pow_ang);
index=1:7;


for z=1:2:12
    figure('Renderer', 'painters', 'Position', [10 10 500 650])
    j=1;

    for i=index
        hold on
        subplot(3,2,1)
        period=length(mean_traces_thr(z,i).period)/250;
        x=linspace(0,period,length(mean_traces_thr(z,i).period));
        plot(x,mean_traces_thr(z,i).period,'color',colors{j},'LineWidth',3)

        hold off
        xlim([0 .75])
        ylim([-1.5 4])
        ylabel('Lift Force (N)')
        xlabel('Time (s)')
        xticks(0:.25:.75)
        xticklabels({'0','0.25','0.50','0.75'})
        ax=gca;
        ax.FontSize=12;

        j=j+1;
    end
    j=1;
    for i=index
        hold on
        subplot(3,2,2)
        plot(roll_pow_ang(i),mean_thr_new(z,i),'s',...
            'MarkerEdgeColor','k','MarkerFaceColor',colors{j},'MarkerSize',12)

        hold off
        j=j+1;
    end
    x1=linspace(0,max(roll_pow_ang));
    p1=polyfit(roll_pow_ang,mean_thr_new(z,:),3);
    y1=polyval(p1,x1);
    hold on
    subplot(3,2,2)
    plot(x1,y1,'--k','LineWidth',2)
    hold off
    xlim([0 90])
    ylim([-.5 2.25])
    xlabel('degrees (\circ)')
    xticks(0:30:90)
    xticklabels({'0','30','60','90'})
    ax=gca;
    ax.FontSize=12;

    j=1;

    for i=index
        hold on
        subplot(3,2,3)
        period=length(mean_traces_lift(z,i).period)/250;
        x=linspace(0,period,length(mean_traces_lift(z,i).period));
        plot(x,mean_traces_lift(z,i).period,'color',colors{j},'LineWidth',3)

        hold off
        xlim([0 .75])
        ylim([-1.5 4])
        ylabel('Lift Force (N)')
        xlabel('Time (s)')
        xticks(0:.25:.75)
        xticklabels({'0','0.25','0.50','0.75'})
        ax=gca;
        ax.FontSize=12;
        j=j+1;
    end
    j=1;

    for i=index
        hold on
        subplot(3,2,4)
        plot(roll_pow_ang(i),mean_lift_new(z,i),'s',...
            'MarkerEdgeColor','k','MarkerFaceColor',colors{j},'MarkerSize',12)

        hold off
        j=j+1;
        xlim([0 90])
    ylim([-.5 2.25])
        xlabel('degrees (\circ)')
        xticks(0:30:90)
        xticklabels({'0','30','60','90'})
        ax=gca;
        ax.FontSize=12;

    end
    x1=linspace(0,max(roll_pow_ang));
    p1=polyfit(roll_pow_ang,mean_lift_new(z,:),3);
    y1=polyval(p1,x1);
    hold on
    subplot(3,2,4)
    plot(x1,y1,'--k','LineWidth',2)
    hold off

    ind = z*7- 6;
    text={strcat('Period -->',num2str(params(ind,1))),...
          strcat('YAW    -->',num2str( params(ind,2))),...
          strcat('Flow   -->',num2str( params(ind,4)))};
    dim = [.3 .15 0.3 0.1];
    annotation('textbox',dim,'String',text)
end

%% Plot Trace Comparison for Change to yaw angles
close all
clc
c=[142,1,82; ...
    222,119,174; ...
    241,182,218; ...
    253,224,239; ... 
    230,245,208; ...
    184,225,134; ...
    127,188,65; ...
    39,100,25]/255;

index=[1,2,3,6,9,10,11];
mean_thrust=mean_thr_new;
mean_lift= mean_lift_new;

zz=1;
ii=1;
for z=1:3:9
    j=1;
    
    for i=1:7
        
        yaw_60(zz,j)=mean_thrust(z,i);
        yaw_75(zz,j)=mean_thrust(z+1,i);
        yaw_90(zz,j)=mean_thrust(z+2,i);
        
        yaw_60_lift(zz,j)=mean_lift(z,i);
        yaw_75_lift(zz,j)=mean_lift(z+1,i);
        yaw_90_lift(zz,j)=mean_lift(z+2,i);

        j=j+1;
    end
    zz=zz+1;
    
end


c_x=[]; c_y=[];  c_z=[]; 
for i=1:length(c)-1
    c_x=[c_x linspace(c(i,1),c(i+1,1))];
    c_y=[c_y linspace(c(i,2),c(i+1,2))];
    c_z=[c_z linspace(c(i,3),c(i+1,3))];

end

figure
c_new=[c_x; c_y; c_z];

xvalues = {'90','75','60','45','30','15','0'};
yvalues = {'60 degrees', '75 degrees','90 degrees'};

cdata= [mean(yaw_60); mean(yaw_75); mean(yaw_90)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Yaw Angle';

figure
c_new=[c_x; c_y; c_z];

cdata= [mean(yaw_60_lift); mean(yaw_75_lift); mean(yaw_90_lift)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Yaw Angle';


%c_test=repmat(linspace(0, 1, 25), 1, 3);
%% Change to flow speed
clc

c=[142,1,82; ...
    222,119,174; ...
    241,182,218; ...
    253,224,239; ... 
    230,245,208; ...
    184,225,134; ...
    127,188,65; ...
    39,100,25]/255;

zz=1;
ii=1;
for z=1:6
    j=1;
    
    for i=1:7
        
        FS_00(zz,j)=mean_thrust(z,i);
        FS_05(zz,j)=mean_thrust(z+6,i);

        FS_00_lift(zz,j)=mean_lift(z,i);
        FS_05_lift(zz,j)=mean_lift(z+6,i);

        j=j+1;
    end
    zz=zz+1;
    
end

c_x=[]; c_y=[];  c_z=[]; 
for i=1:length(c)-1
    c_x=[c_x linspace(c(i,1),c(i+1,1))];
    c_y=[c_y linspace(c(i,2),c(i+1,2))];
    c_z=[c_z linspace(c(i,3),c(i+1,3))];

end

figure
c_new=[c_x; c_y; c_z];
xvalues = {'90','75','60','45','30','15','0'};
yvalues = {'0.05m/s','0 m/s'};

cdata= [mean(FS_05); mean(FS_00)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Flow Speed';

figure
c_new=[c_x; c_y; c_z];

cdata= [mean(FS_05_lift); mean(FS_00_lift)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Flow Speed';


%% Change to flipper speed
clc


index=[1,2,3,6,9,10,11];

zz=1;
ii=1;
f=1;
fast_ind=[1,2,3,7,8,9];
slow_ind=[4,5,6,10,11,12];
for i=1:length(fast_ind)
    for j=1:7       
        Period_175(zz,j)=mean_thrust(fast_ind(i),j);
        Period_215(zz,j)=mean_thrust(slow_ind(i),j);

        Period_175_lift(zz,j)=mean_lift(fast_ind(i),j);
        Period_215_lift(zz,j)=mean_lift(slow_ind(i),j);
    end
    zz=zz+1;
end

c=[142,1,82; ...
    222,119,174; ...
    241,182,218; ...
    253,224,239; ... 
    230,245,208; ...
    184,225,134; ...
    127,188,65; ...
    39,100,25]/255;

c_x=[]; c_y=[];  c_z=[]; 
for i=1:length(c)-1
    c_x=[c_x linspace(c(i,1),c(i+1,1))];
    c_y=[c_y linspace(c(i,2),c(i+1,2))];
    c_z=[c_z linspace(c(i,3),c(i+1,3))];
end

figure
c_new=[c_x; c_y; c_z];
xvalues = {'90','75','60','45','30','15','0'};
yvalues = {'Fast Flap','Slow Flap'};

cdata= [mean(Period_175); mean(Period_215)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Power Stroke Speed';

figure
c_new=[c_x; c_y; c_z];

cdata= [mean(Period_175_lift); mean(Period_215_lift)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Power Stroke Speed';
