# NetBox Attachments Plugin

[NetBox](https://github.com/netbox-community/netbox) plugin for attaching files to any model.

## Features
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/Kani999/netbox-attachments?utm_source=oss&utm_medium=github&utm_campaign=Kani999%2Fnetbox-attachments&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

This plugin provides the following model:

- **NetBoxAttachment**: A model for attaching files to any NetBox object.

## Compatibility

The following table shows the compatibility between different NetBox versions and plugin versions:

| NetBox Version | Plugin Version |
| -------------- | -------------- |
| >= 3.3.4       | 0.0.0 - 0.0.5  |
| >= 3.4.0       | 0.0.6 - 1.0.6  |
| >= 3.4.3       | 1.0.7 - 1.1.x  |
| >= 3.5.0       | 2.0.0          |
| >= 3.6.0       | 3.0.0          |
| >= 3.7.0       | 4.0.0          |
| >= 4.0.0       | 5.x.x          |
| >= 4.1.0       | 6.x.x          |
| >= 4.2.0       | 7.x.x          |
| >= 4.3.0       | 8.x.x          |
| >= 4.4.0       | 9.x.x          |
| >= 4.5.0       | 10.x.x         |

## Installation

The plugin is available as a Python package on PyPI and can be installed with `pip`:

```sh
pip install netbox-attachments
```

To enable the plugin, add it to the `PLUGINS` list in your `configuration.py`:

```python
PLUGINS = ['netbox_attachments']
```

Next, create a directory for storing attachments and set the appropriate permissions:

```sh
mkdir -p /opt/netbox/netbox/media/netbox-attachments
chown netbox /opt/netbox/netbox/media/netbox-attachments
```

Run the database migrations for the plugin:

```sh
python3 manage.py migrate netbox_attachments
```

Restart NetBox and ensure that `netbox-attachments` is included in your `local_requirements.txt`.

For more details, see the [NetBox Documentation](https://docs.netbox.dev/en/stable/plugins/#installing-plugins).

## NetBox 4.4 Compatibility Changes

Starting from version 9.0.0, the plugin has been updated for full NetBox 4.4 compatibility with the following changes:

### Template Extension Updates
- **Models Attribute**: Updated template extensions to use the `models` list attribute instead of the deprecated `model` attribute for NetBox 4.x compatibility.
- **Error Handling**: Improved error handling for template rendering when object types are missing.
- **Template Panel Rendering**: Fixed AttributeError issues in `render_attachment_panel` function for proper template extension compatibility.

### API and URL Improvements
- **Bulk Action URLs**: Added proper URL patterns for bulk edit and bulk delete operations.
- **URL Pattern Reorganization**: Improved URL pattern ordering for better routing logic.
- **Default Return URLs**: Enhanced navigation flow after bulk operations.

These changes ensure the plugin works seamlessly with NetBox 4.4 while maintaining all core attachment functionality and improving the user experience.


## New Validation Checks

From version `7.2.0`, we introduce new model-level validation that ensures attachments are only created for permitted object types. Attempting to attach to an unpermitted model will raise a ValidationError.

## Configuration

### Plugin Options

The plugin can be customized using the following configuration options:

- `applied_scope`:

  - **Type**: String
  - **Default**: `"app"`
  - **Options**: `"app"`, `"model"`
  - **Description**: Determines how attachments are enabled. In 'app' mode, attachments are allowed for all models in the configured apps. In 'model' mode, attachments can be enabled for specific models or all models within specified apps.

- `scope_filter`:

  - **Type**: List
  - **Default**: `['dcim', 'ipam', 'circuits', 'tenancy', 'virtualization', 'wireless']`
  - **Description**: List of items to filter by. The expected format depends on the `applied_scope` mode:
    - In **'app' mode**: Should contain app labels (e.g., `'dcim'`, `'ipam'`, `'netbox_custom_objects'` to enable all custom objects)
    - In **'model' mode**: Can contain:
      - Specific model strings in the format `app_label.model_name` (e.g., `'dcim.device'`)
      - App labels to include all models from that app (e.g., `'dcim'`)
      - For NetBox Custom Objects: `'netbox_custom_objects.{CustomObjectType.name}'` to enable specific custom object types (see [Custom Objects Support](#custom-objects-support-new-feature) below)

- `display_default`:

  - **Type**: String
  - **Default**: `"additional_tab"`
  - **Options**: `"left_page"`, `"right_page"`, `"full_width_page"`, `"additional_tab"`
  - **Description**: Sets the default location where attachments should be displayed in the models.

- `create_add_button`:

  - **Type**: Boolean
  - **Default**: `True`
  - **Description**: Specific only to `additional_tab` display setting. If set to True, it will create an "Add Attachment" button at the top of the parent view.

- `display_setting`:
  - **Type**: Dictionary
  - **Default**: `{}`
  - **Format**: `{<app_label.model>: <preferred_display>}`
  - **Example**: `{'dcim.devicerole': 'full_width_page', 'dcim.device': 'left_page', 'ipam.vlan': 'additional_tab'}`
  - **Description**: Override the display settings for specific models.
  - **Tip**: Use the correct `app_label` and `model` names, which can be found in the API at `<your_netbox_url>/api/extras/content-types/`.

### Custom Objects Support (New Feature)

The plugin now supports the NetBox Custom Objects plugin, allowing attachments on dynamically created custom object models.

- In **'app' mode**: Add `'netbox_custom_objects'` to `scope_filter` to enable attachments for all custom objects without specifying individual types.
- In **'model' mode**: Use the format `'netbox_custom_objects.{CustomObjectType.name}'` to enable attachments for specific custom object types only.

#### Configuration Examples

**Example 1: Enable all custom objects (app mode)**
```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': ['dcim', 'ipam', 'netbox_custom_objects'],
    }
}
```

**Example 2: Enable specific custom objects only**
```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'dcim.device',
            'ipam.ipaddress',
            'netbox_custom_objects.attachment',
            'netbox_custom_objects.vendor_policy',
        ],
    }
}
```

**Example 3: Mixed mode - whole apps and specific models**
```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'dcim',
            'circuits',
            'ipam.ipaddress',
            'netbox_custom_objects.attachment',
        ],
    }
}
```

#### Finding Custom Object Names

To find the CustomObjectType names for your configuration:

1. Navigate to **NetBox → Custom Objects → Custom Objects Types**
2. Look at the **"Name"** column
3. Use these names in `scope_filter` with format: `'netbox_custom_objects.{name}'`

You can also list all custom object names using the NetBox shell:
```python
from netbox_custom_objects.models import CustomObjectType

for cot in CustomObjectType.objects.all():
    print(f"Use in config: 'netbox_custom_objects.{cot.name}'")
```

**Important Notes:**
- NetBox restart is required after adding or removing custom object types
- The netbox-custom-objects plugin must be installed and configured
- Custom object models are discovered at startup time only
- **Limitation:** The `additional_tab` display mode is not supported for custom object models due to their non-standard URL routing. Custom objects will automatically use `full_width_page` display mode instead. You can override this by explicitly setting a different panel mode (`left_page`, `right_page`) in `display_setting`


## API Usage

Since the import functionality has been removed, you can use the NetBox API to programmatically manage attachments:

### Creating Attachments via API

```python
import requests

# Example: Upload attachment via API
url = "https://your-netbox-url/api/plugins/netbox-attachments/attachments/"
headers = {
    "Authorization": "Token your-api-token",
    "Content-Type": "application/json"
}

# For file uploads, use multipart/form-data
files = {
    'file': ('filename.pdf', open('path/to/file.pdf', 'rb'))
}
data = {
    'object_type': 'dcim.device',  # ContentType ID or app_label.model
    'object_id': 123,
    'name': 'Device Manual',
    'description': 'User manual for the device'
}

response = requests.post(url, headers=headers, files=files, data=data)
```

> **Note**: The `additional_tab` feature will work for plugin models if you include the following in your `urls.py`:
>
> ```python
> from netbox.urls import get_model_urls
> 
> path(
>    "MODEL/<int:pk>/",
>    include(get_model_urls("plugin_name", "model_name")),
> ),
> ```
>
> **Note**: `plugin_name` refers to the plugin slug used in URLs (often hyphenated), which may differ from the Python package/module name.
>
> By doing so, the system will automatically include the Changelog, Journal, and other registered tabs (such as Attachments) when `additional_tab` is enabled.

### Configuration Example

Here is an example of how to configure the plugin in `configuration.py`:

```python
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': "model",  # 'app' or 'model'
        'scope_filter': [
            'dcim.device', 'ipam.prefix', 'ipam.ipaddress',  # Specific models
            'tenancy',  # All models from this app
        ],
        'display_default': "right_page",
        'create_add_button': True,
        'display_setting': { # Works only for `app.model` definition
            'ipam.vlan': "left_page",
            'dcim.device': "full_width_page",
            'dcim.devicerole': "full_width_page",
            'tenancy.tenant': "additional_tab"
        }
    }
}
```

## Enabling Attachments for Custom Plugins (Models)

To enable attachments for custom plugin models:

1. Append your plugin to the `scope_filter` configuration list:

   ```python
   scope_filter: ['<plugin_name>']
   ```

2. Extend the detail templates of your plugin models:

   ```django
   {% load plugins %}  # At the top of the template

   {% plugin_right_page object %}  # Under the comments section

   # Add left_page and full_width for future extensions
   ```

### Example (Device Model)

- [load](https://github.com/netbox-community/netbox/blob/c1b7f09530f0293d0f053b8930539b1d174cd03b/netbox/templates/dcim/device.html#L6)
- [left_page](https://github.com/netbox-community/netbox/blob/c1b7f09530f0293d0f053b8930539b1d174cd03b/netbox/templates/dcim/device.html#L149)
- [right_page](https://github.com/netbox-community/netbox/blob/c1b7f09530f0293d0f053b8930539b1d174cd03b/netbox/templates/dcim/device.html#L288)
- [full_width_page](https://github.com/netbox-community/netbox/blob/c1b7f09530f0293d0f053b8930539b1d174cd03b/netbox/templates/dcim/device.html#L293)

## Screenshots

- **Model View:**
  ![Platform attachments](docs/img/platform.png)
- **List View:**
  ![List View](docs/img/list.PNG)
- **Detail View:**
  ![Detail View](docs/img/detail.PNG)
