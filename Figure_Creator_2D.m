clear
%close all
clc

mag =   [231,41,138]/255;
blue =  [55,126,184]/255;
green = [27 158 119]/255;
purple =[117 112 179]/255;
orange= [217 95 2]/255;
gold=   [230,171,2]/255;
red =   [227,26,28]/255;
pink =  [251,154,153]/255;

load('Power_Traces.mat')
Lift_Power=lift_trace_master;
Thrust_Power=thr_trace_master;

load('Paddle_Traces.mat')
Lift_Paddle=lift_trace_master;
Thrust_Paddle=thr_trace_master;

load('Full_Traces.mat')
Lift_Full=lift_trace_master;
Thrust_Full=thr_trace_master;

colors=[228,26,28; 55,126,184; 77,175,74]/255;

lower_bound=-4;
upper_bound=4;

f5=figure('Position', [10 10 300 300]);

hold on
plot(Thrust_Power,Lift_Power,'color',gold,'LineWidth',3)
scatter(mean(Thrust_Power),mean(Lift_Power),'color',gold,'SizeData',5)

plot(Thrust_Paddle,Lift_Paddle,'color',red,'LineWidth',3)
scatter(mean(Thrust_Paddle),mean(Lift_Paddle),'color',red,'SizeData',5)

plot(Thrust_Full,Lift_Full,'color',purple,'LineWidth',3)
scatter(mean(Thrust_Full),mean(Lift_Full),'color',purple,'SizeData',5)


xline(0,'k')
yline(0,'k')
%xlim([lower_bound upper_bound])

xlim([-1 upper_bound])
ylim([lower_bound upper_bound])
hold off

title('2D Force')
xlabel('Thrust (N)')
ylabel('Lift (N)')
fontsize(gca, 16, "points")
fontname('Times New Roman')


%% Thrust

x_power=linspace(0,length(Thrust_Power)/250,length(Thrust_Power))/(length(Thrust_Full)/500);
x_paddle=linspace(0,length(Thrust_Paddle)/250,length(Thrust_Paddle))/(length(Thrust_Full)/500);
x_full=linspace(0,length(Thrust_Full)/500,length(Thrust_Full))/(length(Thrust_Full)/500);

figure('Position', [10 10 200 150]);

hold on
plot(x_power,Thrust_Power,'color',gold,'LineWidth',3)
yline(mean(Thrust_Power),'--','color',gold,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off

figure('Position', [10 10 200 150]);

hold on
plot(x_paddle+max(x_power)-.05,Thrust_Paddle,'color',red,'LineWidth',3)
yline(mean(Thrust_Paddle),'--','color',red,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off

figure('Position', [10 10 200 150]);

hold on
plot(x_full,Thrust_Full,'color',purple,'LineWidth',3)
yline(mean(Thrust_Full),'--','color',purple,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off

%% Lift

figure('Position', [10 10 200 150]);

hold on
plot(x_power,Lift_Power,'color',gold,'LineWidth',3)
yline(mean(Lift_Power),'--','color',gold,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off


figure('Renderer', 'painters', 'Position', [10 10 200 150]);

hold on
plot(x_paddle+max(x_power)-.1,Lift_Paddle,'color',red,'LineWidth',3)
yline(mean(Lift_Paddle),'--','color',red,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off


figure('Position', [10 10 200 150]);

hold on
plot(x_full,Lift_Full,'color',purple,'LineWidth',3)
yline(mean(Lift_Full),'--','color',purple,'LineWidth',2)
yline(0,'k')
ylim([lower_bound upper_bound])
xlim([0 1])
yticks(-4:2:4)
yticklabels({'-4','-2','0','2','4'})

fontsize(gca, 16, "points")
fontname('Times New Roman')

hold off


