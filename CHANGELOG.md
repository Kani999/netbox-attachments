# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.0.0] - 2026-03-02

### Added

- Global assignment list view at `/plugins/netbox-attachments/netbox-attachment-assignments/` with search (`q`) and filter by attachment, object type, and tag (issue #2).
- Object detail attachment tab now renders assignments via `NetBoxAttachmentForObjectTable` with columns: Attachment, Description, File, Size, Tags, and Actions (download + Unlink per row) (issue #4).
- Tags on `NetBoxAttachmentAssignment`: exposed in the global assignment list table, the link form, and the filter form.
- "Assignments" entry added to the plugin sidebar menu under Attachments.
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
- Project packaging migrated to `pyproject.toml`; `setuptools` minimum requirement bumped; `dependencies` populated with `django>=5.0,<6.0`; NetBox compatibility enforced at runtime via `min_version`/`max_version`.
- `MANIFEST.in` corrected to include `docs/` in sdist.
- README aligned to current compatibility policy and support channels.
- Unlinking the last assignment no longer auto-deletes the attachment or its file. Attachments now persist until explicitly deleted.
- `ObjectType` queryset scan now uses `.only("id").iterator()` for memory efficiency when resolving enabled models.
- Panel display modes (`left_page`, `right_page`, `full_width_page`) now render per-row Download and Unlink buttons via a dedicated `NetBoxAttachmentPanelListView` backed by `NetBoxAttachmentForObjectTable`, matching `additional_tab` behaviour.
- Unlink confirmation displays `app_label > model #id` (e.g., `dcim > circuit #224`) instead of the ContentType verbose name (issue #3).
- Redirect after unlinking the last assignment now goes to the attachment list instead of a stale attachment URL.
- Filter form boolean fields use `BooleanField` with an explicit `Select` widget instead of `NullBooleanField`.
- Exception handlers narrowed from bare `except` clauses to specific exception types throughout.
- `template_content.py` render functions guard against missing request context before rendering.
- `OSError` when reading file size on save is caught; `size` field stores `null` instead of raising.
- `CustomObjectType` DB lookup in `validate_object_type` deferred to avoid startup `RuntimeWarning`.
- Exception chaining suppressed in serializer `validate()` for cleaner error tracebacks.
- Bulk-view `prefetch_related` traverses `attachment_assignments__object_type` to avoid N+1 queries on the "Assigned To" column.
- `__init__.py`: `except ImportError` narrowed to `except ModuleNotFoundError` for the `PluginConfig` fallback.
- `utils.py`: `_get_plugin_settings()` also catches `ImproperlyConfigured` so the helper is safe to call before Django is fully configured.
- `NetBoxAttachmentLinkView`: "Save and Add Another" now correctly detects flow direction and forwards only the relevant GET params, avoiding a `ValueError` when `object_type`/`object_id` were absent.
- `NetBoxAttachmentForObjectTable`: `tags` column added to `default_columns` so assignment tag badges are visible by default on object detail Attachments tabs and inline panels.
- `NetBoxAttachmentForObjectTable`: `TagColumn.url_name` corrected to `netboxattachmentassignment_list` (was `netboxattachment_list`).
- Assignment querysets in `AttachmentTabView.get_children()`, `NetBoxAttachmentAssignmentListView`, and `NetBoxAttachmentPanelListView` now `prefetch_related("tags")` so assignment tag badges render without N+1 queries.

### Fixed

- `has_assignments` and `has_broken_assignments` filter fields changed from `forms.BooleanField` (with a `Select` widget) to `forms.ChoiceField`. Django's `BooleanField.has_changed()` coerces both `None` and `"false"` to Python `False`, so the field was never considered changed and the filter chip for "Has Assignments: No" / "Has Broken Assignments: No" never appeared. `ChoiceField` compares raw strings (`"" != "false"`), so the chip now renders correctly.

### Security

- `return_url` redirect targets validated with `url_has_allowed_host_and_scheme` before redirecting.
- Templates updated with `rel="noopener"` on external links and `urlencode` filter on URL parameters.

## [10.0.0] - 2025-11-11

### Changed

- NetBox 4.5 compatibility line introduced.

[11.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v11.0.0
[10.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v10.0.0
