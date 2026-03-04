"""Unit tests for pending assignment validation logic in NetBoxAttachmentForm.

These tests intentionally mirror the form logic with fakes so they can run in
standalone CI (no NetBox runtime available).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


class _FakeValidationError(Exception):
    pass


def _clean_pending_assignment(instance, get_enabled_object_type_queryset):
    """Replica of NetBoxAttachmentForm.clean() pending-target validation."""
    pending_type_id = getattr(instance, "_pending_object_type_id", None)
    pending_obj_id = getattr(instance, "_pending_object_id", None)

    if pending_type_id is None and pending_obj_id is None:
        return

    if not pending_type_id or not pending_obj_id:
        raise _FakeValidationError("Invalid assignment target context.")

    try:
        pending_type_id = int(pending_type_id)
        pending_obj_id = int(pending_obj_id)
    except (TypeError, ValueError):
        raise _FakeValidationError("Invalid assignment target identifiers.")

    object_type = get_enabled_object_type_queryset().filter(pk=pending_type_id).first()
    if object_type is None:
        raise _FakeValidationError("Attachments are not permitted for this object type.")

    model = object_type.model_class()
    if model is None:
        raise _FakeValidationError("Invalid assignment target model.")

    if not model.objects.filter(pk=pending_obj_id).exists():
        raise _FakeValidationError("The target object does not exist.")

    instance._validated_pending_object_type = object_type
    instance._validated_pending_object_id = pending_obj_id


def _save_pending_assignment(instance, commit, assignment_model, obj):
    """Replica of NetBoxAttachmentForm.save() assignment creation gating."""
    if not commit:
        return

    object_type = getattr(instance, "_validated_pending_object_type", None)
    object_id = getattr(instance, "_validated_pending_object_id", None)
    if object_type is not None and object_id is not None:
        assignment_model.objects.get_or_create(
            attachment=obj,
            object_type=object_type,
            object_id=object_id,
        )


def _enabled_queryset_returning(object_type):
    qs = MagicMock()
    filtered = MagicMock()
    filtered.first.return_value = object_type
    qs.filter.return_value = filtered
    return lambda: qs


def test_clean_accepts_no_pending_assignment_context():
    instance = SimpleNamespace()

    _clean_pending_assignment(instance, get_enabled_object_type_queryset=lambda: MagicMock())

    assert not hasattr(instance, "_validated_pending_object_type")
    assert not hasattr(instance, "_validated_pending_object_id")


@pytest.mark.parametrize(
    ("pending_type_id", "pending_obj_id"),
    [
        (None, "10"),
        ("5", None),
        ("", "10"),
        ("5", ""),
    ],
)
def test_clean_rejects_partial_pending_context(pending_type_id, pending_obj_id):
    instance = SimpleNamespace(
        _pending_object_type_id=pending_type_id,
        _pending_object_id=pending_obj_id,
    )

    with pytest.raises(_FakeValidationError, match="Invalid assignment target context"):
        _clean_pending_assignment(instance, get_enabled_object_type_queryset=lambda: MagicMock())


def test_clean_rejects_non_integer_identifiers():
    instance = SimpleNamespace(
        _pending_object_type_id="not-an-int",
        _pending_object_id="10",
    )

    with pytest.raises(_FakeValidationError, match="Invalid assignment target identifiers"):
        _clean_pending_assignment(instance, get_enabled_object_type_queryset=lambda: MagicMock())


def test_clean_rejects_disallowed_object_type():
    instance = SimpleNamespace(
        _pending_object_type_id="5",
        _pending_object_id="10",
    )

    get_enabled_qs = _enabled_queryset_returning(None)

    with pytest.raises(
        _FakeValidationError,
        match="Attachments are not permitted for this object type",
    ):
        _clean_pending_assignment(instance, get_enabled_qs)


def test_clean_rejects_unresolvable_model_class():
    instance = SimpleNamespace(
        _pending_object_type_id="5",
        _pending_object_id="10",
    )
    object_type = MagicMock()
    object_type.model_class.return_value = None

    get_enabled_qs = _enabled_queryset_returning(object_type)

    with pytest.raises(_FakeValidationError, match="Invalid assignment target model"):
        _clean_pending_assignment(instance, get_enabled_qs)


def test_clean_rejects_missing_target_object():
    instance = SimpleNamespace(
        _pending_object_type_id="5",
        _pending_object_id="10",
    )
    model = MagicMock()
    model.objects.filter.return_value.exists.return_value = False

    object_type = MagicMock()
    object_type.model_class.return_value = model

    get_enabled_qs = _enabled_queryset_returning(object_type)

    with pytest.raises(_FakeValidationError, match="target object does not exist"):
        _clean_pending_assignment(instance, get_enabled_qs)


def test_clean_stores_validated_assignment_target_for_save():
    instance = SimpleNamespace(
        _pending_object_type_id="5",
        _pending_object_id="10",
    )
    model = MagicMock()
    model.objects.filter.return_value.exists.return_value = True

    object_type = MagicMock()
    object_type.model_class.return_value = model

    get_enabled_qs = _enabled_queryset_returning(object_type)

    _clean_pending_assignment(instance, get_enabled_qs)

    assert instance._validated_pending_object_type is object_type
    assert instance._validated_pending_object_id == 10


def test_save_creates_assignment_only_when_commit_and_validated_context():
    assignment_model = MagicMock()
    instance = SimpleNamespace(
        _validated_pending_object_type=MagicMock(),
        _validated_pending_object_id=42,
    )
    attachment_obj = object()

    _save_pending_assignment(instance, True, assignment_model, attachment_obj)

    assignment_model.objects.get_or_create.assert_called_once_with(
        attachment=attachment_obj,
        object_type=instance._validated_pending_object_type,
        object_id=42,
    )


def test_save_skips_assignment_creation_without_commit():
    assignment_model = MagicMock()
    instance = SimpleNamespace(
        _validated_pending_object_type=MagicMock(),
        _validated_pending_object_id=42,
    )

    _save_pending_assignment(instance, False, assignment_model, object())

    assignment_model.objects.get_or_create.assert_not_called()


def test_save_skips_assignment_creation_without_validated_context():
    assignment_model = MagicMock()
    instance = SimpleNamespace()

    _save_pending_assignment(instance, True, assignment_model, object())

    assignment_model.objects.get_or_create.assert_not_called()
