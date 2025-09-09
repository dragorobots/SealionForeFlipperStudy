# Repository Audit and Reorganization Tools

This directory contains tools for auditing and reorganizing the Sea Lion Fore Flipper Study repository.

## repo_audit_and_reorg.py

Main orchestrator script that performs comprehensive repository audit and optional reorganization.

### Usage

#### Dry Run (Recommended First)
```bash
python tools/repo_audit_and_reorg.py --plan-only
```

This will:
- Audit the entire repository
- Create a reorganization plan
- Generate all deliverables
- **NOT** make any changes to files

#### Apply Reorganization
```bash
python tools/repo_audit_and_reorg.py --apply
```

This will:
- Perform the audit
- Create the reorganization plan
- **Apply** all planned moves using `git mv` (if git repo) or `shutil.move`
- Update paths in affected files
- Generate all deliverables

#### Limited Processing (for testing)
```bash
python tools/repo_audit_and_reorg.py --limit 100 --plan-only
```

### Output Files

The script generates the following deliverables:

- **audit_report.md** - Comprehensive repository analysis
- **README.md** - Repository checkpoint documentation
- **reorg_plan.tsv** - Planned file moves (tab-separated)
- **reorg_log.tsv** - Log of applied moves (if --apply used)
- **repo_provenance.json** - Repository state snapshot
- **tests/** - Minimal test structure

### Safety Features

- **Dry run by default** - No changes unless `--apply` is specified
- **Git integration** - Uses `git mv` when possible to preserve history
- **Backup creation** - Creates `.bak` files before editing
- **Comprehensive logging** - All changes are logged with timestamps
- **Validation** - Checks file existence before moving

### Target Directory Structure

The reorganization follows this structure:

```
/src/helpers/                  # Shared, reusable helper functions
/src/pipeline/                 # Pipeline entrypoints and components
/analysis/good/                # Validated analysis scripts
/analysis/legacy/              # Old or ambiguous analyses
/data/raw/                     # Immutable raw experimental data
/data/processed/               # Analysis-ready datasets
/results/                      # Numerical results and tables
/figures/                      # Generated figures
/config/                       # Configuration files
/docs/                         # Documentation
/tests/                        # Test scripts
```

### Requirements

- Python 3.6+
- Git (optional, for history preservation)
- Access to repository files

### Troubleshooting

#### Permission Errors
Ensure you have write permissions to the repository directory.

#### Git Errors
If git commands fail, the script will fall back to regular file operations.

#### Path Issues
The script automatically creates target directories as needed.

### Example Workflow

1. **Initial Audit**:
   ```bash
   python tools/repo_audit_and_reorg.py --plan-only
   ```

2. **Review Plan**:
   ```bash
   cat reorg_plan.tsv
   ```

3. **Apply Changes**:
   ```bash
   python tools/repo_audit_and_reorg.py --apply
   ```

4. **Verify Results**:
   ```bash
   git status
   cat reorg_log.tsv
   ```

### Notes

- The script is idempotent - running it multiple times won't break the repository
- All moves are logged with timestamps
- Original file paths are preserved in comments when files are moved
- The script respects .gitignore and skips hidden files

