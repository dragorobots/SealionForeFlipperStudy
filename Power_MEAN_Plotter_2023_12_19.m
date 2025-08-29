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
extra_points2=50;
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
                mean_lift_struct(jj,ii).period=mean(lift2);


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
        mean_lift(j,i)=mean_lift_struct(j,i).period;

        z=z+1;
    end
end

index=[1,2,3,6,9,10,11];
roll_pow_ang_true=roll_pow_ang;
roll_pow_ang=roll_pow_ang(index);

%% ----------------------  Create Color Scheme  --------------------------

mag =   [231,41,138]/255;
blue =  [55,126,184]/255;
green = [27 158 119]/255;
purple =[117 112 179]/255;
orange= [217 95 2]/255;
gold=   [230,171,2]/255;

color_scheme=[mag; blue; gold];

%% Thrust Figures
fast_ind=[1,2,3,7,8,9,13,14,15];
thrust_limits=[.1,1.4];
lift_limits=[.5, 1.9];
x=linspace(0,90,1000);



zz=1;
ii=1;
for z=1:3:18
    j=1;
    
    for i=index
        
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

FontSize=16;
MarkerSize=8;
LW=2.5;
poly_order=3;
Marker_LW=2;

leng=800;
height=300;

%roll_pow_ang=roll_pow_ang(index);
f1=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)

hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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

    
    [val,ind]=max(y);
    x_ind=interp1([0,length(y)],[0,90],ind);
    xline(x_ind,speed_line,'Color',fs_color,'LineWidth',LW)

    %'MarkerFaceColor',fs_color,
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)
    ylim([0 1.6])
    yticks(0:.2:1.6)
    yticklabels({'0','','0.4','','0.8','','1.2','','1.6'})

end
hold off


subplot(1,3,2)
hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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


          [val,ind]=max(y);
    x_ind=interp1([0,length(y)],[0,90],ind);
    xline(x_ind,speed_line,'Color',fs_color,'LineWidth',LW)

    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    ylim([0 1.6])
    yticklabels({'0','','0.4','','0.8','','1.2','','1.6'})
    

end
hold off

subplot(1,3,3)
hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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
   
    [val,ind]=max(y);
    x_ind=interp1([0,length(y)],[0,90],ind);
    xline(x_ind,speed_line,'Color',fs_color,'LineWidth',LW)

    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    xtickangle(0)

    ylim([0 1.6])
    yticklabels({'0','','0.4','','0.8','','1.2','','1.6'})
    
end
hold off

fontsize(f1, 16, "points")
fontname('Times New Roman')

%% LIFT

poly_order=3;


f2=figure('Position', [100, 100, leng, height]);
subplot(1,3,1)
hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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



    ylim([.4 2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    yticks(.4:.2:2)
    xtickangle(0)
    yticklabels({'0.4','','0.8','','1.2','','1.6','','2.0'})
    fontsize(gca,FontSize,'points')

end
hold off


subplot(1,3,2)
hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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

    ylim([.4 2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    yticks(.4:.2:2)
    xtickangle(0)
    yticklabels({'0.4','','0.8','','1.2','','1.6','','2.0'})

end
hold off

subplot(1,3,3)
hold on
for i=1:6

    if i==1 || i==3 || i==5
        speed_line='-';
    else
        speed_line=':';
    end

    if i == 1 || i ==2
        fs_color=color_scheme(1,:);
        fs_marker='o';
    elseif i == 3 || i ==4
        fs_color=color_scheme(2,:);
        fs_marker='o';
    elseif i == 5 || i ==6
        fs_color=color_scheme(3,:);
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

    ylim([.4 2])
    xlim([0 90])
    xticks(0:15:90)
    xticklabels({'0','','30','','60','','90'})
    yticks(.4:.2:2)
    xtickangle(0)
    yticklabels({'0.4','','0.8','','1.2','','1.6','','2.0'})

end
hold off

fontsize(f2, 16, "points")
fontname('Times New Roman')