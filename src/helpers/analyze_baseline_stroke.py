#!/usr/bin/env python3
"""
Analyze baseline stroke to determine optimal cutoff frequency
Baseline: Period 2.25s, Yaw -70°, Roll -45°, Paddle 0.5
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import medfilt, firwin, filtfilt
from scipy.fft import fft, fftfreq
import os

def analyze_baseline_stroke():
    """Analyze baseline stroke to determine optimal cutoff frequency"""
    
    # Find the dataset file
    processed_dir = "data/processed"
    h5_files = []
    for root, dirs, files in os.walk(processed_dir):
        for file in files:
            if file.startswith("FullStroke_Complete") and file.endswith(".h5"):
                h5_files.append(os.path.join(root, file))
    
    if not h5_files:
        print("❌ No FullStroke_Complete.h5 files found!")
        return
    
    h5_file = sorted(h5_files)[-1]
    print(f"🔍 ANALYZING BASELINE STROKE")
    print(f"📁 File: {os.path.basename(h5_file)}")
    print("=" * 60)
    
    # Baseline parameters
    target_period = 2.25
    target_yaw = -70.0
    target_roll = -45.0
    target_paddle = 0.5
    
    print(f"🎯 Target Parameters:")
    print(f"   Period: {target_period}s")
    print(f"   Yaw: {target_yaw}°")
    print(f"   Roll: {target_roll}°")
    print(f"   Paddle: {target_paddle}")
    print()
    
    with h5py.File(h5_file, 'r') as f:
        # Load data structure
        data_group = f['data']
        zeros_group = f['zeros']
        params_group = f['parameters']
        
        # Get all experiment keys
        experiment_keys = sorted(data_group.keys(), key=lambda x: int(x.split('_')[1]))
        
        # Find baseline experiment
        baseline_idx = None
        for i, key in enumerate(experiment_keys):
            params = params_group[key][:]
            period = float(params[0,0])
            yaw = float(params[1,0])
            roll = float(params[2,0])
            paddle = float(params[3,0])
            
            if (abs(period - target_period) < 1e-6 and
                abs(yaw - target_yaw) < 1e-6 and
                abs(roll - target_roll) < 1e-6 and
                abs(paddle - target_paddle) < 1e-6):
                baseline_idx = i
                print(f"✅ Found baseline experiment: {key} (index {i})")
                break
        
        if baseline_idx is None:
            print("❌ Baseline experiment not found!")
            return
        
        # Load baseline data
        baseline_key = experiment_keys[baseline_idx]
        raw_data = data_group[baseline_key][:]  # Shape: (3, 15000)
        zeros_data = zeros_group[baseline_key][:]  # Shape: (3, 15000)
        
        print(f"📊 Baseline Data Shape: {raw_data.shape}")
        print(f"📊 Time Points: {raw_data.shape[1]:,}")
        print(f"📊 Duration: {raw_data.shape[1]/500:.1f} seconds")
        print()
        
        # Apply zero correction
        zero_thrust_mean = zeros_data[0, :].mean()  # Thrust channel
        zero_lift_mean = zeros_data[1, :].mean()    # Lift channel
        
        corrected_data = raw_data.copy()
        corrected_data[0, :] -= zero_thrust_mean  # Thrust
        corrected_data[1, :] -= zero_lift_mean    # Lift
        # Arduino (index 2) remains unchanged
        
        # Scale by 2.22
        scaled_data = corrected_data * 2.22
        
        # Apply median filter
        median_filtered = np.zeros_like(scaled_data)
        for i in range(min(scaled_data.shape)):
            median_filtered[i, :] = medfilt(scaled_data[i, :], kernel_size=11)
        
        # Analyze frequency content
        print("🔍 FREQUENCY ANALYSIS:")
        print("=" * 40)
        
        # Parameters for analysis
        fs = 500  # Sampling rate
        N = scaled_data.shape[1]  # Number of samples
        time = np.arange(N) / fs
        
        # Analyze each channel
        channels = ['Thrust', 'Lift', 'Arduino']
        colors = ['blue', 'red', 'green']
        
        # Calculate FFT for each channel
        for i, (channel, color) in enumerate(zip(channels, colors)):
            signal = median_filtered[i, :]
            
            # FFT analysis
            fft_signal = fft(signal)
            freqs = fftfreq(N, 1/fs)
            
            # Only positive frequencies
            positive_freqs = freqs[:N//2]
            positive_fft = np.abs(fft_signal[:N//2])
            
            # Find dominant frequencies
            # Exclude DC component (freq=0)
            analysis_freqs = positive_freqs[1:]
            analysis_fft = positive_fft[1:]
            
            # Find peaks
            peak_indices = []
            for j in range(1, len(analysis_fft)-1):
                if (analysis_fft[j] > analysis_fft[j-1] and 
                    analysis_fft[j] > analysis_fft[j+1] and
                    analysis_fft[j] > np.max(analysis_fft) * 0.1):  # At least 10% of max
                    peak_indices.append(j)
            
            # Get top 5 peaks
            if peak_indices:
                peak_values = analysis_fft[peak_indices]
                top_peaks = np.argsort(peak_values)[-5:][::-1]  # Top 5, descending
                
                print(f"\n{channel} Channel:")
                print(f"  Top frequency components:")
                for k, peak_idx in enumerate([peak_indices[i] for i in top_peaks]):
                    freq = analysis_freqs[peak_idx]
                    magnitude = analysis_fft[peak_idx]
                    print(f"    {k+1}. {freq:.2f} Hz (magnitude: {magnitude:.2f})")
                
                # Suggest cutoff frequency (2-3x the highest significant frequency)
                if len(top_peaks) > 0:
                    highest_freq = analysis_freqs[peak_indices[top_peaks[0]]]
                    suggested_cutoff = highest_freq * 2.5
                    print(f"  💡 Suggested cutoff: {suggested_cutoff:.1f} Hz (2.5x highest peak)")
        
        print("\n" + "=" * 60)
        print("📈 RECOMMENDATIONS:")
        print("=" * 60)
        
        # Analyze stroke frequency
        stroke_period = 2.25  # seconds
        stroke_freq = 1 / stroke_period
        print(f"🎯 Stroke frequency: {stroke_freq:.3f} Hz (period: {stroke_period}s)")
        
        # Common cutoff frequency recommendations
        print(f"\n💡 Cutoff frequency recommendations:")
        print(f"   • 2x stroke frequency: {stroke_freq * 2:.1f} Hz")
        print(f"   • 3x stroke frequency: {stroke_freq * 3:.1f} Hz")
        print(f"   • 5x stroke frequency: {stroke_freq * 5:.1f} Hz")
        print(f"   • 10x stroke frequency: {stroke_freq * 10:.1f} Hz")
        
        # Nyquist frequency
        nyquist = fs / 2
        print(f"\n📊 Sampling info:")
        print(f"   • Sampling rate: {fs} Hz")
        print(f"   • Nyquist frequency: {nyquist} Hz")
        print(f"   • Maximum safe cutoff: {nyquist * 0.8:.1f} Hz (80% of Nyquist)")
        
        # Final recommendation
        recommended_cutoff = min(stroke_freq * 5, nyquist * 0.8)
        print(f"\n🎯 RECOMMENDED CUTOFF: {recommended_cutoff:.1f} Hz")
        print(f"   (5x stroke frequency, but not exceeding 80% of Nyquist)")
        
        # Show data statistics
        print(f"\n📊 Data Statistics (after zero correction and scaling):")
        for i, channel in enumerate(channels):
            signal = median_filtered[i, :]
            print(f"   {channel}: Min={signal.min():.3f}, Max={signal.max():.3f}, "
                  f"Mean={signal.mean():.3f}, Std={signal.std():.3f}")

if __name__ == "__main__":
    analyze_baseline_stroke()
