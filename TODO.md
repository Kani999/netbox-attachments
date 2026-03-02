# TODO / Backlog

Lightweight backlog for future maintenance and improvement tasks.

---

## Done

### 5. Defer DB access during NetBox app initialization

Restructured `validate_object_type()` in `utils.py` to defer the `CustomObjectType` DB lookup.
In the default `applied_scope = "app"` mode, zero DB queries are made at startup.
In `applied_scope = "model"` mode, the app-label short-circuit avoids the DB query when
the whole app is listed in `scope_filter`; the DB is only hit for custom objects when a
specific model-name lookup is actually required.

Eliminates `RuntimeWarning: Accessing the database during app initialization is discouraged.`

### 6. Suppress exception chaining in serializers `validate()`

Added `from None` when re-raising `ObjectDoesNotExist` as `serializers.ValidationError`
in `netbox_attachments/api/serializers.py`. Suppresses the original exception context from
tracebacks.

---

## Open Items

### 2. Migrate repository to CESNET GitHub organisation

Move the repository from the current location to the CESNET GitHub org.
Update all links in README, PyPI metadata, and docs accordingly.

### 3. Multi-object assignment in the link form

The "Assign to Object" link form currently creates one assignment per submission.
A future improvement would let users assign one attachment to **multiple objects at once**
(e.g. select object type → multi-select from the object list → one submit creates N assignments).

Starting scope: same object type only (avoids mixed-type API complexity).

### 7. Add tags to assignments

`NetBoxAttachmentAssignment` already inherits a `tags` M2M field from `NetBoxModel` (no migration needed).
Wire it up when ready:

- `tables.py` — add `tags = columns.TagColumn(url_name="plugins:netbox_attachments:netboxattachmentassignment_list")` to `NetBoxAttachmentAssignmentTable` and include `"tags"` in `fields`/`default_columns`
- `forms.py` — add `"tags"` to `NetBoxAttachmentLinkForm.Meta.fields` and add `tag = TagFilterField(model)` to `NetBoxAttachmentAssignmentFilterForm`
- `filtersets.py` — add `tag = TagFilter()` to `NetBoxAttachmentAssignmentFilterSet`
- `templates/netbox_attachments/netbox_attachment_link.html` — add `{% render_field form.tags %}` in the forward-flow branch (after `form.attachment`)
- `tests/test_new_features.py` — restore the `test_assignment_filter_form_declares_tag_filter_field` test

### 8. Bulk-unlink on the object attachment tab

The per-row unlink button handles one assignment at a time. A bulk-unlink action on the
object detail attachment tab would let users select multiple rows and remove all chosen
assignments in a single operation — useful when an attachment has been linked to many
objects and needs cleaning up.

Implementation notes:
- Enable checkboxes by removing the `actions = ()` override (or adding a bulk-delete URL)
  in `AttachmentTabView` inside `template_content.py`.
- Register a bulk-delete URL for `NetBoxAttachmentAssignment` scoped to the parent object
  so the return URL stays on the correct tab.
- Guard with `netbox_attachments.delete_netboxattachmentassignment` permission.

### 4. Plugin certification remediation status (NetBox 4.5.x)

External maintainer actions remaining:

- [ ] Add GitHub co-maintainer
- [ ] Add PyPI co-maintainer
- [ ] Confirm NetDev community account
- [ ] Submit certification request issue in `netbox-community/netbox`

