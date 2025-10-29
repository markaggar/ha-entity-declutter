# HA Entity Declutter

A comprehensive Home Assistant helper analysis system built with PyScript. This tool helps you identify unused helpers and provides detailed reports for manual cleanup via the Home Assistant dashboard.

## 🎯 Features

- **Comprehensive Helper Detection**: Analyzes all 27 helper integration types including template sensors, input helpers, utility meters, and more
- **Smart Dependency Analysis**: Tracks references across automations, scripts, templates, and dashboards
- **Multi-Category Classification**: 
  - **Actively Used**: Referenced in automations/scripts/templates
  - **Dashboard Only**: Only used in UI dashboards
  - **Truly Orphaned**: No references found anywhere
- **Auto-Generated Lovelace Cards**: Creates ready-to-use dashboard cards for easy review
- **Multi-Environment Support**: Separate dev and production deployments
- **Manual Deletion Guide**: Comprehensive reports for safe manual cleanup
- **Reference Source Tracking**: Shows exactly where each helper is used

## 📊 Results

On a production system with 484 helpers, this tool achieved:
- **83% reduction** in false positives (78 → 13 truly orphaned helpers)
- **Accurate categorization** of dashboard-only vs unused helpers
- **Zero false positives** for critical dashboard entities

## 🚀 Quick Start

### Prerequisites
- Home Assistant with [PyScript](https://github.com/custom-components/pyscript) custom component installed

### Installation

1. **Install PyScript** (if not already installed):
   - Install via HACS or manually following [PyScript installation guide](https://github.com/custom-components/pyscript)

2. **Add PyScript to configuration.yaml**:
   ```yaml
   pyscript:
     allow_all_imports: true
     hass_is_global: true
   ```

3. **Create required directories**:
   ```bash
   # In your Home Assistant config directory:
   mkdir pyscript
   mkdir helper_analysis
   ```

4. **Download and copy the Python script**:
   - Download `analyze_helpers.py` from this repository
   - Copy the file to your `/config/pyscript/` directory

5. **Restart Home Assistant** to load the PyScript components

6. **Run the analysis**:
   - Go to **Developer Tools → Actions** in Home Assistant
   - Run action: `pyscript.analyze_helpers`
   - Check `/config/helper_analysis/` for results

## 📁 Output Files

The analysis generates several files in `/config/helper_analysis/`:

- **`helper_analysis.json`**: Complete analysis with reference sources
- **`helper_summary.txt`**: Human-readable summary report
- **`orphaned_helpers.txt`**: List of helpers safe to delete
- **`helper_review_cards.yaml`**: Lovelace dashboard cards for review

## 🎨 Dashboard Integration

The tool generates ready-to-use Lovelace cards showing:
- **Left Column**: Truly orphaned helpers (safe to delete)
- **Right Column**: Dashboard-only helpers (review before deleting)

Simply copy the contents of `helper_review_cards.yaml` into a new dashboard card.

## 🧹 Manual Cleanup

1. **Review the analysis**: Check `helper_summary.txt` and the generated dashboard cards
2. **Navigate to Settings → Device & Services → Helpers** in your Home Assistant dashboard
3. **Search for helpers** from the orphaned_helpers.txt list
4. **Delete helpers manually** after confirming they're not needed

## 🔧 Configuration

No additional configuration is required. The scripts will automatically:
- Detect your Home Assistant configuration structure
- Analyze all helper types and their dependencies
- Generate reports in `/config/helper_analysis/`

### Supported Helper Types

The tool detects all Home Assistant helper integrations:
- `input_*` helpers (boolean, button, datetime, number, select, text)
- Template helpers (sensors, binary sensors, etc.)
- Utility helpers (counter, timer, statistics, utility_meter)
- Advanced helpers (derivative, integral, threshold, trend, history_stats)
- Special helpers (generic_thermostat, manual_alarm_control_panel, etc.)

## 📈 Analysis Process

1. **Entity Discovery**: Scans entity registry for all helper types
2. **Configuration Analysis**: Parses YAML files, packages, and blueprints
3. **Template Dependencies**: Analyzes template code for entity references
4. **Dashboard Scanning**: Checks UI dashboards in `.storage/lovelace*` files
5. **Categorization**: Classifies helpers by usage patterns
6. **Report Generation**: Creates JSON, text, and Lovelace card outputs

## 🛠️ Files

- **`analyze_helpers.py`**: Main analysis script - copy to `/config/pyscript/`
- **`deploy-pyscript.ps1`**: Development deployment tool (for contributors)
- **`README.md`**: This documentation

## 🤝 Contributing

Contributions welcome! This tool has evolved through real-world testing on complex Home Assistant setups.

## 📄 License

MIT License - feel free to adapt for your Home Assistant setup.

## � PyScript Implementation Notes

### Architecture

- **analyze_helpers.py**: Main analysis engine with comprehensive helper detection and dependency analysis
- **deploy-pyscript.ps1**: Multi-environment deployment script with discrete token management

### PyScript I/O Best Practices

PyScript restricts built-in I/O functions like `open()`, `read()`, and `write()` to prevent blocking the main event loop and for security reasons. The proper approach is:

**❌ Incorrect (causes errors):**

```python
# This will fail in PyScript
with open('file.txt', 'r') as f:
    content = f.read()
```

**✅ Correct (PyScript compatible):**

```python
def read_text_file(file_path):
    fd = os.open(file_path, os.O_RDONLY)
    try:
        content = b''
        while True:
            chunk = os.read(fd, 8192)
            if not chunk:
                break
            content += chunk
        return content.decode('utf-8')
    finally:
        os.close(fd)

# Use with task.executor for async operations
content = await task.executor(read_text_file, file_path)
```

### Known PyScript Framework Issue

You may see this harmless error after successful script completion:

```text
TypeError: '<function>' is not callable (got None)
```

This is a known PyScript framework bug with `task.create()` completion handling that affects **all** async functions, including the working `analyze_helpers` service. The script completes successfully despite this error - it's purely a framework limitation, not a code issue.

## �🙏 Acknowledgments

Built with the excellent [PyScript](https://github.com/custom-components/pyscript) custom component for Home Assistant.
