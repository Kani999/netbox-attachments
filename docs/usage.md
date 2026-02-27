# Usage

## UI Workflow

1. Open a supported NetBox object detail page.
2. Use the plugin UI to add a new attachment or link an existing one.
3. Manage assignments from the attachment and object detail views.

Display location depends on `display_default`/`display_setting`.

## API Workflow

Attachments are exposed through plugin API endpoints.

Endpoint paths:

- `/api/plugins/netbox-attachments/netbox-attachments/`
- `/api/plugins/netbox-attachments/netbox-attachment-assignments/`

Minimal two-step example with `requests`:

```python
import requests

base_url = "https://your-netbox-url/api/plugins/netbox-attachments"
headers = {"Authorization": "Token your-api-token"}

# 1) Upload attachment
with open("./manual.pdf", "rb") as file_handle:
    upload_response = requests.post(
        f"{base_url}/netbox-attachments/",
        headers=headers,
        files={"file": ("manual.pdf", file_handle)},
        data={
            "name": "Device Manual",
            "description": "Manual for device 123",
            "comments": "Uploaded via API",
        },
        timeout=30,
    )
upload_response.raise_for_status()
attachment_id = upload_response.json()["id"]

# 2) Link attachment to target object
assignment_response = requests.post(
    f"{base_url}/netbox-attachment-assignments/",
    headers=headers,
    json={
        "attachment": attachment_id,
        "object_type": "dcim.device",
        "object_id": 123,
    },
    timeout=30,
)
assignment_response.raise_for_status()
```

## Attachment Lifecycle

Attachments are independent objects and can exist without any assignments.

- **Unlinking** removes only the assignment record. The attachment and its file on disk are kept.
- To remove the file from disk, explicitly delete the attachment via its detail page (`/plugins/netbox-attachments/netbox-attachments/<id>/`) or via the API (`DELETE /api/plugins/netbox-attachments/netbox-attachments/<id>/`).
- When a linked NetBox object (e.g. a Device) is deleted, its assignments are removed but the attachment is preserved.
- Attachments with no assignments appear highlighted in red in the attachment list. Use the `?has_assignments=false` filter to surface them.
