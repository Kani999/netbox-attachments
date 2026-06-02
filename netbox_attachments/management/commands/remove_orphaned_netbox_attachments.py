"""
Management command to clean up orphaned netbox-attachments data.

It addresses the two distinct kinds of "orphan" that accumulate over time
(see issue #22):

1. **Orphaned files on disk** -- files under ``MEDIA_ROOT/netbox-attachments/``
   that no ``NetBoxAttachment`` record references. These are left behind by failed
   deletes and by renaming/overwriting an attachment's file (the old file is not
   removed automatically).
2. **Orphaned attachment records** -- ``NetBoxAttachment`` rows that have no
   assignments. Since plugin 11.0.0, unlinking the last assignment no longer deletes
   the attachment, so unused records (and their files) build up. Deleting the record
   removes its file too.

Safety first (cf. discussion in issue #22): the command is a **dry-run by default**
and prints a report. Nothing is removed unless ``--delete`` is given, and even then a
confirmation prompt guards the operation (skip it with ``--no-input``). A
``--min-age`` guard skips freshly written files to avoid racing in-flight uploads.

Examples::

    # Report only (default) -- safe to run anytime
    python manage.py remove_orphaned_netbox_attachments

    # Verbose report, including the per-file list and assignment breakdown
    python manage.py remove_orphaned_netbox_attachments -v2

    # Actually delete, without the interactive prompt
    python manage.py remove_orphaned_netbox_attachments --delete --no-input

    # Also list attachments tied to disabled/uninstalled plugins (report-only)
    python manage.py remove_orphaned_netbox_attachments --list-broken -v2

Safety with disabled/uninstalled plugins: this command keys off database rows, not
whether a linked object's model can be resolved. Disabling a plugin leaves the
attachment, its assignment row, and the file in place, so such attachments are never
treated as orphaned. Use ``--list-broken`` to surface them for manual review.
"""

import time
from pathlib import Path

from core.models.object_types import ObjectType
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from netbox_attachments.management.orphan_cleanup import (
    UPLOAD_SUBDIR,
    select_missing_files,
    select_orphaned_files,
)
from netbox_attachments.models import NetBoxAttachment, NetBoxAttachmentAssignment


class Command(BaseCommand):
    help = "Remove orphaned netbox-attachments files and/or unassigned attachment records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            default=False,
            help="Actually delete. Without this flag the command only reports (dry-run).",
        )
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            default=False,
            help="Force report-only mode (default). Overrides --delete if both are given.",
        )
        parser.add_argument(
            "--no-input",
            "--noinput",
            dest="interactive",
            action="store_false",
            default=True,
            help="Do not prompt for confirmation before deleting.",
        )
        parser.add_argument(
            "--files-only",
            action="store_true",
            default=False,
            help="Only act on orphaned files on disk (skip unassigned records).",
        )
        parser.add_argument(
            "--records-only",
            action="store_true",
            default=False,
            help="Only act on unassigned attachment records (skip on-disk file scan).",
        )
        parser.add_argument(
            "--min-age",
            dest="min_age",
            type=int,
            default=60,
            metavar="SECONDS",
            help="Skip files modified within this many seconds (default 60). Use 0 to disable.",
        )
        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            default=[],
            metavar="MASK",
            help="Exclude on-disk files by *-style mask (relative to MEDIA_ROOT). Repeatable.",
        )
        parser.add_argument(
            "--list-broken",
            action="store_true",
            default=False,
            help=(
                "Report-only: also list attachments whose assignment points to an object type "
                "from a disabled/uninstalled plugin (unresolvable model). These are never deleted."
            ),
        )

    # -- output helpers -------------------------------------------------------

    def info(self, message=""):
        if self.verbosity > 0:
            self.stdout.write(message)

    def debug(self, message=""):
        if self.verbosity > 1:
            self.stdout.write(message)

    # -- main -----------------------------------------------------------------

    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        # Dry-run is the default and always wins if explicitly requested.
        delete = options["delete"] and not options["dry_run"]
        interactive = options["interactive"]

        if options["files_only"] and options["records_only"]:
            raise CommandError("--files-only and --records-only are mutually exclusive.")
        do_files = not options["records_only"]
        do_records = not options["files_only"]

        media_root = Path(settings.MEDIA_ROOT)
        attachment_dir = media_root / UPLOAD_SUBDIR

        # --- gather ----------------------------------------------------------
        orphaned_files, missing_files = [], []
        if do_files:
            orphaned_files, missing_files = self._scan_files(
                media_root, attachment_dir, options["min_age"], options["exclude"]
            )

        orphaned_records_qs = NetBoxAttachment.objects.filter(attachment_assignments__isnull=True)
        orphaned_records_count = orphaned_records_qs.count() if do_records else 0

        # --- report ----------------------------------------------------------
        self._report(
            attachment_dir=attachment_dir,
            do_files=do_files,
            do_records=do_records,
            orphaned_files=orphaned_files,
            missing_files=missing_files,
            orphaned_records_qs=orphaned_records_qs,
            orphaned_records_count=orphaned_records_count,
        )

        # Report-only: attachments tied to disabled/uninstalled plugins. These are
        # deliberately never deleted (see _delete / docs), only surfaced for review.
        if options["list_broken"]:
            self._report_broken()

        total = (len(orphaned_files) if do_files else 0) + orphaned_records_count
        if total == 0:
            self.info("\nNothing to clean up.")
            return

        mode = "DELETE" if delete else "DRY RUN (nothing will be removed)"
        self.info(f"\nMode: {mode}")
        if not delete:
            self.info("Re-run with --delete to remove the items listed above.")
            return

        if interactive:
            answer = input(f"\nDelete {total} orphaned item(s)? [y/N] ").strip().upper()
            if answer != "Y":
                self.info("Aborted; nothing was deleted.")
                return

        self._delete(do_files, do_records, orphaned_files, orphaned_records_qs)

    # -- steps ----------------------------------------------------------------

    def _report_broken(self):
        """
        List attachments whose assignment points to an object type from a
        disabled/uninstalled plugin (its model can no longer be resolved).

        Uses the same definition of "broken" as the ``has_broken_assignments``
        filter (``ObjectType.model_class() is None``). Report-only -- these
        attachments are never deleted by this command.
        """
        broken_ids = [
            ot.id for ot in ObjectType.objects.only("id", "app_label", "model").iterator() if ot.model_class() is None
        ]
        assignments = (
            NetBoxAttachmentAssignment.objects.filter(object_type_id__in=broken_ids)
            .select_related("attachment", "object_type")
            .order_by("object_type__app_label", "object_type__model", "object_id")
        )

        self.info(f"\nAttachments on disabled/uninstalled plugins (broken assignments): {assignments.count()}")
        self.info("  (report-only -- these are never deleted)")
        for assignment in assignments.iterator():
            ot = assignment.object_type
            attachment = assignment.attachment
            self.debug(
                f"  {ot.app_label}.{ot.model} #{assignment.object_id}"
                f"  ->  #{attachment.pk} {attachment.name or attachment.filename}"
            )

    def _scan_files(self, media_root, attachment_dir, min_age, exclude):
        if not attachment_dir.exists():
            self.debug(f"Attachment directory does not exist: {attachment_dir}")
            return [], []

        # Absolute paths still referenced by the database.
        used_files = {
            str((media_root / value).resolve())
            for value in NetBoxAttachment.objects.exclude(file="")
            .exclude(file__isnull=True)
            .values_list("file", flat=True)
        }

        # Every file currently on disk, as (abspath, relpath, mtime) tuples.
        disk_files = []
        for path in attachment_dir.rglob("*"):
            if path.is_file():
                try:
                    disk_files.append((str(path.resolve()), str(path.relative_to(media_root)), path.stat().st_mtime))
                except OSError:
                    # File vanished (or became unreadable) between the directory walk
                    # and stat(); skip it -- a file we cannot stat is not a deletable orphan.
                    continue

        orphaned = select_orphaned_files(
            disk_files,
            used_files,
            now=time.time(),
            minimum_file_age=min_age,
            exclude=exclude,
        )
        missing = select_missing_files(disk_files, used_files)
        return orphaned, missing

    def _report(
        self,
        *,
        attachment_dir,
        do_files,
        do_records,
        orphaned_files,
        missing_files,
        orphaned_records_qs,
        orphaned_records_count,
    ):
        # Context: how many attachments are linked per object type. The
        # "(unassigned)" line is exactly the set of orphaned records below.
        self.info("Attachment assignment breakdown:")
        breakdown = (
            NetBoxAttachmentAssignment.objects.values("object_type__app_label", "object_type__model")
            .annotate(n=Count("attachment", distinct=True))
            .order_by("object_type__app_label", "object_type__model")
        )
        for row in breakdown:
            label = f"{row['object_type__app_label']}.{row['object_type__model']}"
            self.info(f"  {label:40} {row['n']} attachment(s)")
        self.info(f"  {'(unassigned -> deletion candidates)':40} {orphaned_records_count}")

        if do_records:
            self.info(f"\nOrphaned attachment records (no assignments): {orphaned_records_count}")
            for attachment in orphaned_records_qs.iterator():
                self.debug(f"  #{attachment.pk} {attachment.name or attachment.filename}")

        if do_files:
            total_size = 0
            self.info(f"\nOrphaned files on disk (no DB record): {len(orphaned_files)}")
            self.debug(f"  (scanned {attachment_dir})")
            for abspath in orphaned_files:
                try:
                    size = Path(abspath).stat().st_size
                except OSError:
                    # File removed between scan and report; nothing left to reclaim.
                    self.debug(f"  {Path(abspath).name}  (vanished before report)")
                    continue
                total_size += size
                self.debug(f"  {Path(abspath).name}  ({size / 1024:.1f} KB)")
            if orphaned_files:
                self.info(f"  Total reclaimable: {total_size / 1024:.1f} KB")
            if missing_files:
                self.info(
                    self.style.WARNING(
                        f"\nBroken attachments (DB record, missing file): {len(missing_files)} "
                        "-- reported only, not deleted."
                    )
                )
                for abspath in missing_files:
                    self.debug(f"  {abspath}")

    def _delete(self, do_files, do_records, orphaned_files, orphaned_records_qs):
        removed_records = 0
        if do_records:
            # Delete via the model so each record's file and signals are handled.
            for attachment in list(orphaned_records_qs):
                attachment.delete()
                removed_records += 1
            self.info(f"Deleted {removed_records} orphaned attachment record(s).")

        if do_files:
            removed_files = 0
            for abspath in orphaned_files:
                try:
                    Path(abspath).unlink()
                    removed_files += 1
                    self.debug(f"Removed {abspath}")
                except OSError as exc:
                    self.stderr.write(f"Could not remove {abspath}: {exc}")
            self.info(f"Deleted {removed_files} orphaned file(s).")

        self.info(self.style.SUCCESS("Cleanup complete."))
