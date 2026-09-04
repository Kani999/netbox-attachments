# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [12.0.0] - 2026-09-04

This release supports NetBox 4.7.x only. Deployments on NetBox 4.5 or 4.6 should stay on the 11.x line.

### Changed

- Compatibility window moved to NetBox `4.7.x` (`min_version = "4.7.0"`, `max_version = "4.7.99"`). NetBox 4.7.0 refused to load the plugin because of the previous `4.6.99` ceiling (issue #116).
- List views declare their actions as `ObjectAction` classes from `netbox.object_actions`. NetBox 4.7 dropped the shim that translated the legacy dict form, so the bump alone would have raised `AttributeError` on every attachment and assignment list page.
- Django requirement raised to `>=6.1`, matching NetBox 4.7.
- Migration `0012` now records `related_name="+"` on `NetBoxAttachment.owner`, matching the change NetBox 4.7 made to `OwnerMixin`. No schema change; existing installs are unaffected.

### Removed

- The `ObjectTypeField` serializer shim. NetBox 4.7's `ContentTypeField` resolves against the field's declared queryset, so the cast to `ObjectType` is no longer needed.

### Fixed

- Custom fields are now exposed by the REST API serializers for both `NetBoxAttachment` and `NetBoxAttachmentAssignment`. They were omitted from the serializers' `fields` list, which DRF drops silently (the field is declared on a NetBox base class, exempting it from the "declared fields must be listed" assertion) — so custom fields were editable in the UI but invisible and unwritable through the API.

### Changed

- Removed a redundant `objects` manager on `NetBoxAttachmentAssignment` (`NetBoxModel` already provides the same `RestrictedQuerySet` manager) and a stray `__init__.py` in the templates directory. No behavior change.

## [11.3.1] - 2026-07-28

### Changed

- Consolidated attachment-panel display resolution (issue #112). Side and full-width panels for every in-scope model — standard and custom — are now served by a single render-time template extension; the startup loop registers only `additional_tab` tab views. This removes the duplicated display logic that previously had to be kept in sync across the two paths (the source of the `display_setting` bug fixed in 11.3.0). No user-facing behavior change.

## [11.3.0] - 2026-07-28

### Fixed

- Attachments never appeared on Custom Object detail pages when `netbox_attachments` was listed before `netbox_custom_objects` in `PLUGINS` (issue #110). Template extensions were built while this plugin's `ready()` ran, but `netbox_custom_objects` withholds its dynamically generated models until its own `ready()` has finished, so model discovery found nothing and no panel was ever registered — regardless of `scope_filter`. Custom objects are now served by a single, globally registered template extension that resolves the object at render time, so plugin order in `PLUGINS` no longer matters.
- Custom Object Types created after startup now get an attachment panel without restarting NetBox. Previously the model list was enumerated once during startup, so any type created later was invisible until the next restart.

### Added

- Startup warning (Django system check `netbox_attachments.W001`–`W003`) when `PLUGINS_CONFIG["netbox_attachments"]` still contains `apps`, `allowed_models`, or `mode`. These were replaced by `scope_filter` and `applied_scope` in v7.1.0, and NetBox keeps unknown keys without reading them, so a stale config silently fell back to the default `scope_filter` — which covers several core apps, making the configuration look partly honored (issue #110). The check names the replacement setting; run `manage.py check` to see it.

### Changed

- Custom object models are no longer enumerated at startup, removing this plugin's own database access during app loading and its dependency on `PLUGINS` ordering. (`apps.get_models()` is still called, so `netbox_custom_objects` may itself query when it loads first — but the plugin no longer drives that.)
- `display_setting` now accepts the same identifier for custom objects that `scope_filter` does — `netbox_custom_objects.<custom_object_type_name>`. It previously keyed off the internal, primary-key-derived model name (`netbox_custom_objects.table12model`), so the documented identifier silently never matched and per-type display overrides had no effect.

## [11.2.3] - 2026-06-02

### Added

- Management command `remove_orphaned_netbox_attachments` to report and clean up orphaned attachment data (issue #22): orphaned files on disk under `MEDIA_ROOT/netbox-attachments/` (including leftovers from renamed/overwritten attachments) and unassigned `NetBoxAttachment` records. It is a **dry-run by default**; deletion requires `--delete` and is guarded by an interactive confirmation (skippable with `--no-input`). Supports `--files-only`/`--records-only`, a `--min-age` guard that skips freshly written files, and `-e/--exclude` masks. Verbose mode (`-v2`) lists each affected file/record plus a per-object-type assignment breakdown. "Broken" attachments (record present, file missing) are reported but never deleted. Attachments tied to disabled/uninstalled plugins are never garbage-collected (the command keys off database rows, not model resolvability); `--list-broken` reports them for manual review. See [docs/usage.md](docs/usage.md#maintenance-cleaning-up-orphans).

## [11.2.2] - 2026-06-02

### Added

- Management command `fix_attachment_object_types` to back-fill `core_objecttype` rows for every object type referenced by existing attachment data. This unblocks the foreign-key violation in migration `0007_alter_netboxattachment_object_type` that can occur when upgrading to NetBox 4.6 with existing attachments (issue #107), including object types whose model is no longer installed. The command is idempotent, supports `--dry-run`, and is a no-op on NetBox < 4.6. See [docs/installation.md](docs/installation.md#upgrading-to-netbox-46-issue-107).

## [11.2.1] - 2026-05-13

### Changed

- Relax Django constraint from `django>=5.0,<6.0` to `django>=5.0,<7.0` in `pyproject.toml`. NetBox 4.6 ships Django 6.0, so the previous cap forced a Django downgrade when installing on NetBox 4.6 (issue #105).

## [11.2.0] - 2026-05-11

### Changed

- Bump `max_version` from `4.5.99` to `4.6.99` to allow installing on NetBox 4.6.x (issue #103).

## [11.1.0] - 2026-04-21

### Added

- NetBox 4.5 Resource Ownership on `NetBoxAttachment`: new optional `owner` field (FK to `users.Owner`, `on_delete=PROTECT`), surfaced in the edit form, bulk-edit form, filter form, DRF filterset, and API serializer. Owner appears in the generic page subtitle via `generic/object.html`; `owner` and `owner_group` are available as opt-in columns on the attachment list table. The attachment list / API endpoint accepts `owner_id`, `owner_group_id`, `owner`, and `owner_group` filters (issue #101).

### Changed

- `NetBoxAttachment` model rebased from `NetBoxModel` onto `PrimaryModel`; the plugin's manually declared `description` and `comments` fields were removed in favor of the inherited definitions (identical signatures).
- Serializer, filterset, and forms for `NetBoxAttachment` re-parented to the matching `PrimaryModel*` base classes.
- Migration `0013_alter_netboxattachmentassignment_custom_field_data` picks up an upstream NetBox change that added `encoder=CustomFieldJSONEncoder` to `CustomFieldsMixin.custom_field_data`; the plugin's existing migration graph was out of sync with that.

## [11.0.1] - 2026-03-04

### Changed

- Version bumped from `11.0.0` to `11.0.1`. The `v11.0.0` tag was accidentally pushed to PyPI before the branch was fully merged; that release has been yanked. `v11.0.1` is the intended release and is functionally identical.

## [11.0.0] - 2026-03-02

### Added

- Global assignment list view at `/plugins/netbox-attachments/netbox-attachment-assignments/` with search (`q`) and filter by attachment, object type, and tag (issue #2).
- Object detail attachment tab now renders assignments via `NetBoxAttachmentForObjectTable` with columns: Attachment, Description, File, Size, Tags, and Actions (download + Unlink per row) (issue #4).
- Tags on `NetBoxAttachmentAssignment`: exposed in the global assignment list table, the link form, and the filter form.
- "Assignments" entry added to the plugin sidebar menu under Attachments.
- `NetBoxAttachmentAssignment` junction model: one attachment can now be linked to multiple objects simultaneously.
- New "Assign" / "Unlink" UI workflow: link form with HTMX-driven object picker (`NetBoxAttachmentLinkView`) and unlink confirmation page (`NetBoxAttachmentAssignmentDeleteView`).
- New API endpoint `/api/plugins/netbox-attachments/netbox-attachment-assignments/` with full CRUD support; uses `ObjectTypeField` to correctly resolve `"app_label.model"` strings to NetBox `ObjectType` proxy instances.
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
- Attachment list, bulk-edit, and bulk-delete querysets now annotate `attachment_link_count` via `Count("attachment__attachment_assignments", distinct=True)` so assignment-count-based row highlighting works in all list contexts without extra queries; replaces the previous `prefetch_related` approach that issued a separate round-trip and returned full rows only to count them.
- `__init__.py`: `except ImportError` narrowed to `except ModuleNotFoundError` for the `PluginConfig` fallback.
- `utils.py`: `_get_plugin_settings()` also catches `ImproperlyConfigured` so the helper is safe to call before Django is fully configured.
- `NetBoxAttachmentLinkView`: "Save and Add Another" now correctly detects flow direction and forwards only the relevant GET params, avoiding a `ValueError` when `object_type`/`object_id` were absent.
- `NetBoxAttachmentForObjectTable`: `tags` column added to `default_columns` so assignment tag badges are visible by default on object detail Attachments tabs and inline panels.
- `NetBoxAttachmentForObjectTable`: `TagColumn.url_name` corrected to `netboxattachmentassignment_list` (was `netboxattachment_list`).
- Assignment querysets in `AttachmentTabView.get_children()`, `NetBoxAttachmentAssignmentListView`, and `NetBoxAttachmentPanelListView` now `prefetch_related("tags")` so assignment tag badges render without N+1 queries.

### Fixed

- `utils.py`: `validate_object_type()` no longer raises `NameError` when `netbox_custom_objects` is not installed; the `except` tuple now uses `ObjectDoesNotExist` (imported at module level) instead of `CustomObjectType.DoesNotExist`, which was unresolvable after a failed import.
- `tables.py`: `get_missing_parent_row_class()` fallback path now emits a `logger.warning()` so unannotated queries are visible in server logs rather than silently issuing extra DB queries.
- `NetBoxAttachmentLinkForm`: object-type picker now filters via `get_enabled_object_type_queryset()` instead of a bare `ObjectType.objects.get()`, so only plugin-configured types are selectable after an HTMX reload.
- `NetBoxAttachmentLinkForm`: editing an existing assignment no longer raises a false "duplicate assignment" validation error; `self.instance.pk` is now excluded from the uniqueness check.
- `has_assignments` and `has_broken_assignments` filter fields changed from `forms.BooleanField` (with a `Select` widget) to `forms.ChoiceField`. Django's `BooleanField.has_changed()` coerces both `None` and `"false"` to Python `False`, so the field was never considered changed and the filter chip for "Has Assignments: No" / "Has Broken Assignments: No" never appeared. `ChoiceField` compares raw strings (`"" != "false"`), so the chip now renders correctly.

### Security

- `return_url` redirect targets validated with `url_has_allowed_host_and_scheme` before redirecting.
- Templates updated with `rel="noopener"` on external links and `urlencode` filter on URL parameters.

## [10.0.0] - 2025-11-11

### Changed

- NetBox 4.5 compatibility line introduced.

[11.0.1]: https://github.com/Kani999/netbox-attachments/releases/tag/v11.0.1
[11.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v11.0.0
[10.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v10.0.0
