clear
clc
close all

load("ard.mat")



%% Align Traces
first_skip=700;
k=1;
j=1;
ep=1;
sp=1;
mat=ard(k,:);


for i=first_skip:length(mat)-1

    p1=mat(i);
    p2=mat(i+1);
    new(i)=p2-p1;

    if logical(mod(j,2))
        if p2-p1 >= 1 && (i-ep)>200
            true_index(k,j)=i;
            j=j+1;
            sp=i;
        end
    end
    
    
    if logical(~mod(j,2))
        
        if p2-p1 <= -1 && (i-sp)>50
            true_index(k,j)=i;
            j=j+1;
            ep=i;
        end
    end
end

%%

%% Align Traces
first_skip=700;
k=1;
j=1;
ep=1;
sp=1;
mat=ard(k,:);


for i=first_skip:length(mat)-1

    p1=mat(i);
    p2=mat(i+1);
    new(i)=p2-p1;

    if logical(mod(j,2))
        disp('here1')
        j=j+1;

    end
    
    
    if logical(~mod(j,2))
        disp('here')
        j=j+1;

    end
end



