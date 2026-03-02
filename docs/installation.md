# Installation

## Requirements

- NetBox `4.5.x`
- Python `3.12` to `<3.15`

## 1. Install the package

```bash
pip install netbox-attachments
```

## 2. Enable the plugin

In NetBox `configuration.py`:

```python
PLUGINS = ["netbox_attachments"]
```

## 3. Configure media storage path

```bash
mkdir -p /opt/netbox/netbox/media/netbox-attachments
chown netbox /opt/netbox/netbox/media/netbox-attachments
```

## 4. Apply migrations

```bash
python3 manage.py migrate netbox_attachments
```

## 5. Restart NetBox services

Restart NetBox application services so plugin hooks and template extensions are loaded.

## 6. Verify installation

- Open NetBox UI and confirm plugin menu entries are available.
- Verify API endpoint `/api/plugins/netbox-attachments/netbox-attachments/` responds.
- Verify API endpoint `/api/plugins/netbox-attachments/netbox-attachment-assignments/` responds.
