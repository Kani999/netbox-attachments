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

### Scope enforcement

Posting an `object_type` not permitted by the plugin's `scope_filter`/`applied_scope` settings returns a `400` validation error:

```json
{"object_type": "This object type is not permitted for attachments."}
```

### Unique constraint

Creating a duplicate assignment — same `attachment`, `object_type`, and `object_id` — is rejected with a validation error both in the UI form and via the API.

### Assignment endpoint filters

The `/api/plugins/netbox-attachments/netbox-attachment-assignments/` endpoint accepts the following query parameters:

| Parameter       | Description                                         |
|-----------------|-----------------------------------------------------|
| `attachment_id` | Filter by attachment ID.                            |
| `object_type_id`| Filter by the content type ID of the linked object. |
| `object_id`     | Filter by the ID of the linked object.              |
| `q`             | Free-text search across assignment fields.          |

### Attachment API response shape

A response from `/api/plugins/netbox-attachments/netbox-attachments/` includes a nested `assignments` array. Each element contains:

| Field          | Description                                                                                     |
|----------------|-------------------------------------------------------------------------------------------------|
| `id`           | Assignment record ID.                                                                           |
| `url`          | Canonical URL of the assignment record.                                                         |
| `display`      | Human-readable display string.                                                                  |
| `attachment`   | Nested attachment reference.                                                                    |
| `object_type`  | Content type label of the linked object (e.g. `dcim.device`).                                  |
| `object_id`    | ID of the linked object.                                                                        |
| `parent`       | Full nested representation of the linked NetBox object, or `null` when the assignment is broken.|
| `created`      | ISO 8601 timestamp of when the assignment was created.                                          |
| `last_updated` | ISO 8601 timestamp of the most recent update.                                                   |

The `size` field on the attachment object can be `null` if the file size could not be read at upload time.

### Attachments endpoint filters

In addition to the standard filters, the `/api/plugins/netbox-attachments/netbox-attachments/` endpoint accepts:

| Parameter               | Description                                                                                       |
|-------------------------|---------------------------------------------------------------------------------------------------|
| `has_assignments`       | `true`/`false` — filter attachments that have at least one assignment.                            |
| `has_broken_assignments`| `true`/`false` — filter attachments that have at least one broken assignment (see note below).    |

!!! note
    A "broken" assignment is one where the linked object type's model class can no longer be resolved, for example after uninstalling a plugin that provided that model.

## Attachment Lifecycle

Attachments are independent objects and can exist without any assignments.

- **Unlinking** removes only the assignment record. The attachment and its file on disk are kept.
- To remove the file from disk, explicitly delete the attachment via its detail page (`/plugins/netbox-attachments/netbox-attachments/<id>/`) or via the API (`DELETE /api/plugins/netbox-attachments/netbox-attachments/<id>/`).

!!! warning
    Deleting a `NetBoxAttachment` (via UI or `DELETE /api/plugins/netbox-attachments/netbox-attachments/<id>/`) also deletes all its assignment records. This is different from the "unlink" operation, which only removes the assignment and leaves the attachment and its file intact.

- When a linked NetBox object (e.g. a Device) is deleted, its assignments are removed but the attachment is preserved.
- Attachments with no assignments appear highlighted in red in the attachment list. Use the `?has_assignments=false` filter to surface them.
