"""
Backfill ``core_objecttype`` rows for every ObjectType referenced by existing
attachment data.

Background (issue #107): NetBox 4.6 turned ``core.ObjectType`` into a concrete
model with its own ``core_objecttype`` table. That table is populated by a
``post_migrate`` signal, not by a migration. Plugin migration ``0007`` re-points
the attachment FK at ``core.objecttype`` and PostgreSQL validates the constraint
against existing rows immediately -- so on an upgrade that carries attachment
data the migration fails with::

    Key (object_type_id)=(...) is not present in table "core_objecttype".

Running ``manage.py migrate`` with the plugin disabled lets the ``post_migrate``
signal populate ``core_objecttype`` for all *installed* models. The remaining
edge case is an attachment that references a ContentType whose model is no longer
installed (a removed plugin, a renamed model): ``post_migrate`` skips those, so
their ObjectType is never recreated and ``0007`` still fails on that id.

This command closes that gap. While the plugin is still at migration ``0006``,
the attachment FK to ``contenttypes.contenttype`` (``on_delete=CASCADE``)
guarantees that every referenced id has a live ``django_content_type`` row -- so
the missing ``core_objecttype`` row can always be recreated directly from it,
whether or not a backing model still exists.

Typical usage during an upgrade::

    # 1. disable the plugin in PLUGINS, then:
    python netbox/manage.py migrate
    # 2. re-enable the plugin, then:
    python netbox/manage.py fix_attachment_object_types
    python netbox/manage.py migrate
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

CORE_OBJECTTYPE = "core_objecttype"
CONTENTTYPE = "django_content_type"

# (table, column) pairs that may reference an ObjectType/ContentType, depending on
# which plugin migrations have been applied. Each is probed for existence first.
CANDIDATE_SOURCES = (
    ("netbox_attachments_netboxattachment", "object_type_id"),  # migrations 0006-0009
    ("netbox_attachments_netboxattachment", "content_type_id"),  # migrations 0001-0005
    ("netbox_attachments_netboxattachmentassignment", "object_type_id"),  # migrations 0008+
)


class Command(BaseCommand):
    help = (
        "Backfill core_objecttype rows for every object type referenced by existing "
        "attachment data. Fixes the migration 0007 FK violation on NetBox 4.6 upgrades "
        "(issue #107), including object types whose model is no longer installed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be created without writing any rows.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        introspection = connection.introspection
        tables = set(introspection.table_names())

        # NetBox < 4.6: ObjectType is a proxy of ContentType -- no separate table, no problem.
        if CORE_OBJECTTYPE not in tables:
            self.stdout.write(
                f"{CORE_OBJECTTYPE} table not found -- this NetBox version uses ObjectType as a "
                "proxy of ContentType; nothing to fix."
            )
            return

        with connection.cursor() as cursor:
            referenced = self._collect_referenced_ids(cursor, introspection, tables)
            if not referenced:
                self.stdout.write("No attachment rows reference an object type; nothing to fix.")
                return

            cursor.execute(
                f"SELECT contenttype_ptr_id FROM {CORE_OBJECTTYPE} WHERE contenttype_ptr_id = ANY(%s)",
                [list(referenced)],
            )
            existing = {row[0] for row in cursor.fetchall()}
            missing = referenced - existing

            if not missing:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"All {len(referenced)} referenced object type(s) already present in "
                        f"{CORE_OBJECTTYPE}; nothing to do."
                    )
                )
                return

            cursor.execute(
                f"SELECT id FROM {CONTENTTYPE} WHERE id = ANY(%s)",
                [list(missing)],
            )
            creatable = missing & {row[0] for row in cursor.fetchall()}
            dangling = missing - creatable  # no ContentType row at all -- cannot auto-fix

            self.stdout.write(
                f"Referenced object types: {len(referenced)} | "
                f"missing in {CORE_OBJECTTYPE}: {len(missing)} | "
                f"fixable: {len(creatable)} | unfixable: {len(dangling)}"
            )

            if dangling:
                self.stdout.write(
                    self.style.WARNING(
                        "These object_type_id values have no django_content_type row and must be "
                        "resolved manually (remap or delete the offending attachments): "
                        + ", ".join(str(i) for i in sorted(dangling))
                    )
                )

            if not creatable:
                return

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[dry-run] Would create {len(creatable)} {CORE_OBJECTTYPE} row(s): "
                        + ", ".join(str(i) for i in sorted(creatable))
                    )
                )
                return

            with transaction.atomic():
                cursor.execute(
                    f"""
                    INSERT INTO {CORE_OBJECTTYPE} (contenttype_ptr_id, public, features)
                    SELECT id, false, '{{}}'::varchar[]
                    FROM {CONTENTTYPE}
                    WHERE id = ANY(%s)
                    ON CONFLICT (contenttype_ptr_id) DO NOTHING
                    """,
                    [list(creatable)],
                )
                created = cursor.rowcount

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {created} {CORE_OBJECTTYPE} row(s). "
                    "The post_migrate signal will refine their public/features values on the next migrate."
                )
            )

    def _collect_referenced_ids(self, cursor, introspection, tables):
        """Gather distinct object-type ids from whichever source columns currently exist."""
        referenced = set()
        for table, column in CANDIDATE_SOURCES:
            if table not in tables:
                continue
            columns = {col.name for col in introspection.get_table_description(cursor, table)}
            if column not in columns:
                continue
            cursor.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL")
            referenced.update(row[0] for row in cursor.fetchall())
        return referenced
