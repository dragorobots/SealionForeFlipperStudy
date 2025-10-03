#!/usr/bin/env python3
"""
Run the Power-stroke conversion without any shell features.

Usage:
  python analysis/power/run_power_convert.py
"""

import os
import sys
import traceback
from datetime import datetime

# Add the project root to Python path so we can import analysis modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.power.power_to_hdf5 import process_files


def main() -> int:
    roots = [
        os.path.join('data', 'raw', 'Master_Data_Set_Backup', '07-Oct-2022_results_PowerStroke.mat'),
        os.path.join('data', 'raw', 'Master_Data_Set_Backup', '14-Oct-2022_results_PowerStroke.mat'),
    ]

    missing = [p for p in roots if not os.path.exists(p)]
    if missing:
        print('Missing raw files:')
        for m in missing:
            print('  ', m)
        return 2

    out_dir = os.path.join('data', 'processed', 'Power')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'PowerTraces_Complete_{datetime.now():%Y-%m-%d}.h5')

    try:
        process_files(roots, out_path, resample_n=1001)
        print('WROTE:', out_path)
        return 0
    except Exception:
        print('Conversion failed:')
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())


