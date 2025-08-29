%% Results Worker single force trace
clc
clear all
close all
%%
load("23-Feb-2023_results_FullStroke.mat")

zeros=results.zeros.zeros*2.22; % convert to newtons
data=results.data.data*2.22; % convert to newtons
filtered_data=Data_Filters(data);
zeroed_data=filtered_data-mean(zeros(500:1000,:));
thr=zeroed_data(:,1);
lift=zeroed_data(:,2);
ard=data(:,3);
%%
first_skip=1000;

j=1;
zz=1;
on_flag=0;

mat=ard;
for i=first_skip:length(mat)-1
    p1=mat(i);
    p2=mat(i+1);
    if (p1-p2)<-1 && on_flag==0
        true_index(j)=i;
        on_flag=1;
        j=j+1;
    end

    if (p1-p2)>1 && on_flag==1
        true_index(j)=i;
        on_flag=0;
        j=j+1;
    end


end

%%
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
%%
clear traces_thr traces_lift lift2 thrust

z=1;
for j=1:2:10
j
    if j==1
        traces_thr(z,:)=thr(true_index(j):true_index(j+1));
        traces_lift(z,:)=lift(true_index(j):true_index(j+1));
        trace_length=length(traces_thr(z,:));
    else
        traces_thr(z,:)=thr(true_index(j):true_index(j)+trace_length-1);
        traces_lift(z,:)=lift(true_index(j):true_index(j)+trace_length-1);
        %                         hold on
        %                         plot(traces(z,:))
        %                         hold off
    end
    z=z+1
end


mean_traces_thr=mean(traces_thr);
%std_traces_thr=std(traces_thr)/sqrt(4);

mean_traces_lift=mean(traces_lift);
%std_traces_lift(jj,ii).period=std(traces_lift)/sqrt(4);

plot(mean_traces_thr)

%%
save('Robot_Forces_Learned_Traj','mean_traces_thr','mean_traces_lift')




