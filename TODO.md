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

### 4. Plugin certification remediation status (NetBox 4.5.x)

External maintainer actions remaining:

- [ ] Add GitHub co-maintainer
- [ ] Add PyPI co-maintainer
- [ ] Confirm NetDev community account
- [ ] Submit certification request issue in `netbox-community/netbox`

---

## Completed

### Validate link-form query-param pre-population

**Location:** `views.py` — `NetBoxAttachmentLinkView.alter_object()`

Forward flow (detail page → link form) pre-populates `object_type` and `object_id`
from GET params. Without validation this allowed arbitrary/disallowed object types
and non-existent object IDs to be silently accepted.

**Fix applied:**
- `object_type` is resolved through `get_enabled_object_type_queryset()` — rejects
  disabled/unconfigured types (404).
- `object_id` is coerced to `int` — rejects non-integer strings early.
- Target object existence is verified with `get_object_or_404(model, pk=target_pk)`.
- If `model_class()` returns `None` (uninstalled app), pre-population is skipped.

### Sanitize return_url in GET confirmation context

**Location:** `views.py` — `NetBoxAttachmentAssignmentDeleteView`

The GET handler (delete confirmation page) passed `return_url` from query params directly
into the template context without validation. A malicious link could set `return_url` to
an off-site URL, which the confirmation form would then POST back and redirect to.

**Fix applied:**
- Extracted `_get_safe_return_url()` helper that validates with
  `url_has_allowed_host_and_scheme()` (including `require_https`).
- Both `get()` (confirmation render) and `post()` (redirect after delete) use the helper.

### Guard pre_delete signal against ObjectType.DoesNotExist and redundant .exists()

**Location:** `models.py` — `pre_delete_receiver()`

`get_for_model()` could raise `ObjectType.DoesNotExist` for models not registered with the
content-type framework, crashing object deletion. The `.exists()` guard before `.delete()`
was also redundant since `QuerySet.delete()` is a no-op on empty querysets.

**Fix applied:**
- Wrapped `get_for_model()` in `try/except ObjectType.DoesNotExist`.
- Removed the `.exists()` round-trip; `.delete()` is called directly on the filtered queryset.

### Replace `isinstance(pk, numbers.Integral)` guard with `try/except (TypeError, ValueError)`

**Location:** `models.py` — `pre_delete_receiver()`

The `isinstance(instance.pk, numbers.Integral)` guard (issue #44 workaround) prevented
crashes when a model with a non-integer PK was deleted, since `object_id` is a
`PositiveBigIntegerField`. Verified that Django raises `TypeError`/`ValueError` at the
Python level (not `DataError` from the DB) for non-integer values passed to integer fields.

**Fix applied:**
- Removed `import numbers`.
- Replaced the upfront `isinstance` check with a `try/except (TypeError, ValueError)` around
  the `.filter().delete()` call — semantically identical but more idiomatic.
- Updated `test_signals.py` replica and test to exercise the new code path.
