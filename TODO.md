# TODO / Backlog

Lightweight backlog for future maintenance and improvement tasks.

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

