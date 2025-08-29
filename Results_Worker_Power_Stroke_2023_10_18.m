clear all
clc
close all
addpath('07-Oct-2022_Power_Stroke_Flipper_Results\')
load("07-Oct-2022_results_PowerStroke.mat")
results_1=results;
addpath('14-Oct-2022_Power_Stroke_Flipper_Results\')
load("14-Oct-2022_results_PowerStroke.mat")
results_2=results;
%% Full Stroke

period_settings=[1.75 2.25];
paddle_tran=[.5 .55 .6];
y_amp_settings=[-70 -80 -90 -100];
roll_pow_ang_settings=[-90,-75,-60,-45,-30,-15, 0];
Flow_Speed_settings=[0, 0.05, .1]; %0, 0.05, 0.1
Fs=500;



%% Unload Result Struct
% Loop order Flow, Speed, Yaw, Roll

num_experiments=length(results.exp_num);

for i=1:num_experiments
    % settings(i,:)=results(i).parameters;
    zeros=results.zeros(i).zeros*2.22; % convert to newtons
    data=results.data(i).data*2.22; % convert to newtons
    filtered_data=Data_Filters(data);
    zeroed_data=filtered_data-mean(zeros(500:1000,:));
    thr(i,:)=zeroed_data(:,1);
    lift1(i,:)=zeroed_data(:,2);
    ard(i,:)=data(:,3);

    %     figure
    %     subplot(4,1,1)
    %     plot(thr(i,:))
    %
    %     subplot(4,1,2)
    %     plot(lift1(i,:))
    %
    %     subplot(4,1,3)
    %     plot(zeros(:,1:2))
    %
    %     subplot(4,1,4)
    %     plot(ard(i,:))
end


%% Align Traces
first_skip=1000;
for k=1:num_experiments
    j=1;
    zz=1;
    on_flag=0;

    mat=ard(k,:);
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
flow_pow=results.Flow_Speed_settings;

%% Create Means and Layer Traces

set=1;
set_length=length(roll_pow_ang);
extra_points=[-220,-283];
%extra_points=-220;
jj=1;
kp=0;
for a=flow_pow
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

                    mean_lift(jj,ii).period=mean(lift2);
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
    for j=1:24
        mean_thr_new(j,i)=mean_thr(j,i).period;
        std_error_new_thr(j,i)=std_error_thr(j,i).period;
        imp_thr_new(j,i)=imp_thr(j,i).period;


        mean_lift_new(j,i)=mean_lift(j,i).period;
        std_error_new_lift(j,i)=std_error_lift(j,i).period;
        imp_lift_new(j,i)=imp_lift(j,i).period;
    end
end
roll_pow_ang=-roll_pow_ang;

%% Roll Angle Mean Graphs
c1=[215,25,28]/255;
c2=[253,174,97]/255;
c3=[171,217,233]/255;
c4=[44,123,182]/255;

curve_fit=2;
x1=linspace(0,90);

colors=[c1;c2;c3;c4];
figure('Renderer', 'painters', 'Position', [10 100 700 900])

% Set One
for i=1:4

    subplot(3,2,1)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i,:),'Color',colors(i,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(i,:),'LineWidth',2)

    title('Thrust: 50 percent transition')
    grid on
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;


    subplot(3,2,2, 'NextPlot','add')

    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i,:),'Color',colors(i,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i,:),'LineWidth',2)

    title('Lift: 50 percent transition')
    grid on
    ylim([-.1 0.45])

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)

for i=5:8

    subplot(3,2,3)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-4,:),'Color',colors(i-4,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i-4,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(i-4,:),'LineWidth',2)

    title('Thrust: 75 percent transition')
    grid on
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;

    subplot(3,2,4, 'NextPlot','add')
    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-4,:),'Color',colors(i-4,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i-4,:),'LineWidth',2)

    title('Lift: 75 percent transition')
    grid on
    ylim([-.1 0.45])

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)

for i=9:12

    subplot(3,2,5)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-8,:),'Color',colors(i-8,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i-8,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(i-8,:),'LineWidth',2)

    title('Thrust: 100 percent transition')
    grid on
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;

    subplot(3,2,6, 'NextPlot','add')
    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(i-8,:),'Color',colors(i-8,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(i-8,:),'LineWidth',2)



    title('Lift: 100 percent transition')
    grid on
    ylim([-.1 0.45])

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)
legend('70','','80','','90','','100','Location','NorthWest')
ax=gca;
ax.FontSize=12;
title_string=['Flow Speed Set at-->',num2str(Flow_Speed_settings),'m/s','\n','and Flipper Period at-->',num2str(period(1)),'s'];
sgtitle(compose(title_string),'FontSize',20)

% Set Two
colors=[c1;c2;c3;c4];
figure('Renderer', 'painters', 'Position', [10 100 700 900])
ii=1;
for i=(1:4)+12

    subplot(3,2,1)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(ii,:),'LineWidth',2)

    title('Thrust: 50 percent transition')
    grid on
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)

    xlim([0 90])
    ax=gca;
    ax.FontSize=12;
    subplot(3,2,2, 'NextPlot','add')

    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    title('Lift: 50 percent transition')
    grid on
    ylim([-.1 0.45])
    ax=gca;
    ax.FontSize=12;
    xlim([0 90])
    ii=ii+1;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)

ii=1;
for i=(5:8)+12

    subplot(3,2,3)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(ii,:),'LineWidth',2)

    title('Thrust: 75 percent transition')
    grid on
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)
    ax=gca;
    ax.FontSize=12;
    xlim([0 90])

    subplot(3,2,4, 'NextPlot','add')
    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    title('Lift: 75 percent transition')
    grid on

    ax=gca;
    ax.FontSize=12;
    ylim([-.1 0.45])
    xlim([0 90])
    ii=ii+1;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)

ii=1;
for i=(9:12)+12

    subplot(3,2,5)
    hold on
    errorbar(roll_pow_ang,mean_thr_new(i,:),std_error_new_thr(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_thr_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    [M,I]=max(f1);
    xline(linspace(x1(I),x1(I)),':','Color',colors(ii,:),'LineWidth',2)

    title('Thrust: 100 percent transition')
    grid on
    ax=gca;
    ax.FontSize=12;
    ylim([0.2 1.2])
    yticks(.2:.2:1.2)

    xlim([0 90])

    subplot(3,2,6, 'NextPlot','add')
    hold on
    errorbar(roll_pow_ang,mean_lift_new(i,:),std_error_new_lift(i,:),'s',...
        'MarkerSize',10,'MarkerEdgeColor','k',...
        'MarkerFaceColor',colors(ii,:),'Color',colors(ii,:),'LineWidth',2)

    p=polyfit(roll_pow_ang,mean_lift_new(i,:),curve_fit);
    f1=polyval(p,x1);
    plot(x1,f1,'--','Color',colors(ii,:),'LineWidth',2)

    title('Lift: 100 percent transition')
    grid on

    ax=gca;
    ax.FontSize=12;
    ylim([-.1 0.45])
    xlim([0 90])
    ii=ii+1;
end
plot(x1,linspace(0,0),'g:','LineWidth',2)
%legend('-70','','-80','','-90','','-100')

title_string=['Flow Speed Set at-->',num2str(Flow_Speed_settings),'m/s','\n','and Flipper Period at-->',num2str(period(2)),'s'];
sgtitle(compose(title_string),'FontSize',20)


%% ********** Traces ***************
%close all
% % % clear thrust_traces lift_traces thrust_traces_std lift_traces_std
% % % 
% % % for i =1:length(results.parameters)
% % %     p(i)=results.parameters(i).parameters(4);
% % % end
% % % 
% % % colors={[166,206,227]/255,...
% % %     [31,120,180]/255,...
% % %     [178,223,138]/255,...
% % %     [51,160,44]/255,...
% % %     [251,154,153]/255,...
% % %     [227,26,28]/255,...
% % %     [253,191,111]/255,...
% % %     [255,127,0]/255,...
% % %     [202,178,214]/255,...
% % %     [106,61,154]/255,...
% % %     [177,89,40]/255};
% % % 
% % % for count=1:12
% % %     %for count=1
% % %     if count ==1
% % %         yaw_str=num2str(results.parameters(count).parameters(2));
% % %         transition_str=num2str(results.parameters(count).parameters(4));
% % % 
% % %     else
% % %         yaw_str=num2str(results.parameters(count*7).parameters(2));
% % %         transition_str=num2str(results.parameters(count*7).parameters(4));
% % % 
% % %     end
% % % 
% % % 
% % %     for zz=1:7
% % %         for j=1:7
% % %             thrust_traces(j,:)      = mean_traces_thr(count,j);
% % %             lift_traces(j,:)        = mean_traces_lift(count,j);
% % %             thrust_traces_std(j,:)  = std_traces_thr(count,j);
% % %             lift_traces_std(j,:)    = std_traces_lift(count,j);
% % %         end
% % %         ms=1;
% % %         figure
% % %         for j=1:7
% % %             hold on
% % %             x=linspace(0,1,length(thrust_traces(j,:).period));
% % %             shadedErrorBar(x,thrust_traces(j,:).period,thrust_traces_std(j,:).period, ...
% % %                 'lineprops',{'color',colors{j},...
% % %                 'markerfacecolor',colors{j},'markersize',ms})
% % %             hold off
% % %         end
% % %         title('Thrust Traces')
% % %         ylim([-2,9])
% % %         transition=p(7*count);
% % % 
% % %         patch([.4 .425 .425 .4],[-10 -10 10 10],[31,120,180]/255,'FaceAlpha',.25);
% % %         patch([transition .6 .6 transition],[-10 -10 10 10],[51,160,44]/255,'FaceAlpha',.25);
% % %         patch([.6 .625 .625 .6],[-10 -10 10 10],[227,26,28]/255,'FaceAlpha',.25);
% % %         patch([.85 1 1 .85],[-10 -10 10 10],[106,61,154]/255,'FaceAlpha',.25);
% % % 
% % %         text(.01,7.5,['yaw=',yaw_str])
% % %         text(.01,6.5,['paddle/power transition=',transition_str])
% % % 
% % % 
% % %         exportgraphics(gcf,'Thrust_Trace.gif','Append',true);
% % %         %     legend([strsplit(num2str(roll_pow_ang_settings)),'Recovery End',...
% % %         %         'Power/Paddle Transition','Power End','Reset'],'location','northwest')
% % % 
% % % 
% % %         figure
% % %         for j=1:7
% % %             hold on
% % %             x=linspace(0,1,length(lift_traces(j,:).period));
% % %             shadedErrorBar(x,lift_traces(j,:).period,lift_traces_std(j,:).period, ...
% % %                 'lineprops',{'color',colors{j},...
% % %                 'markerfacecolor',colors{j},'markersize',ms})
% % %             hold off
% % %         end
% % %         title('Lift Traces')
% % %         ylim([-6,6])
% % %         patch([.4 .425 .425 .4],[-10 -10 10 10],[31,120,180]/255,'FaceAlpha',.25);
% % %         patch([transition .6 .6 transition],[-10 -10 10 10],[51,160,44]/255,'FaceAlpha',.25);
% % %         patch([.6 .625 .625 .6],[-10 -10 10 10],[227,26,28]/255,'FaceAlpha',.25);
% % %         patch([.85 1 1 .85],[-10 -10 10 10],[106,61,154]/255,'FaceAlpha',.25);
% % % 
% % %         text(.01,4,['yaw=',yaw_str])
% % %         text(.01,3,['paddle/power transition=',transition_str])
% % %         exportgraphics(gcf,'Lift_Trace.gif','Append',true);
% % % 
% % %         legend([strsplit(num2str(-roll_pow_ang_settings)),'Recovery End',...
% % %             'Power/Paddle Transition','Power End','Reset'],'FontSize',16,...
% % %             'location','northwest')
% % %     end
% % % end
% % % %%
% % % colors={[166,206,227]/255,...
% % %     [31,120,180]/255,...
% % %     [178,223,138]/255,...
% % %     [51,160,44]/255,...
% % %     [251,154,153]/255,...
% % %     [227,26,28]/255,...
% % %     [253,191,111]/255,...
% % %     [255,127,0]/255,...
% % %     [202,178,214]/255,...
% % %     [106,61,154]/255,...
% % %     [177,89,40]/255};
% % % 
% % % 
% % % blue_colors={[166,206,227]/255,...
% % %     [31,120,180]/255,...
% % %     [178,223,138]/255,...
% % %     [51,160,44]/255,...
% % %     [251,154,153]/255,...
% % %     [227,26,28]/255,...
% % %     [253,191,111]/255,...
% % %     [255,127,0]/255,...
% % %     [202,178,214]/255,...
% % %     [106,61,154]/255,...
% % %     [177,89,40]/255};
% % % f1=figure;
% % % 
% % % 
% % % for count=1:12
% % %     hold on
% % %     for j=1:7
% % % 
% % %         if count ==1
% % %             yaw_str=num2str(results.parameters(count).parameters(2));
% % %             transition_str=num2str(results.parameters(count).parameters(4));
% % % 
% % %         else
% % %             yaw_str=num2str(results.parameters(count*7).parameters(2));
% % %             transition_str=num2str(results.parameters(count*7).parameters(4));
% % % 
% % %         end
% % % 
% % %         thrust_traces(j,:)      = mean_traces_thr(count,j);
% % %         lift_traces(j,:)        = mean_traces_lift(count,j);
% % %         thrust_traces_std(j,:)  = std_traces_thr(count,j);
% % %         lift_traces_std(j,:)    = std_traces_lift(count,j);
% % % 
% % %         plot(thrust_traces(j,:).period,lift_traces(j,:).period,...
% % %             'color',colors{j},...
% % %             'markerfacecolor',colors{j},'markersize',6,'LineWidth',2.5)
% % %         ax=gca;
% % %         ax.FontSize=16;
% % % 
% % %         xlim([-2,8]);
% % %         ylim([-4.5,6.5]);
% % %         xlabel('Thrust')
% % %         ylabel('Lift')
% % % 
% % %         quiver(0,0,mean(thrust_traces(j,:).period)*3,...
% % %             mean(lift_traces(j,:).period)*3,...
% % %             'LineWidth',4,'color',colors{j})
% % % 
% % %         text(-2.05,6,['yaw=',yaw_str])
% % %         text(-2.05,5,['paddle/power transition=',transition_str])
% % %         exportgraphics(gcf,'TwoD.gif','Append',true);
% % % 
% % %     end
% % %     clf(f1)
% % % end
% % % 
% % % 
% % % 
% % % 
% % % %