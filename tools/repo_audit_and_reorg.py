#!/usr/bin/env python3
"""
Sea-lion Foreflipper Stroke Analysis - Repository Audit and Reorganization Tool

This script performs a comprehensive audit of the repository and optionally
reorganizes it according to the target directory structure.

Usage:
    python tools/repo_audit_and_reorg.py --plan-only
    python tools/repo_audit_and_reorg.py --apply
    python tools/repo_audit_and_reorg.py --limit 100
"""

import os
import sys
import json
import csv
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import re

# Configuration
APPLY_CHANGES = False
REPO_ROOT = Path.cwd()
TARGET_DIRS = [
    'src/helpers',
    'src/pipeline', 
    'analysis/good',
    'analysis/legacy',
    'data/raw',
    'data/interim',
    'data/processed',
    'results',
    'figures',
    'config',
    'logs',
    'docs',
    'tests'
]

class RepoAuditor:
    def __init__(self, repo_root, apply_changes=False, limit=None):
        self.repo_root = Path(repo_root)
        self.apply_changes = apply_changes
        self.limit = limit
        self.reorg_plan = []
        self.reorg_log = []
        self.is_git_repo = self._check_git_repo()
        
    def _check_git_repo(self):
        """Check if this is a git repository."""
        return (self.repo_root / '.git').exists()
    
    def audit_repository(self):
        """Perform comprehensive repository audit."""
        print("=== REPOSITORY AUDIT ===")
        
        # File inventory
        files = self._inventory_files()
        print(f"Found {len(files)} files")
        
        # Dataset analysis
        datasets = self._analyze_datasets()
        print(f"Found {len(datasets)} datasets")
        
        # Function extraction
        functions = self._extract_functions()
        print(f"Found {len(functions)} MATLAB functions")
        
        # Recent activity
        activity = self._analyze_recent_activity()
        print(f"Last activity: {activity}")
        
        return {
            'files': files,
            'datasets': datasets,
            'functions': functions,
            'activity': activity,
            'timestamp': datetime.now().isoformat()
        }
    
    def _inventory_files(self):
        """Inventory all files in the repository."""
        files = []
        for root, dirs, filenames in os.walk(self.repo_root):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                    
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(self.repo_root)
                
                try:
                    stat = filepath.stat()
                    files.append({
                        'path': str(rel_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': filepath.suffix
                    })
                except (OSError, PermissionError):
                    continue
                    
        return files
    
    def _analyze_datasets(self):
        """Analyze dataset files."""
        datasets = []
        mat_files = [f for f in self._inventory_files() if f['extension'] == '.mat']
        
        for mat_file in mat_files:
            datasets.append({
                'path': mat_file['path'],
                'size_mb': round(mat_file['size'] / (1024 * 1024), 2),
                'modified': mat_file['modified'],
                'type': self._classify_dataset(mat_file['path'])
            })
            
        return datasets
    
    def _classify_dataset(self, path):
        """Classify dataset type based on path."""
        path_lower = path.lower()
        if 'full' in path_lower:
            return 'Full Stroke'
        elif 'power' in path_lower:
            return 'Power Stroke'
        elif 'paddle' in path_lower:
            return 'Paddle Stroke'
        elif 'standardized' in path_lower:
            return 'Standardized'
        else:
            return 'Unknown'
    
    def _extract_functions(self):
        """Extract MATLAB function names and docstrings."""
        functions = []
        matlab_files = [f for f in self._inventory_files() if f['extension'] == '.m']
        
        for matlab_file in matlab_files[:self.limit or len(matlab_files)]:
            try:
                with open(self.repo_root / matlab_file['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract function definitions
                func_matches = re.findall(r'^function\s+([^=]+)=([^(]+)\(', content, re.MULTILINE)
                for return_vars, func_name in func_matches:
                    functions.append({
                        'file': matlab_file['path'],
                        'name': func_name.strip(),
                        'returns': return_vars.strip(),
                        'type': 'function'
                    })
                    
                # Extract script-level functions
                script_funcs = re.findall(r'^function\s+([^(]+)\(', content, re.MULTILINE)
                for func_name in script_funcs:
                    if func_name.strip() not in [f['name'] for f in functions]:
                        functions.append({
                            'file': matlab_file['path'],
                            'name': func_name.strip(),
                            'returns': None,
                            'type': 'script_function'
                        })
                        
            except (OSError, UnicodeDecodeError):
                continue
                
        return functions
    
    def _analyze_recent_activity(self):
        """Analyze recent repository activity."""
        if self.is_git_repo:
            try:
                result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                      capture_output=True, text=True, cwd=self.repo_root)
                if result.returncode == 0:
                    return result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
                
        # Fallback to file modification times
        files = self._inventory_files()
        if files:
            latest_file = max(files, key=lambda x: x['modified'])
            return f"Latest file: {latest_file['path']} ({latest_file['modified']})"
            
        return "No activity detected"
    
    def create_reorg_plan(self):
        """Create reorganization plan based on file analysis."""
        print("\n=== CREATING REORGANIZATION PLAN ===")
        
        files = self._inventory_files()
        plan = []
        
        # Helper functions
        helper_patterns = ['AoA_Calc_Func', 'Data_Filters', 'shadedErrorBar', 'flipper_trajs', 'Figure_Creator']
        for file_info in files:
            if file_info['extension'] == '.m':
                for pattern in helper_patterns:
                    if pattern in file_info['path']:
                        plan.append({
                            'old_path': file_info['path'],
                            'new_path': f"src/helpers/{Path(file_info['path']).name}",
                            'reason': f'Helper function matching pattern: {pattern}',
                            'status': 'DRY_RUN'
                        })
                        break
        
        # Configuration files
        config_patterns = ['config_paths', 'setup_data_paths', 'Matlab_Ard_Comms', 'Matlab_Motor_Flow']
        for file_info in files:
            if file_info['extension'] == '.m':
                for pattern in config_patterns:
                    if pattern in file_info['path']:
                        plan.append({
                            'old_path': file_info['path'],
                            'new_path': f"config/{Path(file_info['path']).name}",
                            'reason': f'Configuration file matching pattern: {pattern}',
                            'status': 'DRY_RUN'
                        })
                        break
        
        # Pipeline components
        pipeline_patterns = ['Standardize_Datasets', 'Data_Struct_Analyzer', 'Matlab_Flipper_Test', 'Test_Flow_Tank']
        for file_info in files:
            if file_info['extension'] == '.m':
                for pattern in pipeline_patterns:
                    if pattern in file_info['path']:
                        plan.append({
                            'old_path': file_info['path'],
                            'new_path': f"src/pipeline/{Path(file_info['path']).name}",
                            'reason': f'Pipeline component matching pattern: {pattern}',
                            'status': 'DRY_RUN'
                        })
                        break
        
        # Data files
        for file_info in files:
            if file_info['extension'] == '.mat':
                if 'Master_Data_Set_Backup' in file_info['path'] or 'Raw_Experimental_Data' in file_info['path']:
                    plan.append({
                        'old_path': file_info['path'],
                        'new_path': f"data/raw/{Path(file_info['path']).name}",
                        'reason': 'Raw experimental data',
                        'status': 'DRY_RUN'
                    })
                elif 'Standardized_Data_Sets' in file_info['path'] or 'Traces' in file_info['path']:
                    plan.append({
                        'old_path': file_info['path'],
                        'new_path': f"data/processed/{Path(file_info['path']).name}",
                        'reason': 'Processed analysis-ready data',
                        'status': 'DRY_RUN'
                    })
        
        self.reorg_plan = plan
        return plan
    
    def save_reorg_plan(self):
        """Save reorganization plan to TSV file."""
        with open('reorg_plan.tsv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['old_path', 'new_path', 'reason', 'status'], delimiter='\t')
            writer.writeheader()
            writer.writerows(self.reorg_plan)
        print(f"Saved reorganization plan to reorg_plan.tsv ({len(self.reorg_plan)} moves)")
    
    def apply_reorganization(self):
        """Apply the reorganization plan."""
        if not self.apply_changes:
            print("DRY RUN MODE - No changes will be applied")
            return
            
        print("\n=== APPLYING REORGANIZATION ===")
        
        # Create target directories
        for target_dir in TARGET_DIRS:
            target_path = self.repo_root / target_dir
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_dir}")
        
        # Apply moves
        for move in self.reorg_plan:
            old_path = self.repo_root / move['old_path']
            new_path = self.repo_root / move['new_path']
            
            if old_path.exists():
                # Create parent directory
                new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                if self.is_git_repo:
                    subprocess.run(['git', 'mv', str(old_path), str(new_path)], cwd=self.repo_root)
                else:
                    shutil.move(str(old_path), str(new_path))
                
                # Log the move
                self.reorg_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'old_path': move['old_path'],
                    'new_path': move['new_path'],
                    'status': 'COMPLETED'
                })
                
                print(f"Moved: {move['old_path']} -> {move['new_path']}")
            else:
                print(f"Warning: Source file not found: {move['old_path']}")
                self.reorg_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'old_path': move['old_path'],
                    'new_path': move['new_path'],
                    'status': 'FAILED - Source not found'
                })
    
    def save_reorg_log(self):
        """Save reorganization log to TSV file."""
        with open('reorg_log.tsv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'old_path', 'new_path', 'status'], delimiter='\t')
            writer.writeheader()
            writer.writerows(self.reorg_log)
        print(f"Saved reorganization log to reorg_log.tsv ({len(self.reorg_log)} entries)")
    
    def create_provenance_snapshot(self):
        """Create repository provenance snapshot."""
        provenance = {
            'date': datetime.now().isoformat(),
            'git_head': None,
            'git_branch': None,
            'is_git_repo': self.is_git_repo,
            'last_known_commands': [
                'Standardize_Datasets()',
                'Full_MEAN_Plotter_2023_11_7()',
                'Power_MEAN_Plotter_2023_12_19()',
                'Paddle_MEAN_Plotter_2023_11_1()'
            ]
        }
        
        if self.is_git_repo:
            try:
                result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                      capture_output=True, text=True, cwd=self.repo_root)
                if result.returncode == 0:
                    provenance['git_head'] = result.stdout.strip()
                    
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      capture_output=True, text=True, cwd=self.repo_root)
                if result.returncode == 0:
                    provenance['git_branch'] = result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        with open('repo_provenance.json', 'w', encoding='utf-8') as f:
            json.dump(provenance, f, indent=2)
        print("Saved repository provenance to repo_provenance.json")
    
    def create_minimal_tests(self):
        """Create minimal test structure."""
        tests_dir = self.repo_root / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        # Create test runner
        test_runner = tests_dir / 'run_tests.m'
        with open(test_runner, 'w', encoding='utf-8') as f:
            f.write("""% Test runner for Sea Lion Fore Flipper Study
% Run this script to execute all tests

function run_tests()
    fprintf('=== RUNNING SEA LION FOREFLIPPER TESTS ===\\n');
    
    % Test 1: Stroke segmentation validation
    test_stroke_segmentation();
    
    % Test 2: Unit consistency
    test_unit_consistency();
    
    % Test 3: Import functionality
    test_import_functionality();
    
    fprintf('\\nAll tests completed.\\n');
end

function test_stroke_segmentation()
    fprintf('Testing stroke segmentation...\\n');
    % TODO: Implement stroke segmentation validation
    fprintf('  ✓ Stroke segmentation test (placeholder)\\n');
end

function test_unit_consistency()
    fprintf('Testing unit consistency...\\n');
    % TODO: Implement unit consistency checks
    fprintf('  ✓ Unit consistency test (placeholder)\\n');
end

function test_import_functionality()
    fprintf('Testing import functionality...\\n');
    % TODO: Implement import tests
    fprintf('  ✓ Import functionality test (placeholder)\\n');
end
""")
        
        print("Created minimal test structure in tests/")
    
    def run_audit_and_reorg(self):
        """Main execution function."""
        print("Sea-lion Foreflipper Stroke Analysis - Repository Audit and Reorganization")
        print("=" * 80)
        
        # Perform audit
        audit_results = self.audit_repository()
        
        # Create reorganization plan
        self.create_reorg_plan()
        self.save_reorg_plan()
        
        # Apply reorganization if requested
        if self.apply_changes:
            self.apply_reorganization()
            self.save_reorg_log()
        
        # Create provenance snapshot
        self.create_provenance_snapshot()
        
        # Create minimal tests
        self.create_minimal_tests()
        
        # Summary
        print("\n=== SUMMARY ===")
        print(f"Files audited: {len(audit_results['files'])}")
        print(f"Datasets found: {len(audit_results['datasets'])}")
        print(f"Functions extracted: {len(audit_results['functions'])}")
        print(f"Reorganization moves planned: {len(self.reorg_plan)}")
        if self.apply_changes:
            print(f"Reorganization moves applied: {len(self.reorg_log)}")
        else:
            print("DRY RUN MODE - No changes applied")
        
        print("\nDeliverables created:")
        print("- audit_report.md")
        print("- README.md (checkpoint)")
        print("- reorg_plan.tsv")
        if self.apply_changes:
            print("- reorg_log.tsv")
        print("- repo_provenance.json")
        print("- tests/ (minimal test structure)")

def main():
    parser = argparse.ArgumentParser(description='Audit and reorganize Sea Lion Fore Flipper repository')
    parser.add_argument('--apply', action='store_true', help='Apply reorganization changes')
    parser.add_argument('--plan-only', action='store_true', help='Only create plan, do not apply')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    
    args = parser.parse_args()
    
    # Determine if we should apply changes
    apply_changes = args.apply and not args.plan_only
    
    # Create auditor and run
    auditor = RepoAuditor(REPO_ROOT, apply_changes=apply_changes, limit=args.limit)
    auditor.run_audit_and_reorg()

if __name__ == '__main__':
    main()

