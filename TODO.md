# TODO / Backlog

Lightweight backlog for future maintenance and improvement tasks.

---

## Open Items

### 1. Integer PK workaround in `pre_delete` signal

**Location:** `models.py:158-161`

```python
# Workaround: only run signals on Models where PK is Integral
# https://github.com/Kani999/netbox-attachments/issues/44
if not isinstance(instance.pk, numbers.Integral):
    return
```

With the new schema (`NetBoxAttachmentAssignment.object_id` is `PositiveBigIntegerField`),
non-integer PK objects can never have assignments, so the guard is still logically correct.
However it is a broad workaround — the signal fires on every model deletion in Django, even
when no assignments exist.

**Investigate before removing the guard:** `PositiveBigIntegerField` — Django may raise
`ValueError`/`DataError` on some DB backends if a non-integer PK (e.g. UUID, string) is
passed as `object_id` in a queryset filter. Verify whether Django/PostgreSQL handles this
gracefully (returns empty queryset) or raises, before dropping the `isinstance` check.

A proper future fix could:
- Cache/register only content types that actually have assignments, so the signal can
  early-exit cheaply without hitting the DB.
- Or accept the current behaviour as "good enough" since the DB query is already guarded
by the `assignments.exists()` short-circuit below.

The `numbers` import can be removed once this is addressed.

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
