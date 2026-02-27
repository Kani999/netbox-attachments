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

### 4. Plugin certification remediation status (NetBox 4.5.x)

External maintainer actions remaining:

- [ ] Add GitHub co-maintainer
- [ ] Add PyPI co-maintainer
- [ ] Confirm NetDev community account
- [ ] Submit certification request issue in `netbox-community/netbox`

