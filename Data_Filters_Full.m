function Filtered_data=Data_Filters_Full(data)

CF=4;
Fs=500;

Wn=(2/Fs)*CF;
b = fir1(1000,Wn,'low',kaiser(1001,1));

for i=1:min(size(data))
    Median_filtered(:,i)=medfilt1(data(:,i),5);
    low_pass_filtered(:,i)=filtfilt(b,1,Median_filtered(:,i));
end
Filtered_data=low_pass_filtered;
end

% look at the fourier spectrum 