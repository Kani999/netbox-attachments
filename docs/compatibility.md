# Compatibility Policy

## Maintained Compatibility

Current maintained line:

- NetBox: `4.7.x`
- Plugin: `12.x`
- Python: `3.12`, `3.13`, `3.14`
- Django: `6.1`

Runtime compatibility is enforced in plugin config:

- `min_version = "4.7.0"`
- `max_version = "4.7.99"`

Source: `netbox_attachments/__init__.py`

## Legacy Versions (Unsupported)

Plugin `11.x` supports NetBox 4.5–4.6. Earlier plugin releases supported older NetBox lines. Those combinations are no longer actively maintained under this certification effort.

See release history in [CHANGELOG.md](../CHANGELOG.md) for migration context.
