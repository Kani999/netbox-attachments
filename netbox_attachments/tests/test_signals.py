"""Unit tests for pre_delete signal handler.

These tests replicate the handler logic using mocks to avoid importing
netbox_attachments.models (which requires a live NetBox/Django environment).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Inline replica of pre_delete_receiver — keeps tests runnable without Django
# ---------------------------------------------------------------------------

class _FakeDoesNotExist(Exception):
    pass


def _make_handler(ObjectType, NetBoxAttachmentAssignment, own_models):
    """
    Returns a pre_delete_receiver function equivalent to the one in models.py,
    wired to the provided fakes.  Used so tests can verify the exact logic path
    without requiring a live Django/NetBox environment.
    """

    def pre_delete_receiver(sender, instance, **kwargs):  # noqa: ARG001
        if sender in own_models:
            return
        try:
            object_type = ObjectType.objects.get_for_model(instance)
        except ObjectType.DoesNotExist:
            return
        try:
            NetBoxAttachmentAssignment.objects.filter(
                object_type_id=object_type.id, object_id=instance.pk
            ).delete()
        except (TypeError, ValueError):
            return

    return pre_delete_receiver


def make_fake_instance(pk=1):
    return SimpleNamespace(pk=pk)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pre_delete_receiver_handles_unregistered_model_gracefully():
    """
    When get_for_model() raises DoesNotExist the handler returns silently.
    """
    FakeObjectType = MagicMock()
    FakeObjectType.DoesNotExist = _FakeDoesNotExist
    FakeObjectType.objects.get_for_model.side_effect = _FakeDoesNotExist

    FakeAssignment = MagicMock()

    handler = _make_handler(FakeObjectType, FakeAssignment, own_models=())

    instance = make_fake_instance(pk=42)
    handler(sender=object, instance=instance)  # must not raise

    FakeAssignment.objects.filter.assert_not_called()


def test_pre_delete_receiver_skips_exists_check_and_calls_delete_once():
    """
    delete() is called directly on the filtered queryset with no .exists() call.
    """
    fake_ot = MagicMock()
    fake_ot.id = 99

    FakeObjectType = MagicMock()
    FakeObjectType.DoesNotExist = _FakeDoesNotExist
    FakeObjectType.objects.get_for_model.return_value = fake_ot

    mock_qs = MagicMock()
    FakeAssignment = MagicMock()
    FakeAssignment.objects.filter.return_value = mock_qs

    handler = _make_handler(FakeObjectType, FakeAssignment, own_models=())

    instance = make_fake_instance(pk=7)
    handler(sender=object, instance=instance)

    FakeAssignment.objects.filter.assert_called_once_with(object_type_id=99, object_id=7)
    mock_qs.delete.assert_called_once()
    mock_qs.exists.assert_not_called()


def test_pre_delete_receiver_skips_own_models():
    """Handler is a no-op when sender is one of the plugin's own models."""
    FakeObjectType = MagicMock()
    FakeObjectType.DoesNotExist = _FakeDoesNotExist

    FakeAttachment = object()
    FakeAssignment = MagicMock()

    handler = _make_handler(FakeObjectType, FakeAssignment, own_models=(FakeAttachment,))

    instance = make_fake_instance(pk=1)
    handler(sender=FakeAttachment, instance=instance)

    FakeObjectType.objects.get_for_model.assert_not_called()
    FakeAssignment.objects.filter.assert_not_called()


def test_pre_delete_receiver_skips_non_integral_pk():
    """Handler is a no-op when the instance PK is not an integer (TypeError/ValueError from filter)."""
    fake_ot = MagicMock()
    fake_ot.id = 5

    FakeObjectType = MagicMock()
    FakeObjectType.DoesNotExist = _FakeDoesNotExist
    FakeObjectType.objects.get_for_model.return_value = fake_ot

    mock_qs = MagicMock()
    mock_qs.delete.side_effect = TypeError("Field expected a number")
    FakeAssignment = MagicMock()
    FakeAssignment.objects.filter.return_value = mock_qs

    handler = _make_handler(FakeObjectType, FakeAssignment, own_models=())

    instance = make_fake_instance(pk="not-an-int")
    handler(sender=object, instance=instance)  # must not raise

    FakeObjectType.objects.get_for_model.assert_called_once_with(instance)
    FakeAssignment.objects.filter.assert_called_once_with(object_type_id=5, object_id="not-an-int")
    mock_qs.delete.assert_called_once()
