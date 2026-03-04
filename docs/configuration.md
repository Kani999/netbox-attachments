# Configuration

Configure plugin settings under `PLUGINS_CONFIG["netbox_attachments"]`.

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
    Unrecognized values for `display_default` will silently produce a non-functional panel extension. Use only the four values listed above.

### `create_add_button`

- Type: `bool`
- Default: `True`

Controls top-level **Attachments** dropdown creation when using `additional_tab` rendering mode.

!!! note
    Non-boolean values (e.g. `1`, `"true"`) log a warning and fall back to `True`.

### `display_setting`

- Type: `dict[str, str]`
- Default: `{}`

Per-model display override map.

Example:

```python
{"dcim.device": "left_page", "ipam.vlan": "additional_tab"}
```

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

## Custom Objects Limitation

`additional_tab` mode is not available for custom object models using non-standard URL routing. For such models, the effective fallback is `full_width_page` unless an explicit left/right panel mode is configured.
