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

period_settings=[1.75 2.25]; % - , --
paddle_tran=[.5 .55 .6]; % o or hexagram, square, ^
y_amp_settings=-[-70 -80 -90 -100];
roll_pow_ang=[-90,-75,-60,-45,-30,-15, 0]*-1;
Flow_Speed_settings=results.Flow_Speed_settings; % color
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
        zeroed_data=filtered_data-mean(zeros(500:750,:));
        thr(i,:)=zeroed_data(:,1);
        lift1(i,:)=zeroed_data(:,2);
        ard(i,:)=data(:,3);
        params(i,:)=[abs(results.parameters(i1).parameters), ...
            results.Flow_Speed_settings];

        zeros_for_plot(i,:)=mean(zeros(500:1000,:));

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
%% unpack structs

for i=1:7
    for j=1:72
        mean_thrust(j,i)=mean_thr(j,i).period;


        mean_lift_new(j,i)=mean_lift(j,i).period;

    end
end
%%
mean_lift=mean_lift_new;
clc
%%
%% ----------------------  Create Color Scheme  --------------------------

mag =   [231,41,138]/255;
blue =  [55,126,184]/255;
green = [27 158 119]/255;
purple =[117 112 179]/255;
orange= [217 95 2]/255;
gold=   [230,171,2]/255;
red =   [227,26,28]/255;
pink =  [251,154,153]/255;

color_scheme=[gold; blue; mag; pink];


%% Plot Trace Comparison for Change to yaw angles
close all
clc



zz=1;
ii=1;
for z=1:4:72
    j=1;

    for i=1:7

        yaw_70(zz,j)=mean_thrust(z,i);
        yaw_80(zz,j)=mean_thrust(z+1,i);
        yaw_90(zz,j)=mean_thrust(z+2,i);
        yaw_100(zz,j)=mean_thrust(z+3,i);

        yaw_70_lift(zz,j)=mean_lift(z,i);
        yaw_80_lift(zz,j)=mean_lift(z+1,i);
        yaw_90_lift(zz,j)=mean_lift(z+2,i);
        yaw_100_lift(zz,j)=mean_lift(z+3,i);

        j=j+1;
    end
    zz=zz+1;

end

roll_pow_ang_true=roll_pow_ang;
FontSize=16;
MarkerSize=12;
LW=2.5;
poly_order=3;
Marker_LW=3.5;

leng=1300;
height=600;


x=linspace(0,90,1000);
f1=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)
hold on
%index=[1,2,3,7,8,9,13,14,15];
index=[1,2,3,7,8,9,13,14,15]+3;
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end


    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
        flow_speed=0;
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
        flow_speed=0.05;
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
        flow_speed=0.1;
    end

    %roll_pow_ang=AoA_Calc_Func(roll_pow_ang_true,flow_speed,1/.57);
    x=linspace(roll_pow_ang(1),roll_pow_ang(end),1000);

    p=polyfit(roll_pow_ang,yaw_70(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(tran_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_70(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_70(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_70(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)

    [val,x_ind]=max(yaw_70(i,:));
    %x_ind=interp1([0,length(y)],[roll_pow_ang(1),roll_pow_ang(end)],ind);
    %xline(x_ind,'Color',fs_color,'LineWidth',LW)
    x_ind;

    ylim([0 1.5])
    % xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(0:.5:2)
    yticklabels({'0','0.5','1','1.5','2'})

end
hold off

subplot(1,3,2)
hold on
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end

    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
        flow_speed=0;
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
        flow_speed=0.05;
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
        flow_speed=0.1;
    end

    %roll_pow_ang=AoA_Calc_Func(roll_pow_ang_true,flow_speed,1/.57);
    x=linspace(roll_pow_ang(1),roll_pow_ang(end),1000);

    p=polyfit(roll_pow_ang,yaw_80(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(tran_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_80(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_80(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_80(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)


    [val,x_ind]=max(yaw_80(i,:));
    %x_ind=interp1([0,length(y)],[roll_pow_ang(1),roll_pow_ang(end)],ind);
    %xline(x_ind,'Color',fs_color,'LineWidth',LW)
    x_ind;

    ylim([0 1.5])
    %xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(0:.5:2)
    yticklabels({'0','0.5','1','1.5','2'})
end
hold off

subplot(1,3,3)
hold on
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end

    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
        flow_speed=0;
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
        flow_speed=0.05;
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
        flow_speed=0.1;
    end

    %roll_pow_ang=AoA_Calc_Func(roll_pow_ang_true,flow_speed,1/.57);
    x=linspace(roll_pow_ang(1),roll_pow_ang(end),1000);

    p=polyfit(roll_pow_ang,yaw_90(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(tran_line),'Color',fs_color,'LineWidth',LW)
    plot(roll_pow_ang,yaw_90(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_90(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_90(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)



    [val,x_ind]=max(yaw_90(i,:));
    %x_ind=interp1([0,length(y)],[roll_pow_ang(1),roll_pow_ang(end)],ind);
    %xline(x_ind,'Color',fs_color,'LineWidth',LW)
    x_ind;

    ylim([0 1.5])
    %xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(0:.5:2)
    yticklabels({'0','0.5','1','1.5','2'})
end
hold off

fontsize(f1, 20, "points")
fontname('Times New Roman')


%% Lift Figures

poly_order=2;


f2=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)
hold on
%index=[1,2,3,7,8,9,13,14,15];
index=[1,2,3,7,8,9,13,14,15]+3;
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end

    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
    end

    p=polyfit(roll_pow_ang,yaw_70_lift(i,:),poly_order);
    y=polyval(p,x);
    %plot(x,y,strcat(tran_line),'Color',fs_color,'LineWidth',LineWidth)
    plot(roll_pow_ang,yaw_70_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_70_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_70_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)

    ylim([-.25 .75])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(-0.25:.25:1.25)
    yticklabels({'-0.25','0','0.25','0.5','0.75','1','1.25'})
    fontsize(gca,FontSize,'points')

end
hold off


subplot(1,3,2)
hold on
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end

    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
    end

    p=polyfit(roll_pow_ang,yaw_80_lift(i,:),poly_order);
    y=polyval(p,x);
    plot(roll_pow_ang,yaw_80_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_80_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_80_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)


    ylim([-.25 .75])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(-0.25:.25:1.25)
    fontsize(gca,FontSize,'points')
end
hold off


subplot(1,3,3)
hold on
for i=index

    if mod(i,3)+1 == 1
        tran_marker='s';
        tran_line='--';
    elseif mod(i,3)+1 == 2
        tran_marker='d';
        tran_line='-.';
    elseif mod(i,3)+1 == 3
        tran_marker='>';
        tran_line=':';
    end

    if max(i == index(1:3))
        fs_color =color_scheme(1,:);
    elseif max(i == index(4:6))
        fs_color =color_scheme(2,:);
    elseif max(i == index(7:9))
        fs_color =color_scheme(3,:);
    end

    p=polyfit(roll_pow_ang,yaw_90_lift(i,:),poly_order);
    y=polyval(p,x);
    plot(roll_pow_ang,yaw_90_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor',fs_color,'MarkerSize',MarkerSize,'LineWidth',Marker_LW)

    plot(roll_pow_ang,yaw_90_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize+Marker_LW,'LineWidth',1)
    plot(roll_pow_ang,yaw_90_lift(i,:),strcat(tran_marker,fs_color),...
        'MarkerEdgeColor','k','MarkerSize',MarkerSize-Marker_LW,'LineWidth',.5)

    ylim([-.25 .75])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    yticks(-0.25:.25:1.25)


end
hold off

fontsize(f2, 20, "points")
fontname('Times New Roman')