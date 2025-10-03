#!/usr/bin/env python3
"""
Power stroke RAW .mat inspector

Purpose:
  - Quickly introspect the structure of Power stroke MATLAB files so we can
    wire the align → mean → HDF5 pipeline with the correct field mappings.

Usage:
  python analysis/power/inspect_power_mat.py \
    data/raw/Master_Data_Set_Backup/07-Oct-2022_results_PowerStroke.mat \
    data/raw/Master_Data_Set_Backup/14-Oct-2022_results_PowerStroke.mat

Notes:
  - Tries scipy.io.loadmat first (MAT v5). If the file is MAT v7.3 (HDF5),
    falls back to h5py to list groups/datasets.
  - Prints a concise summary: top-level keys, array shapes/dtypes, and a peek
    into likely fields (thrust, lift, time, params/metadata).
"""

import sys
import os
from typing import Any

def print_header(path: str) -> None:
    print("\n=== Inspecting:", path)
    print("Exists:", os.path.exists(path))

def try_scipy(path: str) -> bool:
    try:
        import scipy.io as sio  # type: ignore
    except Exception as e:
        print("scipy not available:", e)
        return False
    try:
        md = sio.whosmat(path)
        print("SCIPY whosmat (first 10):", md[:10])
        d = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
        keys = [k for k in d.keys() if not k.startswith('__')]
        print("TOP_KEYS:", keys)
        # summarize
        for k in keys:
            v = d[k]
            try:
                shape = getattr(v, 'shape', None)
                dtype = getattr(v, 'dtype', None)
                if shape is not None and dtype is not None:
                    print(f"  ARR {k}: shape={shape}, dtype={dtype}")
                else:
                    print(f"  {k}: type={type(v)}")
            except Exception:
                print(f"  {k}: type={type(v)}")
        # quick candidates
        for cand in [
            'thrust','lift','force','Force','Lift','Thrust',
            'time','Time','t','params','Parameters','meta','experiment','experiments']:
            if cand in d:
                vv = d[cand]
                print(f"CAND '{cand}' → type={type(vv)}")
        return True
    except Exception as e:
        print("SCIPY load failed:", e)
        return False

def try_h5py(path: str) -> bool:
    try:
        import h5py  # type: ignore
    except Exception as e:
        print("h5py not available:", e)
        return False
    try:
        with h5py.File(path, 'r') as f:
            def walk(name: str, obj: Any):
                if isinstance(obj, h5py.Dataset):
                    print(f"  DS  {name}: shape={obj.shape}, dtype={obj.dtype}")
                elif isinstance(obj, h5py.Group):
                    print(f"  GRP {name}")
            print("HDF5 groups/datasets:")
            f.visititems(walk)
        return True
    except Exception as e:
        print("H5PY open failed:", e)
        return False

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python analysis/power/inspect_power_mat.py <file.mat> [file2.mat ...]")
        return 2
    for p in argv[1:]:
        print_header(p)
        if not os.path.exists(p):
            continue
        ok = try_scipy(p)
        if not ok:
            _ = try_h5py(p)
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv))



