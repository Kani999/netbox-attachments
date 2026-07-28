# Configuration

Configure plugin settings under `PLUGINS_CONFIG["netbox_attachments"]`.

## Removed settings

These were replaced in v7.1.0 and are **ignored** if still present:

| Removed | Use instead | Check ID |
| --- | --- | --- |
| `apps` | `scope_filter` | `netbox_attachments.W001` |
| `allowed_models` | `scope_filter` | `netbox_attachments.W002` |
| `mode` | `applied_scope` (values are `app`/`model`, not `permissive`/`restrictive`) | `netbox_attachments.W003` |

NetBox keeps unrecognized keys in `PLUGINS_CONFIG` without reading them, so a stale config does not raise an error — the replacement setting silently falls back to its default instead. Because that default already covers several core apps, part of the configuration keeps working while the rest does not, which is easy to mistake for a bug in the plugin.

Since v11.3.0 a Django system check warns about each removed setting at startup. To see them:

```bash
python3 manage.py check
```

The check IDs above are stable and will not be renumbered. Deleting the stale key is the correct fix, but if you must keep it, silence the warning in `configuration.py`:

```python
SILENCED_SYSTEM_CHECKS = ["netbox_attachments.W001"]
```

## Settings

### `applied_scope`

- Type: `str`
- Default: `"app"`
- Allowed: `"app"`, `"model"`

Determines whether `scope_filter` entries are interpreted as app labels only (`app` mode) or as a mix of app labels and exact `app.model` identifiers (`model` mode).

### `scope_filter`

- Type: `list[str]`
- Default:
  - `dcim`
  - `ipam`
  - `circuits`
  - `tenancy`
  - `virtualization`
  - `wireless`

Scope targets where attachments are allowed.

- In `app` mode: use app labels, for example `dcim`.
- In `model` mode: use app labels and/or exact model names, for example `dcim.device`.
- For custom objects support:
  - `app` mode: include `netbox_custom_objects`
  - `model` mode: include `netbox_custom_objects.<custom_object_type_name>`

### `display_default`

- Type: `str`
- Default: `"additional_tab"`
- Allowed: `"left_page"`, `"right_page"`, `"full_width_page"`, `"additional_tab"`

Default display location for attachment UI. Each value controls where the panel is rendered on the object detail page:

- `additional_tab` — adds a dedicated "Attachments" tab to the object detail page.
- `left_page` — injects the panel into the left column of the object detail page.
- `right_page` — injects the panel into the right column of the object detail page.
- `full_width_page` — injects the panel as a full-width section below the main content.

!!! warning
    An unrecognized value matches none of the four render positions, so no attachment UI appears at all for the affected models — no tab, no panel. There is no error or warning. Use only the four values listed above.

### `create_add_button`

- Type: `bool`
- Default: `True`

Controls top-level **Attachments** dropdown creation when using `additional_tab` rendering mode.

!!! note
    Non-boolean values (e.g. `1`, `"true"`) log a warning and fall back to `True`.

### `display_setting`

- Type: `dict[str, str]`
- Default: `{}`

Per-model display override map. Keys use the same identifiers as `scope_filter`: `app_label.model` for standard models, and `netbox_custom_objects.<custom_object_type_name>` for custom objects.

Example:

```python
{
    "dcim.device": "left_page",
    "ipam.vlan": "additional_tab",
    "netbox_custom_objects.display_calibration": "right_page",
}
```

!!! note
    Before v11.3.0, custom objects were keyed here by an internal, primary-key-derived model name (`netbox_custom_objects.table12model`), so the identifier above silently had no effect.

## Example Configuration

```python
PLUGINS_CONFIG = {
    "netbox_attachments": {
        "applied_scope": "model",
        "scope_filter": [
            "dcim",
            "circuits",
            "ipam.ipaddress",
            "netbox_custom_objects.attachment",
        ],
        "display_default": "right_page",
        "create_add_button": True,
        "display_setting": {
            "dcim.device": "full_width_page",
            "tenancy.tenant": "additional_tab",
        },
    }
}
```

## Custom Objects

Attachments work on [netbox-custom-objects](https://github.com/netboxlabs/netbox-custom-objects) models. Enable them like any other app:

- `applied_scope: "app"` — add `netbox_custom_objects` to `scope_filter`
- `applied_scope: "model"` — add `netbox_custom_objects.<custom_object_type_name>`

Custom object types created after NetBox starts are picked up automatically; no restart is needed.

### Display limitations

A custom object detail page is rendered by the Custom Objects plugin's own template, which hardcodes its tab bar and its button row. It renders only the `left_page`, `right_page`, and `full_width_page` panel hooks, so on custom objects:

- **`additional_tab` is unavailable** — there is no way for a plugin to add a tab to that page. The effective display falls back to `full_width_page`, unless you pick a side panel explicitly:

    ```python
    "display_setting": {"netbox_custom_objects.display_calibration": "right_page"},
    ```

- **`create_add_button` has no effect** — the top-level "Attachments" dropdown cannot be rendered there. Use the panel's own "Add Attachment" and "Link Existing" buttons instead.

Both limitations are properties of the Custom Objects detail template, not of this plugin, and would need an upstream change to lift.
