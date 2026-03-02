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

### 10. Panel display modes missing unlink button; "Link Existing" shown instead

When `display_default` (or a per-model override) is set to `left_page`, `right_page`, or
`full_width_page`, the attachment panel renders via `netbox_attachment_panel.html`, which calls:

```django
{% htmx_table 'plugins:netbox_attachments:netboxattachment_list' object_type_id=... object_id=... %}
```

This URL points to `NetBoxAttachmentListView`, which queries `NetBoxAttachment` objects and uses
`NetBoxAttachmentTable` — a table that has no unlink button, but does show a "Link Existing"
button in the card header and an "Assign" button per row (neither of which is useful when you
are already looking at the object's own attachments).

The `additional_tab` mode works correctly because `AttachmentTabView` queries
`NetBoxAttachmentAssignment` objects and uses `NetBoxAttachmentForObjectTable`, which renders
both a **Download** and an **Unlink** button per row via `OBJECT_ATTACHMENT_ACTIONS`.

**Fix plan:**

1. Add `NetBoxAttachmentPanelListView` in `views.py` — a `generic.ObjectListView` subclass that:
   - queries `NetBoxAttachmentAssignment` with `select_related("attachment")` and
     `prefetch_related("attachment__tags", "attachment__attachment_assignments")`
   - uses `tables.NetBoxAttachmentForObjectTable`
   - uses `filtersets.NetBoxAttachmentAssignmentFilterSet`
   - sets `actions = {}` (no bulk actions needed in this context)

2. Register a URL in `urls.py`:
   ```python
   path("netbox-attachment-panel/", views.NetBoxAttachmentPanelListView.as_view(),
        name="netboxattachment_panel_list")
   ```

3. Update `netbox_attachment_panel.html` line 24 to use the new URL:
   ```django
   {% htmx_table 'plugins:netbox_attachments:netboxattachment_panel_list' object_type_id=object|content_type_id object_id=object.pk %}
   ```

4. Remove the "Link Existing" button from the card header actions in `netbox_attachment_panel.html`
   (it is not meaningful when browsing an object's own attachment list; linking is done from the
   attachment detail or global list). Keep the "Add Attachment" button.

No migration needed. No change to `NetBoxAttachmentForObjectTable`.

### 9. HTMX selector error for Custom Objects and object types without list/filter view

When linking an attachment to a **Custom Object** (or any `object_type` that has no standard
list/filter view registered in NetBox), clicking the object selector widget raises an HTMX error.

Root cause: the selector widget constructs a URL to a NetBox list/filter view for the selected
`content_type` — Custom Objects and some plugin-registered types either have no such URL or
their URL pattern is not discoverable via the standard `<app_label>:<model>_list` convention.

What needs fixing:
- Detect (before or during widget rendering) whether the selected `object_type` has a resolvable
  list/filter URL.
- Gracefully degrade: show a disabled selector or a plain text input when no URL can be resolved,
  rather than letting HTMX fire a broken request.
- Applies to both the **assignment link form** selector and any other place the object picker
  widget is used.

### 4. Plugin certification remediation status (NetBox 4.5.x)

External maintainer actions remaining:

- [ ] Add GitHub co-maintainer
- [ ] Add PyPI co-maintainer
- [ ] Confirm NetDev community account
- [ ] Submit certification request issue in `netbox-community/netbox`

