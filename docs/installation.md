# Installation

## Requirements

- NetBox `4.5.x` – `4.6.x`
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

## Upgrading to NetBox 4.6 (issue #107)

Upgrading to NetBox 4.6 **with existing attachments** can fail in plugin migration
`0007_alter_netboxattachment_object_type` with:

```
psycopg.errors.ForeignKeyViolation: ... violates foreign key constraint
"netbox_attachments_n_object_type_id_..._fk_core_obje"
DETAIL: Key (object_type_id)=(...) is not present in table "core_objecttype".
```

**Why it happens.** NetBox 4.6 turned `core.ObjectType` into a concrete model with its own
`core_objecttype` table, which is populated by a `post_migrate` signal that fires only at the *end*
of a completed `migrate` run. Migration `0007` re-points the attachment foreign key at
`core.objecttype`, and PostgreSQL validates that constraint immediately — while `core_objecttype`
is still empty — so the run aborts before the population signal is ever reached. Fresh installs are
unaffected (no attachment rows to validate).

**Recommended upgrade procedure:**

1. Comment the plugin out of `PLUGINS` in `configuration.py`.
2. Run `python3 manage.py migrate`. This completes the core upgrade; the end-of-run `post_migrate`
   signal populates `core_objecttype` for all installed models.
3. Re-enable the plugin in `PLUGINS`.
4. Back-fill any object types whose model is no longer installed (a removed plugin, a renamed
   model) — `post_migrate` skips those, but the command recreates them directly from
   `django_content_type`:

   ```bash
   python3 manage.py fix_attachment_object_types        # add --dry-run to preview first
   ```

5. Run `python3 manage.py migrate` to apply the plugin migrations.

The `fix_attachment_object_types` command is idempotent, safe to run repeatedly, and a no-op on
NetBox versions older than 4.6.

### Running the fix before this release is installed

If you hit this on a plugin version that does not yet ship the command, run the equivalent directly
in `nbshell` (`python3 manage.py nbshell`) after step 3, before the final `migrate`:

> **Scope:** this snippet assumes the schema left by a failed `0007` migration — i.e. the plugin at
> migration `0006`, where object-type references live solely in
> `netbox_attachments_netboxattachment.object_type_id` (`content_type_id` was renamed away in `0006`,
> and the assignment table is not created until `0008`). If your database is in any other state, use
> the `fix_attachment_object_types` command instead, which auto-detects the source table/column.

```python
from django.db import connection

if "core_objecttype" in connection.introspection.table_names():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO core_objecttype (contenttype_ptr_id, public, features)
            SELECT id, false, '{}'::varchar[]
            FROM django_content_type ct
            WHERE id IN (
                SELECT DISTINCT object_type_id
                FROM netbox_attachments_netboxattachment
                WHERE object_type_id IS NOT NULL
            )
            AND NOT EXISTS (
                SELECT 1 FROM core_objecttype ot WHERE ot.contenttype_ptr_id = ct.id
            )
            """
        )
        print("created", cursor.rowcount, "core_objecttype row(s)")
```

The `post_migrate` signal refines the `public`/`features` values of the inserted rows on the next
`migrate`.
