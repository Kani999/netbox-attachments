# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.0.0] - 2026-02-26

### Added

- `NetBoxAttachmentAssignment` junction model: one attachment can now be linked to multiple objects simultaneously.
- New "Assign" / "Unlink" UI workflow: link form with HTMX-driven object picker (`NetBoxAttachmentLinkView`) and unlink confirmation page (`NetBoxAttachmentAssignmentDeleteView`).
- New API endpoint `/api/plugins/netbox-attachments/netbox-attachment-assignments/` with full CRUD support.
- New filter fields: `has_assignments`, `has_broken_assignments`, `object_type_id`, `object_id` (routed through assignment relation).
- Attachment list table: "Assigned To" column shows up to 3 linked objects with a "+N more" badge; rows with no assignments highlighted with the `danger` CSS class.
- Migrations 0008–0011: create assignment table, data-migrate existing FK links, remove deprecated `object_type`/`object_id` fields from `NetBoxAttachment`, add composite DB index on `(object_type_id, object_id)`.
- CI matrix extended to Python 3.14.
- Certification documentation set under `docs/`.
- CI workflow for tests and build validation.
- Governance documents (`CONTRIBUTING.md`, certification checklist).
- Standalone pytest coverage for configuration and template helper behavior.

### Changed

- NetBox compatibility locked to `4.5.x` in plugin runtime bounds.
- Project packaging migrated to `pyproject.toml`; `setuptools` minimum requirement bumped.
- `MANIFEST.in` corrected to include `docs/` in sdist.
- README aligned to current compatibility policy and support channels.
- Unlinking the last assignment no longer auto-deletes the attachment or its file. Attachments now persist until explicitly deleted.
- `ObjectType` queryset scan now uses `.only("id").iterator()` for memory efficiency when resolving enabled models.

### Security

- `return_url` redirect targets validated with `url_has_allowed_host_and_scheme` before redirecting.
- Templates updated with `rel="noopener"` on external links and `urlencode` filter on URL parameters.

### Fixed

- Redirect to a deleted attachment URL after unlinking the last assignment (404 error).
- Filter form boolean fields use `BooleanField` with an explicit `Select` widget instead of `NullBooleanField`.
- Exception handlers narrowed from bare `except` clauses to specific exception types.
- `template_content.py` render functions guard against missing request context before rendering.

## [10.0.0] - 2025-11-11

### Changed

- NetBox 4.5 compatibility line introduced.

[11.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v11.0.0
[10.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v10.0.0
