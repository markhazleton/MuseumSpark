# Cleanup and Maintenance Guide

## Project Organization

This document describes the cleanup performed on January 18, 2026, and provides guidelines for maintaining a clean workspace.

## Recent Cleanup Actions

### 1. Archived Old Test Runs
- **Location**: `data/runs/` → `data/archive/old_runs_20260116-20260117/`
- **Action**: Moved 200+ dated run folders from January 16-17, 2026
- **Reason**: Historical test runs that are no longer actively needed but preserved for reference

### 2. Consolidated Temp Files
- **Location**: `_archive_temp_files/` → `data/archive/temp_files_archive/`
- **Action**: Moved temporary files archive to proper archive location
- **Contents**: State comparison files (Alaska, Alabama) and temp museum data

### 3. Removed Deprecated Scripts
- **Location**: `scripts/_archive_legacy_DEPRECATED_2026-01-17/`
- **Action**: Permanently deleted deprecated legacy test scripts
- **Reason**: Marked as deprecated on 2026-01-17, no longer needed

### 4. Updated .gitignore
- **Added patterns**:
  - `data/runs/` - Test run outputs
  - `data/archive/old_runs_*/` - Archived runs
  - `temp_*.txt` and `temp_*.json` - Temporary files
  - `**/temp/` - Temporary directories
  - `**/*_temp_*/` - Directories with temp in name

## Directory Structure for Archives

```
data/
  archive/
    temp_files_archive/       # Historical temp files
    old_runs_20260116-20260117/  # Historical test runs
  cache/                     # Runtime cache (gitignored)
  runs/                      # Active test runs (gitignored)
```

## Maintenance Guidelines

### When to Archive
- **Test Runs**: Archive runs older than 7 days to `data/archive/old_runs_[date-range]/`
- **Temp Files**: Move temp files to `data/archive/temp_files_archive/` when no longer needed
- **Cache**: Cache files are automatically regenerated and should stay gitignored

### When to Delete
- **Deprecated Scripts**: Delete immediately after archiving if marked DEPRECATED
- **Old Archives**: Consider deleting archives older than 90 days if no historical value
- **Cache**: Can be safely deleted anytime (will regenerate as needed)

### Regular Cleanup Tasks
1. **Weekly**: Check `data/runs/` and archive old runs
2. **Monthly**: Review `data/archive/` and remove very old files
3. **As Needed**: Clear `data/cache/` to free disk space

## File Naming Conventions

**Avoid:**
- `temp_*` prefix for files you want to keep
- Dated folders in active directories (use archive for historical data)
- Test scripts in main scripts directory (use tests/ subdirectory)

**Prefer:**
- Descriptive names for persistent files
- Archive dated folders in `data/archive/`
- Clear separation between active and archived content

## Git Patterns

The following are gitignored to prevent accidental commits:
- All temp files matching `temp_*.txt`, `temp_*.json`
- Test run outputs in `data/runs/`
- Cache directories under `data/cache/`
- Archive directories under `data/archive/old_runs_*/`

## Questions?

If you're unsure whether to keep, archive, or delete something:
1. Check if it's actively used in scripts or documentation
2. Look for DEPRECATED or temp markers in names
3. Consider if historical value exists (archive) or not (delete)
4. When in doubt, archive first rather than delete
