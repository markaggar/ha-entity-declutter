# HA Entity Declutter

A comprehensive Home Assistant helper analysis and cleanup system built with PyScript. This tool helps you identify and safely remove unused helpers, reducing clutter in your Home Assistant configuration.

## 🎯 Features

- **Comprehensive Helper Detection**: Analyzes all 27 helper integration types including template sensors, input helpers, utility meters, and more
- **Smart Dependency Analysis**: Tracks references across automations, scripts, templates, and dashboards
- **Multi-Category Classification**: 
  - **Actively Used**: Referenced in automations/scripts/templates
  - **Dashboard Only**: Only used in UI dashboards
  - **Truly Orphaned**: No references found anywhere
- **Auto-Generated Lovelace Cards**: Creates ready-to-use dashboard cards for easy review
- **Multi-Environment Support**: Separate dev and production deployments
- **Safe Deletion Tools**: Backup and restore functionality with dry-run mode
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

4. **Download and copy the Python scripts**:
   - Download `analyze_helpers.py` and `delete_helpers.py` from this repository
   - Copy both files to your `/config/pyscript/` directory

5. **Restart Home Assistant** to load the PyScript components

6. **Run the analysis**:
   - Go to **Developer Tools → Services** in Home Assistant
   - Run service: `pyscript.analyze_helpers`
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

## 🧹 Safe Deletion

1. **Review the analysis**: Check `helper_summary.txt` and the generated dashboard cards
2. **Edit the list**: Remove any helpers you want to keep from `orphaned_helpers.txt`
3. **Dry run**: `pyscript.delete_helpers` with `dry_run: true`
4. **Execute**: `pyscript.delete_helpers` with `dry_run: false`

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
- **`delete_helpers.py`**: Safe deletion script - copy to `/config/pyscript/`  
- **`deploy-pyscript.ps1`**: Development deployment tool (for contributors)
- **`README.md`**: This documentation

## 🤝 Contributing

Contributions welcome! This tool has evolved through real-world testing on complex Home Assistant setups.

## 📄 License

MIT License - feel free to adapt for your Home Assistant setup.

## 🙏 Acknowledgments

Built with the excellent [PyScript](https://github.com/custom-components/pyscript) custom component for Home Assistant.
