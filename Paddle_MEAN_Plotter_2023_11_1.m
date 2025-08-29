clear all
clc
close all
addpath('19-Oct-2022_Power_Stroke_Flipper_Results\')
load("19-Oct-2022_results_PaddleStroke.mat")

%% Paddle Stroke (Extended Yaw Amplitude)


period_settings=[1.75,2.25];
y_amp_settings=-[-60,-75,-90];
roll_paddle_ang_settings=[-90,-75,-60,-45,-30,-15, 0]*-1;
Flow_Speed_settings=[0,70];

% Loop order Flow, Speed, Yaw, Roll

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
        mean_lift_new(j,i)=mean_lift(j,i).period;
    end
end

%% ----------------------  Create Color Scheme  --------------------------

mag =   [231,41,138]/255;
blue =  [55,126,184]/255;
green = [27 158 119]/255;
purple =[117 112 179]/255;
orange= [217 95 2]/255;
gold=   [230,171,2]/255;

color_scheme=[mag; gold];


%% Plot Thrust Means Comparison for Change to yaw angles
close all
clc

zz=1;
ii=1;
for z=1:3:12
    j=1;

    for i=1:7

        yaw_60(zz,j)=mean_thr_new(z,i);
        yaw_75(zz,j)=mean_thr_new(z+1,i);
        yaw_90(zz,j)=mean_thr_new(z+2,i);

        yaw_60_lift(zz,j)=mean_lift_new(z,i);
        yaw_75_lift(zz,j)=mean_lift_new(z+1,i);
        yaw_90_lift(zz,j)=mean_lift_new(z+2,i);

        j=j+1;
    end
    zz=zz+1;

end

FontSize=16;
MarkerSize=8;
LW=2.5;
poly_order=3;
Marker_LW=2;

leng=800;
height=300;


x=linspace(0,90,1000);
roll_pow_ang=abs(roll_pow_ang);

f1=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_60(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_60(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_60(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_60(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  

    ylim([0,2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(0:.5:2.0)
    yticklabels({'0','0.5','1','1.5','2'})
    fontsize(gca,FontSize,'points')
    
end
hold off


subplot(1,3,2)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_75(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_75(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_75(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_75(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  
    ylim([0,2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    yticks(0:.5:2.0)
    yticklabels({'0','0.5','1','1.5','2'})

    fontsize(gca,FontSize,'points')

end
hold off


subplot(1,3,3)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_90(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_90(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_90(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_90(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  
    
    ylim([0,2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    yticks(0:.5:2.0)
    yticklabels({'0','0.5','1','1.5','2'})

    fontsize(gca,FontSize,'points')

end
hold off

fontsize(f1, 16, "points")
fontname('Times New Roman')

%% Plot Thrust Means Comparison for Change to yaw angles


poly_order=3;
x=linspace(0,90,1000);

f2=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_60_lift(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_60_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_60_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_60_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  

    ylim([-1 .25])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    yticks(-1:.25:.25)
    yticklabels({'-1','-0.75','-0.5','-0.25','0','0.25'})
    

end
hold off


subplot(1,3,2)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_75_lift(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_75_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_75_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_75_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  

    ylim([-1 .25])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    yticks(-1:.25:.25)
    yticklabels({'-1','-0.75','-0.5','-0.25','0','0.25'})

end
hold off


subplot(1,3,3)
hold on
for i=1:4

    if i==1 || i==3 
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i == 2
        fs_color=color_scheme(1,:);
        fs_marker='o';

    elseif i == 3 || i == 4
        fs_color=color_scheme(2,:);
        fs_marker='o';
        
    end


    p=polyfit(roll_pow_ang,yaw_90_lift(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(speed_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_90_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_90_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',.5)
      plot(roll_pow_ang,yaw_90_lift(i,:),strcat(fs_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)  

    ylim([-1 .25])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    yticks(-1:.25:.25)
    yticklabels({'-1','-0.75','-0.5','-0.25','0','0.25'})

end
hold off

fontsize(f2, 16, "points")
fontname('Times New Roman')