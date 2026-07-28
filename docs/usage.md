# Usage

## UI Workflow

### Object detail attachment tab

Open a supported NetBox object detail page. The attachment tab shows a table of all assignments for that object, rendered using `NetBoxAttachmentForObjectTable`. Columns shown by default: Attachment (link), Description, Size, Links, Tags, Created, and Actions. A **File** column is also available and can be enabled through the table's column selector.

The **Links** column shows the total number of objects this attachment is assigned to across the whole system, as a clickable number linking to the attachment detail page. A count of 1 means unlinking will leave the attachment with no assignments; a count greater than 1 means the attachment remains linked elsewhere.

The Actions column holds a Download button plus the standard NetBox actions dropdown. Choosing **Delete** there removes only that assignment — the attachment and its file on disk are kept, so the effect is an unlink. Below the table, two buttons are available: "Add Attachment" (upload and assign a new file) and "Link Existing" (assign an already-uploaded attachment).

Display location of the tab depends on the `display_default` and `display_setting` configuration options.

### Panel display modes (left_page, right_page, full_width_page)

When the display mode is `left_page`, `right_page`, or `full_width_page`, the attachment UI is injected as an inline panel on the object detail page. The panel renders the same `NetBoxAttachmentForObjectTable` as the tab view, scoped to that object's assignments — including the Download button and the Delete action described above.

The panel header contains "Add Attachment" and "Link Existing" buttons identical to those in the tab view. The table is loaded via HTMX from the dedicated `netboxattachment_panel_list` endpoint (`/plugins/netbox-attachments/netbox-attachment-panel/`), which filters assignments by `object_type_id` and `object_id`.

### Global assignment list

A global list of all assignments is available at `/plugins/netbox-attachments/netbox-attachment-assignments/`. Access it from the sidebar via Attachments → Assignments.

The list supports the following search and filter options:

| Filter      | Description                                      |
|-------------|--------------------------------------------------|
| `q`         | Free-text search across assignment fields.       |
| Attachment  | Filter by a specific attachment record.          |
| Object Type | Filter by the content type of the linked object. |
| Tag         | Filter by tags applied to the assignment.        |

### Unlink confirmation

When unlinking an assignment, the confirmation page identifies the target object as `app_label > model #id` (e.g., `dcim > circuit #224`). For broken assignments — where the linked object type can no longer be resolved — the same format is used, derived from the raw content type, so the confirmation is unambiguous even when the object no longer exists.

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

## Maintenance: cleaning up orphans

Over time two kinds of "orphan" can accumulate (see issue #22):

- **Orphaned files on disk** — files under `MEDIA_ROOT/netbox-attachments/` that no `NetBoxAttachment` record references. These are left behind by failed deletes and by renaming/overwriting an attachment's file (the old file is not removed automatically).
- **Orphaned attachment records** — `NetBoxAttachment` rows with no assignments. Since unlinking the last assignment no longer deletes the attachment, unused records (and their files) build up. They are the same records surfaced by the `?has_assignments=false` filter.

The `remove_orphaned_netbox_attachments` management command reports and (optionally) removes both:

```bash
# Report only — safe to run anytime (this is the default; nothing is deleted)
python3 manage.py remove_orphaned_netbox_attachments

# Verbose report listing each orphaned file/record and the assignment breakdown
python3 manage.py remove_orphaned_netbox_attachments -v2

# Actually delete, with an interactive confirmation prompt
python3 manage.py remove_orphaned_netbox_attachments --delete

# Delete without prompting (e.g. from cron)
python3 manage.py remove_orphaned_netbox_attachments --delete --no-input

# Report-only: also list attachments tied to disabled/uninstalled plugins
python3 manage.py remove_orphaned_netbox_attachments --list-broken -v2
```

Useful options:

| Option | Description |
|--------|-------------|
| `--delete` | Perform deletion. Without it the command only reports (dry-run). |
| `-n`, `--dry-run` | Force report-only mode; overrides `--delete` if both are given. |
| `--no-input` | Skip the confirmation prompt when deleting. |
| `--files-only` | Only act on orphaned files on disk. |
| `--records-only` | Only act on unassigned attachment records. |
| `--min-age SECONDS` | Skip files modified within this many seconds (default `60`). Use `0` to disable. Protects in-flight uploads. |
| `-e`, `--exclude MASK` | Exclude on-disk files by `*`-style mask (relative to `MEDIA_ROOT`); repeatable. |
| `--list-broken` | Report-only: also list attachments tied to a disabled/uninstalled plugin (see below). Never deletes them. |
| `-v2` | List each affected file/record and the per-object-type assignment breakdown. |

!!! warning
    Deleting an orphaned attachment record also deletes its file from disk. Run without `--delete` first and review the report. The command reports — but never deletes — "broken" attachments (a record whose file is already missing from disk).

### Safety with disabled or uninstalled plugins

The command decides what to delete from **database rows**, never from whether a linked object's model can be resolved. Disabling (or uninstalling) a plugin leaves the `NetBoxAttachment` record, its `NetBoxAttachmentAssignment` row, and the file on disk all in place. As a result:

- The attachment's file is still referenced by a record, so it is **never** counted as an orphaned file.
- The attachment still has an assignment row, so it is **never** counted as an orphaned record (the assignment merely becomes "broken" — the same state surfaced by the `?has_broken_assignments=true` filter).

In other words, **temporarily disabling a plugin can never cause its attachments to be garbage-collected.** This is intentional and conservative: even a *fully uninstalled* plugin's attachments are preserved rather than auto-deleted. To find such attachments — for example to clean them up deliberately — use `--list-broken`, which reports (but never deletes) every attachment whose assignment points to an object type with an unresolvable model.
