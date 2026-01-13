# NetBox Attachments - Complete Testing Guide

This directory contains the complete testing infrastructure for the netbox_attachments plugin, including automated tests, configuration scenarios, and testing documentation.

---

## Quick Start

### Run All Automated Tests

```bash
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests -v 2
```

**Expected output:**
```
Ran 22 tests in 0.209s
OK (skipped=2)
```

### Run Manual Web Tests

```bash
# Terminal 1: Start web server
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py runserver 0.0.0.0:8000

# Terminal 2: Load configuration
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1

# Back to Terminal 1: Ctrl+C and restart
/opt/netbox/venv/bin/python manage.py runserver 0.0.0.0:8000

# Browser: Visit http://localhost:8000 and verify
```

### Run Specific Tests

```bash
# Run specific test file
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests.test_configuration

# Run specific test class
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests.test_configuration.DisplayDefaultTestCase

# Run specific test method
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests.test_configuration.DisplayDefaultTestCase.test_left_page_display
```

---

## Automated Test Suite

### Test Files

- **`test_configuration.py`** - 13 test classes covering all configuration options:
  - Configuration loading and defaults
  - Scope filtering (app vs model modes)
  - Display modes (tab, left/right panels, full-width)
  - Per-model display overrides
  - Button visibility
  - Custom objects integration
  - Graceful degradation

- **`test_template_extensions.py`** - 2 test classes for template extension registration:
  - Extension registration by display mode
  - Extension types and attributes

### Test Coverage

**Total:** 22 tests, 14 configuration scenarios

**Breakdown by Category:**

| Category | Tests | Coverage |
|----------|-------|----------|
| Configuration Loading | 2 | Default settings, minimal config |
| Scope Filtering | 4 | App scope, model scope, mixed mode |
| Display Modes | 4 | Tab, left, right, full-width |
| Display Overrides | 1 | Per-model overrides |
| Button Control | 1 | Add button visibility |
| Custom Objects | 3 | Integration, auto-conversion, missing plugin |
| Template Extensions | 5 | Registration, types, attributes |
| Edge Cases | 2 | Invalid config, empty scope |

---

## Configuration Scenarios

### Overview

The plugin includes 14 test configurations covering all supported features:

| # | Name | Focus | Config File |
|---|------|-------|-------------|
| 1 | Minimal | Default settings | `config_01_minimal.py` |
| 2 | App Scope | App-level filtering | `config_02_app_scope.py` |
| 3 | Model Scope | Specific models only | `config_03_model_scope.py` |
| 4 | Mixed Scope | App + model mix | `config_04_mixed_scope.py` |
| 5 | Left Panel | Left sidebar display | `config_05_left_page.py` |
| 6 | Right Panel | Right sidebar display | `config_06_right_page.py` |
| 7 | Full Width | Full-width panel | `config_07_full_width.py` |
| 8 | Mixed Display | Per-model overrides | `config_08_mixed_displays.py` |
| 9 | Button Disabled | No upload button | `config_09_button_disabled.py` |
| 10 | Custom Objects | All custom objects | `config_10_custom_objects_only.py` |
| 11 | Specific CO | Specific custom types | `config_11_specific_custom_objects.py` |
| 12 | Production | Recommended config | `config_12_production.py` |
| 13 | Empty Scope | Disabled (no models) | `config_13_empty_scope.py` |
| 14 | No CO Plugin | Without custom_objects | `config_14_without_custom_objects.py` |

### Testing Each Scenario

Use the swap script to quickly load configurations:

```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1    # Load config 1
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 5    # Load config 5
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 12   # Load config 12
```

---

## Configuration Parameters Reference

### `applied_scope`

Controls how `scope_filter` is interpreted:

- **`'app'`** - Filter by app label only (all models in specified apps)
  - Example: `'dcim'` → All dcim models enabled
  - Example: `'ipam'` → All ipam models enabled

- **`'model'`** - Filter by specific model or mixed app+model
  - Example: `'dcim.device'` → Only Device model
  - Example: `'dcim'` → All dcim models (same as app mode)
  - Mixed: `['dcim', 'ipam.ipaddress']` → All dcim + only ipaddress from ipam

### `scope_filter`

List of apps/models where attachments are enabled.

```python
# App scope examples
'scope_filter': ['dcim', 'ipam', 'circuits']

# Model scope examples
'scope_filter': ['dcim.device', 'dcim.site', 'ipam.ipaddress']

# Mixed examples
'scope_filter': ['dcim', 'ipam.ipaddress', 'virtualization.cluster']
```

### `display_default`

Default location for attachment UI on model detail pages:

- **`'additional_tab'`** (default) - Separate tab in the tabbed interface
- **`'left_page'`** - Left sidebar panel
- **`'right_page'`** - Right sidebar panel
- **`'full_width_page'`** - Full-width panel at bottom of page

### `display_setting`

Per-model overrides for `display_default`:

```python
'display_setting': {
    'dcim.device': 'full_width_page',    # Device uses full-width
    'dcim.site': 'left_page',            # Site uses left panel
    'dcim.rack': 'right_page',           # Rack uses right panel
    # Others use display_default: 'additional_tab'
}
```

### `create_add_button`

Whether to show "Add Attachment" button (only in `additional_tab` mode):

- **`True`** (default) - Show button, users can upload attachments
- **`False`** - Hide button, view-only mode (requires pre-existing attachments)

---

## Detailed Scenario Descriptions

### Scenario 1: Minimal (Defaults)

**Configuration:** `fixtures/config_01_minimal.py`

All default settings applied. Tests plugin with standard configuration.

**Tests:**
- `PluginConfigurationTestCase.test_default_configuration`
- `PluginConfigurationTestCase.test_minimal_config_loads`

**Web Testing:**
- Device detail page → Attachments tab visible
- All dcim, ipam, circuits, tenancy, virtualization, wireless models have attachments
- "Add Attachment" button visible in tab
- Can upload and download attachments

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1
```

---

### Scenario 2: App Scope Filtering

**Configuration:** `fixtures/config_02_app_scope.py`

Filter attachments by application only - all models within specified apps enabled.

**Tests:**
- `AppScopeFilteringTestCase.test_app_scope_basic`
- `AppScopeFilteringTestCase.test_custom_objects_only_app_scope`

**Expected Configuration:**
```python
applied_scope: 'app'
scope_filter: ['dcim', 'ipam', 'circuits', 'netbox_custom_objects']
```

**Web Testing:**
- Device (dcim) → Attachments visible ✓
- IP Address (ipam) → Attachments visible ✓
- Circuit (circuits) → Attachments visible ✓
- Custom Objects → Attachments visible ✓
- Tenant (tenancy) → Attachments NOT visible ✗
- Virtual Machine (virtualization) → Attachments NOT visible ✗

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 2
```

---

### Scenario 3: Model Scope - Specific Models

**Configuration:** `fixtures/config_03_model_scope.py`

Restrict attachments to only specific models.

**Tests:**
- `ModelScopeFilteringTestCase.test_model_scope_specific_models_only`

**Expected Configuration:**
```python
applied_scope: 'model'
scope_filter: ['dcim.device', 'dcim.site', 'ipam.ipaddress']
```

**Web Testing:**
- Device (dcim.device) → Attachments visible ✓
- Site (dcim.site) → Attachments visible ✓
- IP Address (ipam.ipaddress) → Attachments visible ✓
- Rack (dcim.rack) → Attachments NOT visible ✗
- Prefix (ipam.prefix) → Attachments NOT visible ✗

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 3
```

---

### Scenario 4: Model Scope - Mixed Mode

**Configuration:** `fixtures/config_04_mixed_scope.py`

Mix app-level and specific model filtering.

**Tests:**
- `ModelScopeFilteringTestCase.test_model_scope_mixed_mode`

**Expected Configuration:**
```python
applied_scope: 'model'
scope_filter: ['dcim', 'ipam.ipaddress', 'virtualization.cluster']
```

**Web Testing:**
- Device (dcim.*) → Attachments visible ✓
- Site (dcim.*) → Attachments visible ✓
- Rack (dcim.*) → Attachments visible ✓
- IP Address (ipam.ipaddress) → Attachments visible ✓
- Prefix (ipam.prefix) → Attachments NOT visible ✗
- Cluster (virtualization.cluster) → Attachments visible ✓
- Virtual Machine (virtualization.virtualmachine) → Attachments NOT visible ✗

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 4
```

---

### Scenario 5: Left Page Panel Display

**Configuration:** `fixtures/config_05_left_page.py`

Display attachments in left sidebar panel instead of tab.

**Tests:**
- `DisplayDefaultTestCase.test_left_page_display`

**Web Testing:**
- Device detail page → Attachments in LEFT sidebar panel (not tab)
- Site detail page → Attachments in LEFT sidebar panel
- Layout: Main content on right, Attachments panel on left
- Can upload/download attachments

**Visual Layout:**
```
┌─────────────────────────────────────┐
│ Device: Device-01                   │
├──────────────────┬──────────────────┤
│ ATTACHMENTS      │ GENERAL           │
│ ─────────────── │ ─────────────────  │
│ • file1.pdf     │ Name: Device-01   │
│ • file2.txt     │ Site: Site-01     │
│                 │                   │
│ + Add Attach... │ Status: active    │
│                 │                   │
├──────────────────┴──────────────────┤
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 5
```

---

### Scenario 6: Right Page Panel Display

**Configuration:** `fixtures/config_06_right_page.py`

Display attachments in right sidebar panel.

**Tests:**
- `DisplayDefaultTestCase.test_right_page_display`

**Web Testing:**
- Device detail page → Attachments in RIGHT sidebar panel (not tab)
- Site detail page → Attachments in RIGHT sidebar panel
- Layout: Main content on left, Attachments panel on right
- Can upload/download attachments

**Visual Layout:**
```
┌─────────────────────────────────────┐
│ Device: Device-01                   │
├──────────────────┬──────────────────┤
│ GENERAL           │ ATTACHMENTS      │
│ ─────────────────│ ─────────────── │
│ Name: Device-01  │ • file1.pdf     │
│ Site: Site-01    │ • file2.txt     │
│                  │                 │
│ Status: active   │ + Add Attach... │
│                  │                 │
├──────────────────┴──────────────────┤
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 6
```

---

### Scenario 7: Full Width Page Display

**Configuration:** `fixtures/config_07_full_width.py`

Display attachments in full-width panel at bottom of page.

**Tests:**
- `DisplayDefaultTestCase.test_full_width_display`

**Web Testing:**
- Device detail page → Attachments in full-width panel at BOTTOM
- Site detail page → Attachments in full-width panel at bottom
- Layout: Full width for attachments section
- Can upload/download attachments

**Visual Layout:**
```
┌─────────────────────────────────────┐
│ Device: Device-01                   │
├─────────────────────────────────────┤
│ GENERAL                             │
│ ─────────────────────────────────── │
│ Name: Device-01                     │
│ Site: Site-01                       │
│ Status: active                      │
├─────────────────────────────────────┤
│ ATTACHMENTS                         │
│ ─────────────────────────────────── │
│ • file1.pdf                         │
│ • file2.txt                         │
│                                     │
│ + Add Attachment                    │
├─────────────────────────────────────┤
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 7
```

---

### Scenario 8: Mixed Display Settings

**Configuration:** `fixtures/config_08_mixed_displays.py`

Different display modes for different models.

**Tests:**
- `DisplaySettingOverrideTestCase.test_mixed_display_settings`

**Web Testing:**
- Device (dcim.device) → Attachments in full-width panel (override)
- Site (dcim.site) → Attachments in LEFT panel (override)
- Rack (dcim.rack) → Attachments in RIGHT panel (override)
- Cable (dcim.cable) → Attachments in tab (default)
- Interface (dcim.interface) → Attachments in tab (default)

**Per-model overrides:**
```python
display_setting: {
    'dcim.device': 'full_width_page',
    'dcim.site': 'left_page',
    'dcim.rack': 'right_page',
}
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 8
```

---

### Scenario 9: Add Button Disabled

**Configuration:** `fixtures/config_09_button_disabled.py`

Disable the "Add Attachment" button for view-only mode.

**Tests:**
- `CreateAddButtonTestCase.test_button_disabled`

**Web Testing:**
- Device detail page → Attachments tab visible
- "Add Attachment" button NOT visible
- Can view existing attachments
- Cannot upload new attachments (view-only mode)

**Configuration:**
```python
create_add_button: False
display_default: 'additional_tab'
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 9
```

---

### Scenario 10: Custom Objects Only

**Configuration:** `fixtures/config_10_custom_objects_only.py`

Enable attachments only for custom objects.

**Prerequisites:**
- netbox_custom_objects plugin installed and configured
- At least one CustomObjectType created

**Web Testing:**
- Device (dcim) → Attachments NOT visible
- Site (dcim) → Attachments NOT visible
- Custom Object → Attachments visible
- Standard models disabled, custom objects enabled

**Configuration:**
```python
scope_filter: ['netbox_custom_objects']
```

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 10
```

---

### Scenario 11: Specific Custom Objects

**Configuration:** `fixtures/config_11_specific_custom_objects.py`

Enable attachments for specific custom object types only.

**Prerequisites:**
- netbox_custom_objects plugin installed
- CustomObjectType with desired name exists

**Web Testing:**
- Custom Object of specified type → Attachments visible
- Other custom object types → Attachments NOT visible

**Note:** Update config with actual CustomObjectType names from your environment

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 11
```

---

### Scenario 12: Production Configuration

**Configuration:** `fixtures/config_12_production.py`

Recommended production-ready configuration.

**Web Testing:**
- Device → Attachments visible ✓
- Site → Attachments visible ✓
- IP Address → Attachments visible ✓
- Circuit → Attachments visible ✓
- Tenant → Attachments visible ✓
- Virtual Machine → Attachments visible ✓
- Wireless LAN → Attachments visible ✓
- Custom Objects → Attachments visible ✓
- "Add Attachment" button visible and functional

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 12
```

---

### Scenario 13: Empty Scope Filter

**Configuration:** `fixtures/config_13_empty_scope.py`

Disable attachments without uninstalling the plugin.

**Web Testing:**
- Device → Attachments NOT visible
- Site → Attachments NOT visible
- Any model → Attachments NOT visible
- Plugin effectively disabled (without uninstalling)

**Use case:** Quick way to disable plugin without removing from PLUGINS list

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 13
```

---

### Scenario 14: Without Custom Objects Plugin

**Configuration:** `fixtures/config_14_without_custom_objects.py`

Test plugin when custom_objects plugin is not installed.

**Prerequisites:**
- netbox_custom_objects NOT in PLUGINS list (or uninstalled)

**Web Testing:**
- Device → Attachments visible ✓
- Site → Attachments visible ✓
- IP Address → Attachments visible ✓
- Standard models work normally
- No errors about missing custom_objects plugin

**Load configuration:**
```bash
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 14
```

---

## Configuration Examples

### Example 1: Minimal (All Defaults)

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        # Uses all default values
    }
}
```

### Example 2: App Scope with Panel Display

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': ['dcim', 'ipam'],
        'display_default': 'left_page',  # Left sidebar instead of tab
    }
}
```

### Example 3: Model Scope with Mixed Filters

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'dcim',                      # All dcim models
            'ipam.ipaddress',            # Only this ipam model
            'virtualization.cluster',    # Only this virtualization model
        ],
    }
}
```

### Example 4: Mixed Display Modes

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': ['dcim'],
        'display_default': 'additional_tab',  # Default for most
        'display_setting': {
            'dcim.device': 'full_width_page',  # Override: Device
            'dcim.site': 'left_page',          # Override: Site
        },
    }
}
```

### Example 5: Production Configuration

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': [
            'dcim',
            'ipam',
            'circuits',
            'tenancy',
            'virtualization',
            'wireless',
            'netbox_custom_objects',
        ],
        'display_default': 'additional_tab',
        'create_add_button': True,
    }
}
```

---

## Testing Workflows

### Automated Test Workflow

```bash
# 1. Run all tests
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests -v 2

# 2. Run specific test file
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests.test_configuration

# 3. Run specific test class
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests.test_configuration.DisplayDefaultTestCase

# 4. Review test results
# Expected: 20 passed, 2 skipped (custom objects missing - expected when plugin installed)
```

### Web Testing Workflow

```bash
# Terminal 1: Start web server
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py runserver 0.0.0.0:8000

# Terminal 2: Load configuration
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1

# Back to Terminal 1: Restart
# Ctrl+C to stop
/opt/netbox/venv/bin/python manage.py runserver 0.0.0.0:8000

# Browser: Navigate and verify
# http://localhost:8000 → Login if required
# Navigate to model detail pages (Device, Site, etc.)
# Verify attachment tabs/panels visible
# Test upload/download if applicable
```

### Manual Configuration Editing (Alternative)

If you prefer not to use the swap script:

1. Edit `/opt/netbox/netbox/netbox/configuration.py`
2. Copy `PLUGINS` section from desired config file in `fixtures/`
3. Copy `PLUGINS_CONFIG` section
4. Restart NetBox server:
   ```bash
   # If using runserver: Ctrl+C and restart
   # If using Docker: docker-compose restart
   # If using systemd: systemctl restart netbox
   ```
5. Verify changes in browser

### Using nbshell for Testing

Test configuration programmatically using nbshell:

```bash
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py nbshell
```

Then in nbshell:

```python
# Check if Device has attachments enabled
from netbox_attachments.utils import validate_object_type
from dcim.models import Device

print(validate_object_type(Device))  # True or False

# Check display preference for a model
from netbox_attachments.template_content import get_display_preference

print(get_display_preference('dcim.device'))  # Display mode
```

---

## Test Fixtures Directory

The `fixtures/` directory contains all configuration files and helper tools:

- **config_01.py through config_14.py** - 14 configuration scenarios
- **swap_netbox_config.sh** - Configuration swapper script

### Using the Swap Script

```bash
# Basic usage
./fixtures/swap_netbox_config.sh 1          # Load config 1
./fixtures/swap_netbox_config.sh 5          # Load config 5

# List available configurations
./fixtures/swap_netbox_config.sh             # Shows available configs

# Disable backups (not recommended)
./fixtures/swap_netbox_config.sh 1 --no-backup
```

### Script Features

- **Automatic Backups:** Creates timestamped backup of original configuration.py
- **Safe Replacement:** Uses regex to replace only netbox_attachments config block
- **Error Handling:** Validates files and provides clear error messages
- **Color Output:** Green for success, red for errors

### Backup Information

Backups stored in `/tmp/netbox_config_backups/` with timestamps:
```
/tmp/netbox_config_backups/configuration_20240115_143022.py
/tmp/netbox_config_backups/configuration_20240115_143045.py
```

### Restoring from Backup

```bash
cp /tmp/netbox_config_backups/configuration_20240115_143022.py /opt/netbox/netbox/netbox/configuration.py
```

---

## Troubleshooting

### Tests Failing

**Problem:** `RuntimeError: NetBox requires Python 3.12 or later`

**Solution:** Use Python from venv:
```bash
/opt/netbox/venv/bin/python manage.py test ...
```

**Problem:** Test fails with import errors

**Solution:** Ensure you're in the correct directory:
```bash
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py test netbox_attachments.tests
```

### Configuration Not Applying

1. Check swap script executed successfully:
   ```bash
   grep -A 5 netbox_attachments /opt/netbox/netbox/netbox/configuration.py
   ```

2. Verify configuration.py syntax:
   ```bash
   python -m py_compile /opt/netbox/netbox/netbox/configuration.py
   ```

3. Restart NetBox server

### Attachment Tab/Panel Not Visible

1. Verify model is in `scope_filter`
2. Check `applied_scope` matches your filtering (app vs model)
3. Verify `display_default` or `display_setting` is correctly set
4. Clear browser cache (Ctrl+Shift+Delete)
5. Restart server and refresh page

### "Add Attachment" Button Not Visible

1. Check `create_add_button` is not False
2. Check `display_default` is 'additional_tab' (button only shown in tab mode)
3. Verify user has appropriate permissions
4. Clear browser cache

### Performance Issues

- Use model scope instead of app scope for fine-grained control
- Reduce `scope_filter` to only necessary models
- Avoid full_width_page if many attachments expected (use tabs for pagination)

---

## Common Commands Reference

```bash
# Run all tests
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test netbox_attachments.tests -v 2

# Run specific test file
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test netbox_attachments.tests.test_configuration

# Run specific test class
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test netbox_attachments.tests.test_configuration.DisplayDefaultTestCase

# Run specific test method
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test netbox_attachments.tests.test_configuration.DisplayDefaultTestCase.test_left_page_display

# Load configuration 1 for manual testing
/opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1

# View current configuration (after applying with swap script)
grep -A 20 'netbox_attachments' /opt/netbox/netbox/netbox/configuration.py

# Start web server for manual testing
cd /opt/netbox/netbox && /opt/netbox/venv/bin/python manage.py runserver 0.0.0.0:8000

# List available configurations
ls /opt/netbox-attachments/netbox_attachments/tests/fixtures/config_*.py

# View specific configuration
cat /opt/netbox-attachments/netbox_attachments/tests/fixtures/config_05_left_page.py
```

---

## File Structure

```
/opt/netbox-attachments/
├── netbox_attachments/
│   └── tests/
│       ├── README.md                    (this file)
│       ├── __init__.py
│       ├── test_configuration.py        (13 test classes, ~500 lines)
│       ├── test_template_extensions.py  (2 test classes)
│       └── fixtures/
│           ├── config_01_minimal.py
│           ├── config_02_app_scope.py
│           ├── ... (14 config files total)
│           ├── config_14_without_custom_objects.py
│           └── swap_netbox_config.sh    (helper script)
```

---

## Next Steps

1. **Run automated tests** to validate plugin works:
   ```bash
   /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py test netbox_attachments.tests -v 2
   ```

2. **Use swap script** to load configurations for manual testing:
   ```bash
   /opt/netbox-attachments/netbox_attachments/tests/fixtures/swap_netbox_config.sh 1
   ```

3. **Verify each scenario** works as documented in the scenario descriptions above

4. **Check test code** to understand what's tested:
   ```bash
   less /opt/netbox-attachments/netbox_attachments/tests/test_configuration.py
   ```

---

**Test Suite Version:** 1.0
**Last Updated:** 2026-01-13
**Tests:** 22 (20 passed, 2 skipped)
**Configurations:** 14
**Status:** Ready for production use
