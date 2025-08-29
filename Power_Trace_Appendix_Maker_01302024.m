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
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);
                    else
                        traces_thr(z,:)=thr(i,true_index(i,j):true_index(i,j)+trace_length-1);
                        traces_lift(z,:)=lift1(i,true_index(i,j):true_index(i,j)+trace_length-1);

                    end
                    z=z+1;
                end
                mean_traces_thr(jj).traces=mean(traces_thr);
                mean_traces_lift(jj).traces=mean(traces_lift);

                ii=ii+1;
                jj=jj+1;
            end
            set=set+set_length;
        end
    end
end

%% Colors

close all
clc
colors={[166,206,227]/255, ...
    [178,223,138]/255, ...
    [251,154,153]/255, ...
    [253,191,111]/255, ...
    [202,178,214]/255, ...
    [255,255,153]/255, ...
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


for all_exp=1:6
    figure('Renderer', 'painters', 'Position', [10 10 1300 400]);
    for j=1:3
        for i=1:11

            if all_exp==2 && i==5 && j==2
                i=i-1;
            end
            period=length(mean_traces_thr(i+(11*(z-1))).traces)/250;
            x=linspace(0,period,length(mean_traces_thr(i+(11*(z-1))).traces));
            subplot(2,3,j)
            hold on
            plot(x,mean_traces_thr(i+(11*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
            hold off
            ylim([-1.5 4])
            xlim([0 .65])

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


            subplot(2,3,j+3)
            hold on
            plot(x,mean_traces_lift(i+(11*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
            hold off
            if j==1
                ylabel('Lift (N)')
            end
            ylim([-1.5 4])
            xlim([0 .65])
            xlabel('Time (s)')
            
            fontsize(gca, 14, "points")
            fontname('Times New Roman')

        end
        z=z+1;
    end
    disp(params(i+(11*(z-2)),[1, 4]))
end


