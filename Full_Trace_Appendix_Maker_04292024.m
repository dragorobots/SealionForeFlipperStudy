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
        zeroed_data=filtered_data-mean(zeros(500:1000,:));
        thr(i,:)=zeroed_data(:,1);
        lift1(i,:)=zeroed_data(:,2);
        ard(i,:)=data(:,3);
        params(i,:)=[abs(results.parameters(i1).parameters), ...
            results.Flow_Speed_settings];
        % figure
        % plot(thr(i,:))

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
                    

                    experimental_vars(jj,:)=[a,k,aa,kk,roll_pow_ang((i+1)-set)];
                    mean_traces_thr(jj).traces=mean(traces_thrust_temp);
                    mean_traces_lift(jj).traces=mean(traces_lift_temp);
                    ii=ii+1;
                    jj=jj+1;

                end

                %         figure
                %         plot(roll_pow_ang,mean_thr)
                %        title(strcat(num2str(kk),'',num2str(k)))
                set=set+set_length;
            end
        end
    end
end

%%
Results.experimental_vars_order={'Flow Speed', 'Period', 'Transition Time','Yaw Amplitude','Roll Power Angle'};
Results.experimental_vars=experimental_vars;
Results.Thurst=mean_traces_thr;
Results.Lift=mean_traces_lift;

save('Full_Stroke_Results','Results')


%% Colors
close all
clc
colors={[253,191,111]/255, ...
    [202,178,214]/255, ...
    [166,206,227]/255, ...
    [31,120,180]/255,...
    [227,26,28]/255,...
    [255,127,0]/255,...
    [106,61,154]/255,...
    [177,89,40]/255};

%center_color=[51,160,44]/255;
%%

close all
clc
z=1;

for all_exp=1:18
    figure('Renderer', 'painters', 'Position', [10 10 1300 400]);
    for j=1:4
        if j~= 4
            for i=1:7

                if j==3 && i==4
                    i=i-1;
                end
                period=length(mean_traces_thr(i+(7*(z-1))).traces)/500;
                x=linspace(0,period,length(mean_traces_thr(i+(7*(z-1))).traces));
                subplot(2,3,j)
                hold on
                plot(x,mean_traces_thr(i+(7*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
                hold off


                if j==1
                    ylabel('Thrust (N)')
                end
                fontsize(gca, 14, "points")
                fontname('Times New Roman')

                if j==1
                    title('Yaw 70^o', FontSize=16)
                elseif j==2
                    title('Yaw 80^o', FontSize=16)
                elseif j==3
                    title('Yaw 90^o', FontSize=16)
                end

                xlim([0 1.2])
                ylim([-1 6])
                xticks(0:.4:1.2)

                subplot(2,3,j+3)
                hold on
                plot(x,mean_traces_lift(i+(7*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
                hold off
                if j==1
                    ylabel('Lift (N)')
                end

                xlabel('Time (s)')
                xlim([0 1.2])
                ylim([-4.5 4.5])
                xticks(0:.4:1.2)
                
                fontsize(gca, 14, "points")
                fontname('Times New Roman')

            end
        end
        z=z+1;
    end
    disp(params(i+(7*(z-2)),[1 4 5]))
end

