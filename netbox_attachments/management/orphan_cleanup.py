"""
Pure, dependency-light helpers for orphaned-attachment cleanup.

This module deliberately imports **no Django models** so its logic can be unit
tested without a live NetBox/Django environment (mirroring the approach in
``tests/test_signals.py``). All database and filesystem access lives in the
``remove_orphaned_netbox_attachments`` management command, which feeds plain data
structures into these functions.
"""

import re

# Flat sub-directory (under MEDIA_ROOT) that NetBoxAttachment files are written to;
# see ``netbox_attachments.utils.attachment_upload``.
UPLOAD_SUBDIR = "netbox-attachments"


def mask_to_regex(mask):
    """Compile a shell-style mask into a regex. Only ``*`` is treated as a wildcard."""
    return re.compile("^{}$".format(re.escape(mask).replace(r"\*", ".*")))


def matches_any_mask(relpath, masks):
    """Return True if ``relpath`` matches any of the given ``*``-style masks."""
    return any(mask_to_regex(mask).match(relpath) for mask in masks or ())


def select_orphaned_files(disk_files, used_files, *, now, minimum_file_age=0, exclude=()):
    """
    Determine which on-disk files are orphaned and eligible for deletion.

    Args:
        disk_files: iterable of ``(abspath, relpath, mtime_epoch)`` tuples for every
            file found under the attachments directory.
        used_files: set/iterable of absolute paths still referenced by the database.
        now: current epoch seconds (passed in so the caller controls the clock; keeps
            this function deterministic and testable).
        minimum_file_age: skip files modified within this many seconds (0 disables the
            guard). Protects in-flight uploads from being collected.
        exclude: iterable of ``*``-style masks (matched against ``relpath``) to skip.

    Returns:
        Sorted list of absolute paths that are orphaned and may be removed. Files
        skipped by the age guard or an exclude mask are not included.
    """
    used = set(used_files)
    orphaned = []
    for abspath, relpath, mtime in disk_files:
        if abspath in used:
            continue
        if minimum_file_age and (now - mtime) < minimum_file_age:
            continue
        if exclude and matches_any_mask(relpath, exclude):
            continue
        orphaned.append(abspath)
    return sorted(orphaned)


def select_missing_files(disk_files, used_files):
    """
    Return database-referenced paths that have no file on disk.

    These indicate broken attachments (the record exists but its file is gone). They
    are reported, never auto-deleted.
    """
    on_disk = {abspath for abspath, _relpath, _mtime in disk_files}
    return sorted(set(used_files) - on_disk)
