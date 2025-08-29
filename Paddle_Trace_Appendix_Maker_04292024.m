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
%
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
                mean_traces_thr(jj).traces=mean(traces_thr);
                mean_traces_lift(jj).traces=mean(traces_lift);

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
%% Colors

close all
clc
% colors={[166,206,227]/255, ...
%     [178,223,138]/255, ...
%     [251,154,153]/255, ...
%     [253,191,111]/255, ...
%     [202,178,214]/255, ...
%     [255,255,153]/255, ...
%     [31,120,180]/255,...
%     [227,26,28]/255,...
%     [255,127,0]/255,...
%     [106,61,154]/255,...
%     [177,89,40]/255};


colors={[253,191,111]/255, ...
    [202,178,214]/255, ...
    [166,206,227]/255, ...
    [31,120,180]/255,...
    [227,26,28]/255,...
    [255,127,0]/255,...
    [106,61,154]/255,...
    [177,89,40]/255};
%%
close all
clc

z=1;


for all_exp=1:4
    figure('Renderer', 'painters', 'Position', [10 10 1300 400]);
    for j=1:3
        for i=1:7
            
            if j==3 && i==4
                i=i-1;
            end
            period=length(mean_traces_thr(i+(7*(z-1))).traces)/250;
            x=linspace(0,period,length(mean_traces_thr(i+(7*(z-1))).traces));
            subplot(2,3,j)
            hold on
            plot(x,mean_traces_thr(i+(7*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
            hold off
            ylim([-1.5 4])
            xlim([0 0.95])

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
            plot(x,mean_traces_lift(i+(7*(z-1))).traces,'Color',colors{i},'LineWidth',1.5)
            hold off
            if j==1
                ylabel('Lift (N)')
            end
            ylim([-4 1])
            xlim([0 0.95])
            xlabel('Time (s)')
            
            fontsize(gca, 14, "points")
            fontname('Times New Roman')

        end
        z=z+1;
    end
    disp(params(i+(7*(z-2)),[1, 4]))
end




