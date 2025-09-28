# Home Assistant Helper Analysis and Cleanup - Complete Guide

This package provides comprehensive helper analysis and safe deletion tools for Home Assistant using PyScript.

## 📋 Prerequisites

1. **Install PyScript via HACS:**
   - HACS → Integrations → Search "PyScript" → Install

2. **Configure PyScript in configuration.yaml:**
   ```yaml
   pyscript:
     allow_all_imports: true
     hass_is_global: true
   ```

3. **Restart Home Assistant**

4. **Create directory structure:**
   ```
   /config/pyscript/
   ├── analyze_helpers.py    # Main analysis script
   └── delete_helpers.py     # Safe deletion script
   ```

## 🚀 Usage Workflow

### Step 1: Run Analysis
```yaml
# Developer Tools → Services
service: pyscript.analyze_helpers
```

This creates files in `/config/helper_analysis/`:
- `orphaned_helpers_YYYYMMDD_HHMMSS.txt` - **Editable list for deletion**
- `helper_analysis_full_YYYYMMDD_HHMMSS.json` - Complete analysis data
- `helper_analysis_summary_YYYYMMDD_HHMMSS.txt` - Human-readable report

### Step 2: Review and Edit Deletion List
1. Open `/config/helper_analysis/orphaned_helpers_[timestamp].txt`
2. **Remove lines for helpers you want to KEEP**
3. Save the file
4. Only remaining helpers will be deleted

Example file content:
```
# Potentially Orphaned Helpers - Safe to Delete List
# Instructions: Remove any lines for helpers you want to KEEP

input_boolean.old_automation_flag  # Old automation flag - State: off
input_text.unused_message         # Unused message - State: 
counter.test_counter              # Test counter - State: 0
# input_number.important_setting   # ← COMMENTED OUT = WILL BE KEPT
```

### Step 3: Safe Deletion (Dry Run First)
```yaml
# Developer Tools → Services
service: pyscript.delete_helpers
data:
  dry_run: true  # Shows what WOULD be deleted without actually deleting
```

### Step 4: Actual Deletion
```yaml
# Developer Tools → Services  
service: pyscript.delete_helpers
data:
  dry_run: false  # Performs actual deletion
```

## 🛡️ Safety Features

### Automatic Backups
- Every deletion creates a backup file with original states
- Backup includes all helper configurations and states
- Backups stored in `/config/helper_analysis/deletion_backup_[timestamp].json`

### Comprehensive Logging
- All operations logged to Home Assistant logs
- Detailed reports written to files
- Clear success/failure tracking

### Dry Run Mode
- Default mode shows what would be deleted
- No actual changes until explicitly confirmed
- Review all changes before committing

### Validation
- Verifies helper existence before deletion
- Validates entity ID formats
- Handles missing/already deleted helpers gracefully

## 📊 Analysis Capabilities

### Helper Detection
- Traditional helpers: `input_*`, `counter.*`, `timer.*`, `variable.*`
- Template sensors and binary sensors
- Custom helper integrations

### Reference Scanning
- **YAML Configuration Files:** `automations.yaml`, `scripts.yaml`, `scenes.yaml`
- **Package Files:** All YAML files in `/config/packages/`
- **Template Analysis:** Full Jinja2 template parsing with regex
- **Entity References:** Direct entity IDs and template functions
- **Naming Patterns:** Related entity detection

### Analysis Techniques (Spook-Inspired)
- Direct configuration file scanning
- Template entity extraction using regex patterns
- Entity relationship analysis  
- Automation/script name correlation
- Reference scoring for confidence levels

## 📁 File Structure

```
/config/
├── helper_analysis/                    # Results directory
│   ├── orphaned_helpers_[timestamp].txt      # ← EDIT THIS FILE
│   ├── helper_analysis_full_[timestamp].json
│   ├── helper_analysis_summary_[timestamp].txt
│   ├── deletion_backup_[timestamp].json      # Auto-created on deletion
│   └── deletion_report_[timestamp].txt       # Auto-created on deletion
└── pyscript/
    ├── analyze_helpers.py             # Main analysis script
    └── delete_helpers.py              # Safe deletion script
```

## 🔧 Advanced Usage

### Custom Analysis
```yaml
# Analyze helpers (standard)
service: pyscript.analyze_helpers

# Delete with specific file
service: pyscript.delete_helpers
data:
  dry_run: false
  orphaned_file: "/config/helper_analysis/orphaned_helpers_20250927_143022.txt"
```

### Emergency Restore
```yaml
# View backup information (limited restore capability)
service: pyscript.restore_helpers
data:
  backup_file: "/config/helper_analysis/deletion_backup_20250927_143022.json"
```

**Note:** Full restoration requires manual reconfiguration as helper creation needs original parameters.

## ⚠️ Important Notes

### Template Sensors
- Cannot be auto-deleted (require configuration file changes)
- Analysis identifies them but deletion must be manual
- Remove from `template:` section in YAML configuration

### Helper Types Supported for Deletion
- ✅ `input_boolean` - Toggles and flags
- ✅ `input_text` - Text inputs  
- ✅ `input_number` - Number sliders
- ✅ `input_select` - Dropdown lists
- ✅ `input_datetime` - Date/time pickers
- ✅ `counter` - Counters
- ✅ `timer` - Timers
- ⚠️ `sensor/binary_sensor` (template) - Manual deletion required

### Backup Limitations
- Backups preserve states and attributes
- Cannot automatically recreate deleted helpers
- Manual reconfiguration required for restoration
- Keep original configuration files as primary backup

## 🔍 Troubleshooting

### Analysis Issues
- Check PyScript configuration in `configuration.yaml`
- Verify `/config/helper_analysis/` directory permissions
- Review Home Assistant logs for detailed error messages

### Deletion Issues  
- Some helpers may require Home Assistant restart after deletion
- Template sensors must be removed from YAML configuration manually
- Check entity registry for orphaned references

### Performance
- Large configurations may take several minutes to analyze
- Analysis processes all YAML files recursively
- Results cached in files for repeated access

## 📝 Example Output

### Analysis Summary
```
SUMMARY:
  Total Helpers: 47
  Traditional Helpers: 31  
  Template Sensors: 16
  Referenced Helpers: 39
  Potentially Orphaned: 8
```

### Deletion Report
```
SUMMARY:
  Requested Deletions: 5
  Successful Deletions: 4
  Failed Deletions: 1

SUCCESSFULLY DELETED:
  ✓ input_boolean.old_flag
  ✓ input_text.unused_message
  ✓ counter.test_counter
  ✓ timer.old_timer

FAILED DELETIONS:
  ✗ sensor.template_helper - requires manual config removal
```

This system provides the most comprehensive helper analysis available, rivaling commercial tools while maintaining complete safety and control over your Home Assistant configuration.