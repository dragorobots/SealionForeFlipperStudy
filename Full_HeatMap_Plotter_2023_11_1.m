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
roll_pow_ang=results.roll_pow_ang_settings;
%flow_pow=;

%% Create Means and Layer Traces

set=1;
set_length=length(roll_pow_ang);
extra_points=[-220,-283];
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
                    clear traces_thr thrust traces_lift lift2
                    z=1;

                    for j=1:2:10

                        if j==1
                            thrust(z)=mean(thr(i,true_index(i,j):true_index(i,j+1)+extra_points(kp)));
                            traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j+1)+extra_points(kp));
                            lift2(z)=mean(lift1(i,true_index(i,j):true_index(i,j+1)+extra_points(kp)));
                            traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j+1)+extra_points(kp));
                            trace_length=length(traces_thr(z,:)+extra_points(kp));
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
                    imp_thr(jj,ii).period=mean(thrust)/round(length(thrust)/Fs);

                    mean_traces_thr(jj,ii).period=mean(traces_thr);
                    std_traces_thr(jj,ii).period=std(traces_thr)/sqrt(4);

                    mean_lif(jj,ii).period=mean(lift2);
                    std_error_lift(jj,ii).period=std(lift2);
                    imp_lift(jj,ii).period=mean(lift2)/round(length(lift2)/Fs);

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


end

%% unpack structs

for i=1:7
    for j=1:72
        mean_thrust(j,i)=mean_thr(j,i).period;
        % std_error_new_thr(j,i)=std_error_thr(j,i).period;
        % imp_thr_new(j,i)=imp_thr(j,i).period;


        mean_lift(j,i)=mean_lif(j,i).period;
        % std_error_new_lift(j,i)=std_error_lift(j,i).period;
        % imp_lift_new(j,i)=imp_lift(j,i).period;
    end
end
%%
roll_pow_ang=flip(-roll_pow_ang);
clc
%% Plot Trace Comparison for Change to yaw angles
close all
clc
c=[127,59,8; ...
    224,130,20; ...
    253,184,99; ...
    237,248,177; ...
    253,224,239; ...
    241,182,218; ...
    222,119,174; ...
    142,1,82]/255;

c=flip([103,0,31; ...
    165,0,38; ...
    253,174,97; ...
    254,224,144; ...
    255,255,191; ...
    224,243,248; ...
    171,217,233;...
    116,173,209;...
    69,117,180;...
    49,54,149])/255;

thrust_limits=[.3,.95];
lift_limits=[-.05, .35];

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


c_x=[]; c_y=[];  c_z=[];
for i=1:length(c)-1
    c_x=[c_x linspace(c(i,1),c(i+1,1))];
    c_y=[c_y linspace(c(i,2),c(i+1,2))];
    c_z=[c_z linspace(c(i,3),c(i+1,3))];

end

figure
c_new=[c_x; c_y; c_z];

xvalues = {'90','75','60','45','30','15','0'};
yvalues = {'70 degrees', '80 degrees','90 degrees', '100 degrees'};

cdata= [mean(yaw_70); mean(yaw_80); mean(yaw_90); mean(yaw_100)];
h = heatmap(xvalues,yvalues,cdata);

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Yaw Angle';

figure
c_new=[c_x; c_y; c_z];

cdata= [mean(yaw_70_lift); mean(yaw_80_lift); ...
    mean(yaw_90_lift); mean(yaw_100_lift)];
h = heatmap(xvalues,yvalues,cdata);

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Yaw Angle';
poly_order=3;
x=linspace(0,90,1000);

figure
subplot(1,4,1)
hold on
for i=10:length(yaw_100)

    if i>9
        speed_line='-';
    else
        speed_line=':';
    end

    if mod(i,3)+1 == 1
        fs_line='-';
        fs_marker='o';
    elseif mod(i,3)+1 == 2
        fs_line='--';
        fs_marker='s';
    elseif mod(i,3)+1 == 3
        fs_line=':';
        fs_marker='^';
        
    end

    if i<=12
        tran_color=[27 158 119]/255;
    elseif i<=15
        tran_color=[217 95 2]/255;
    else
        tran_color=[117 112 179]/255;
    end


    p=polyfit(roll_pow_ang,yaw_70(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(fs_line),'Color',tran_color,'LineWidth',2)
    plot(roll_pow_ang,yaw_70(i,:),strcat(fs_marker,tran_color),...
        'MarkerFaceColor',tran_color,'MarkerEdgeColor','k','MarkerSize',12)

    ylim([.15,1.15])

end
hold off

subplot(1,4,2)
hold on
for i=10:length(yaw_100)

    if i>9
        speed_line='-';
    else
        speed_line=':';
    end

    if mod(i,3)+1 == 1
        fs_line='-';
        fs_marker='o';
    elseif mod(i,3)+1 == 2
        fs_line='--';
        fs_marker='s';
    elseif mod(i,3)+1 == 3
        fs_line=':';
        fs_marker='^';
        
    end

    if i<=12
        tran_color=[27 158 119]/255;
    elseif i<=15
        tran_color=[217 95 2]/255;
    else
        tran_color=[117 112 179]/255;
    end


    p=polyfit(roll_pow_ang,yaw_80(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(fs_line),'Color',tran_color,'LineWidth',2)
    plot(roll_pow_ang,yaw_80(i,:),strcat(fs_marker,tran_color),...
        'MarkerFaceColor',tran_color,'MarkerEdgeColor','k','MarkerSize',12)

    ylim([.15,1.15])

end
hold off

subplot(1,4,3)
hold on
for i=10:length(yaw_100)

    if i>9
        speed_line='-';
    else
        speed_line=':';
    end

    if mod(i,3)+1 == 1
        fs_line='-';
        fs_marker='o';
    elseif mod(i,3)+1 == 2
        fs_line='--';
        fs_marker='s';
    elseif mod(i,3)+1 == 3
        fs_line=':';
        fs_marker='^';
        
    end

    if i<=12
        tran_color=[27 158 119]/255;
    elseif i<=15
        tran_color=[217 95 2]/255;
    else
        tran_color=[117 112 179]/255;
    end


    p=polyfit(roll_pow_ang,yaw_90(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(fs_line),'Color',tran_color,'LineWidth',2)
    plot(roll_pow_ang,yaw_90(i,:),strcat(fs_marker,tran_color),...
        'MarkerFaceColor',tran_color,'MarkerEdgeColor','k','MarkerSize',12)

    ylim([.15,1.15])

end
hold off

subplot(1,4,4)
hold on
for i=10:length(yaw_100)

    if i>9
        speed_line='-';
    else
        speed_line=':';
    end

    if mod(i,3)+1 == 1
        fs_line='-';
        fs_marker='o';
    elseif mod(i,3)+1 == 2
        fs_line='--';
        fs_marker='s';
    elseif mod(i,3)+1 == 3
        fs_line=':';
        fs_marker='^';
        
    end

    if i<=12
        tran_color=[27 158 119]/255;
    elseif i<=15
        tran_color=[217 95 2]/255;
    else
        tran_color=[117 112 179]/255;
    end


    p=polyfit(roll_pow_ang,yaw_100(i,:),poly_order);
    y=polyval(p,x);
    plot(x,y,strcat(fs_line),'Color',tran_color,'LineWidth',2)
    plot(roll_pow_ang,yaw_100(i,:),strcat(fs_marker,tran_color),...
        'MarkerFaceColor',tran_color,'MarkerEdgeColor','k','MarkerSize',12)

    ylim([.15,1.15])

end
hold off
% subplot(1,4,2)
% hold on
% plot(yaw_80','bo--')
% plot(mean(yaw_70),'b-o','LineWidth',5)
% hold off
% ylim([0,1.2])
%
% subplot(1,4,3)
% hold on
% plot(yaw_90','mo--')
% plot(mean(yaw_90),'m-o','LineWidth',5)
% hold off
% ylim([0,1.2])
%
% subplot(1,4,4)
% hold on
% plot(yaw_100','go--')
% plot(mean(yaw_100),'g-o','LineWidth',5)
% hold off
% ylim([0,1.2])



%c_test=repmat(linspace(0, 1, 25), 1, 3);
%% Change to flow speed
clc

index=[1,2,3,6,9,10,11];

zz=1;
ii=1;
for z=1:24
    j=1;

    for i=1:7

        FS_00(zz,j)=mean_thrust(z,i);
        FS_05(zz,j)=mean_thrust(z+24,i);
        FS_10(zz,j)=mean_thrust(z+48,i);

        FS_00_lift(zz,j)=mean_lift(z,i);
        FS_05_lift(zz,j)=mean_lift(z+24,i);
        FS_10_lift(zz,j)=mean_lift(z+48,i);

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
yvalues = {'0.1 m/s', '0.05m/s','0 m/s'};

cdata= [mean(FS_10); mean(FS_05); mean(FS_00)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Flow Speed';

figure
c_new=[c_x; c_y; c_z];


cdata= [mean(FS_10_lift); mean(FS_05_lift); mean(FS_00_lift)];
h = heatmap(xvalues,yvalues,round(cdata,2));

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Flow Speed';


%% Change to stroke transition
clc

zz=1;
ii=1;
for z=1:64
    j=1;

    for i=1:7

        TP_50(zz,j)=mean_thrust(z,i);
        TP_55(zz,j)=mean_thrust(z+4,i);
        TP_60(zz,j)=mean_thrust(z+8,i);

        TP_50_lift(zz,j)=mean_lift(z,i);
        TP_55_lift(zz,j)=mean_lift(z+4,i);
        TP_60_lift(zz,j)=mean_lift(z+8,i);

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
yvalues = {'smooth', 'middle','choppy'};

cdata= [mean(TP_50); mean(TP_55); mean(TP_60)];
h = heatmap(xvalues,yvalues,cdata);

h.Colormap = c_new';
h.Title = 'Mean Thrust Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Power/Paddle Transition';

figure
c_new=[c_x; c_y; c_z];


cdata= [mean(TP_50_lift); mean(TP_55_lift); mean(TP_60_lift)];
h = heatmap(xvalues,yvalues,cdata);

h.Colormap = c_new';
h.Title = 'Mean Lift Forces';
h.XLabel = 'Roll Angle';
h.YLabel = 'Power/Paddle Transition';


%% Change to flipper speed
clc

zz=1;
ii=1;
index_fast=[1:12 25:36 49:60];
index_slow=[13:24 37:48 61:72];
for i=1:length(index_slow)
    for j=1:7
        Period_175(zz,j)=mean_thrust(index_fast(i),j);
        Period_215(zz,j)=mean_thrust(index_slow(i),j);

        Period_175_lift(zz,j)=mean_lift(index_fast(i),j);
        Period_215_lift(zz,j)=mean_lift(index_slow(i),j);
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

