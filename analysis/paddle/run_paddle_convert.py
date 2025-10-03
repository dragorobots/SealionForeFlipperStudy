#!/usr/bin/env python3
"""
Wrapper script to run Paddle stroke conversion without complex shell commands.
"""

import os
import sys

# Add the project root to Python path so we can import analysis modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.paddle.paddle_to_hdf5 import process_files


def main() -> int:
    roots = [
        os.path.join('data', 'raw', 'Master_Data_Set_Backup', '19-Oct-2022_results_PaddleStroke.mat'),
        os.path.join('data', 'raw', 'Raw_Experimental_Data', '19-Oct-2022_Paddle_Stroke_Flipper_Results', '19-Oct-2022_results_PaddleStroke.mat'),
        os.path.join('data', 'raw', 'Raw_Experimental_Data', '27-Oct-2022_Power_Stroke_Flipper_Results', '27-Oct-2022_results_PaddleStroke.mat')
    ]
    
    out_path = os.path.join('data', 'processed', 'Paddle', 'PaddleTraces_Complete_2025-09-19.h5')
    
    try:
        process_files(roots, out_path, resample_n=1001)
        print(f"WROTE: {out_path}")
        return 0
    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
