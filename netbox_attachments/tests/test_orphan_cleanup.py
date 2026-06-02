"""
Unit tests for the pure orphan-cleanup helpers.

These import only ``netbox_attachments.management.orphan_cleanup`` (which pulls in no
Django models), so they run without a live NetBox/Django environment -- matching the
approach used in ``test_signals.py``.
"""

from netbox_attachments.management.orphan_cleanup import (
    matches_any_mask,
    select_missing_files,
    select_orphaned_files,
)

NOW = 1_000_000.0


def _disk(abspath, relpath, mtime=0.0):
    return (abspath, relpath, mtime)


# --- matches_any_mask --------------------------------------------------------


def test_mask_star_matches_prefix():
    assert matches_any_mask("netbox-attachments/keep.pdf", ["netbox-attachments/*"])


def test_mask_exact_match():
    assert matches_any_mask("netbox-attachments/a.pdf", ["netbox-attachments/a.pdf"])


def test_mask_no_match():
    assert not matches_any_mask("netbox-attachments/a.pdf", ["other/*"])


def test_mask_star_is_not_treated_as_regex():
    # A '.' in the mask must be literal, not "any char".
    assert not matches_any_mask("netbox-attachmentsXpdf", ["netbox-attachments.pdf"])


def test_empty_masks_never_match():
    assert not matches_any_mask("anything", [])
    assert not matches_any_mask("anything", None)


# --- select_orphaned_files ---------------------------------------------------


def test_orphaned_excludes_used_files():
    disk = [_disk("/m/a", "a"), _disk("/m/b", "b")]
    used = {"/m/a"}
    assert select_orphaned_files(disk, used, now=NOW) == ["/m/b"]


def test_orphaned_result_is_sorted():
    disk = [_disk("/m/c", "c"), _disk("/m/a", "a"), _disk("/m/b", "b")]
    assert select_orphaned_files(disk, set(), now=NOW) == ["/m/a", "/m/b", "/m/c"]


def test_min_age_guard_skips_recent_files():
    disk = [_disk("/m/fresh", "fresh", mtime=NOW - 10), _disk("/m/old", "old", mtime=NOW - 999)]
    # 60s guard => "fresh" (10s old) is protected, "old" is collectable.
    assert select_orphaned_files(disk, set(), now=NOW, minimum_file_age=60) == ["/m/old"]


def test_min_age_zero_disables_guard():
    disk = [_disk("/m/fresh", "fresh", mtime=NOW)]
    assert select_orphaned_files(disk, set(), now=NOW, minimum_file_age=0) == ["/m/fresh"]


def test_exclude_mask_skips_matching_files():
    disk = [_disk("/m/keep.tmp", "keep.tmp"), _disk("/m/drop.pdf", "drop.pdf")]
    assert select_orphaned_files(disk, set(), now=NOW, exclude=["*.tmp"]) == ["/m/drop.pdf"]


# --- select_missing_files ----------------------------------------------------


def test_missing_files_are_db_refs_absent_on_disk():
    disk = [_disk("/m/present", "present")]
    used = {"/m/present", "/m/gone"}
    assert select_missing_files(disk, used) == ["/m/gone"]


def test_no_missing_when_all_present():
    disk = [_disk("/m/a", "a"), _disk("/m/b", "b")]
    assert select_missing_files(disk, {"/m/a"}) == []
