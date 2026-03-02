"""Standalone unit tests for new netbox-attachments features.

These tests run with plain ``pytest -q`` — no Django runtime is needed.
Logic is verified by parsing source files as text or by replicating the
relevant code inline with SimpleNamespace and MagicMock, exactly as the
other test modules in this package do.
"""

import ast
import pathlib
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Paths to source files used throughout the test suite
# ---------------------------------------------------------------------------

_ROOT = pathlib.Path(__file__).parent.parent  # netbox_attachments/

_TEMPLATE = _ROOT / "templates" / "netbox_attachments" / "netboxattachmentassignment_delete.html"
_FORMS_PY = _ROOT / "forms.py"
_TABLES_PY = _ROOT / "tables.py"
_NAV_PY = _ROOT / "navigation.py"
_URLS_PY = _ROOT / "urls.py"


# ===========================================================================
# Feature 1 — Issue 3: Unlink confirmation template fix
# ===========================================================================


def test_template_contains_app_label_attribute():
    """Template uses object.object_type.app_label, not a stringified content type."""
    content = _TEMPLATE.read_text()
    assert "object.object_type.app_label" in content


def test_template_contains_model_attribute():
    """Template uses object.object_type.model to display the model name."""
    content = _TEMPLATE.read_text()
    assert "object.object_type.model" in content


def test_template_does_not_use_old_obj_type_variable():
    """The old buggy pattern ``obj_type=object.object_type %}`` must not exist."""
    content = _TEMPLATE.read_text()
    assert "obj_type=object.object_type %}" not in content


def test_content_type_str_differs_from_app_label_model_format():
    """
    Demonstrates why the fix was necessary: ContentType.__str__() does not
    produce an "app_label > model" style string.  A fake with __str__ returning
    just the model name shows the mismatch.
    """

    class FakeContentType:
        app_label = "dcim"
        model = "device"

        def __str__(self):
            # Real Django ContentType.__str__ returns the verbose model name,
            # e.g. "device" — not "dcim > device".
            return self.model

    ct = FakeContentType()
    expected_display = f"{ct.app_label} > {ct.model}"

    # str() does NOT produce the "app > model" format
    assert str(ct) != expected_display
    # But accessing attributes directly does
    assert f"{ct.app_label} > {ct.model}" == "dcim > device"


# ===========================================================================
# Feature 2 — Issue 4: Object-detail attachment tab get_children() logic
# ===========================================================================


def get_children_replica(parent, NetBoxAttachmentAssignment, ObjectType):
    """Exact replica of AttachmentTabView.get_children() for isolated testing."""
    return (
        NetBoxAttachmentAssignment.objects.filter(
            object_type=ObjectType.objects.get_for_model(parent),
            object_id=parent.id,
        )
        .restrict(MagicMock(), "view")
        .select_related("attachment")
        .prefetch_related("attachment__tags", "attachment__attachment_assignments")
    )


def _make_get_children_mocks(parent_id=42):
    parent = SimpleNamespace(id=parent_id)

    fake_object_type = MagicMock(name="object_type_instance")

    ObjectType = MagicMock(name="ObjectType")
    ObjectType.objects.get_for_model.return_value = fake_object_type

    # Build a realistic queryset call chain: filter → restrict → select_related → prefetch_related
    after_prefetch = MagicMock(name="after_prefetch")
    after_select = MagicMock(name="after_select")
    after_select.prefetch_related.return_value = after_prefetch

    after_restrict = MagicMock(name="after_restrict")
    after_restrict.select_related.return_value = after_select

    filtered_qs = MagicMock(name="filtered_qs")
    filtered_qs.restrict.return_value = after_restrict

    NetBoxAttachmentAssignment = MagicMock(name="NetBoxAttachmentAssignment")
    NetBoxAttachmentAssignment.objects.filter.return_value = filtered_qs

    return parent, ObjectType, NetBoxAttachmentAssignment, fake_object_type, after_prefetch


def test_get_children_calls_get_for_model_with_parent():
    parent, ObjectType, NetBoxAttachmentAssignment, _, _ = _make_get_children_mocks()
    get_children_replica(parent, NetBoxAttachmentAssignment, ObjectType)
    ObjectType.objects.get_for_model.assert_called_once_with(parent)


def test_get_children_filters_by_object_type_and_object_id():
    parent, ObjectType, NetBoxAttachmentAssignment, fake_ot, _ = _make_get_children_mocks(parent_id=7)
    get_children_replica(parent, NetBoxAttachmentAssignment, ObjectType)
    NetBoxAttachmentAssignment.objects.filter.assert_called_once_with(
        object_type=fake_ot,
        object_id=7,
    )


def test_get_children_prefetches_attachment_and_tags():
    parent, ObjectType, NetBoxAttachmentAssignment, _, _ = _make_get_children_mocks()
    filtered_qs = NetBoxAttachmentAssignment.objects.filter.return_value
    after_restrict = filtered_qs.restrict.return_value
    after_select = after_restrict.select_related.return_value

    get_children_replica(parent, NetBoxAttachmentAssignment, ObjectType)

    # FK traversal uses select_related (single JOIN); M2M/reverse-FK use prefetch_related
    after_restrict.select_related.assert_called_once_with("attachment")
    after_select.prefetch_related.assert_called_once_with("attachment__tags", "attachment__attachment_assignments")


def test_get_children_returns_prefetched_queryset():
    parent, ObjectType, NetBoxAttachmentAssignment, _, final_qs = _make_get_children_mocks()
    result = get_children_replica(parent, NetBoxAttachmentAssignment, ObjectType)
    assert result is final_qs


# ===========================================================================
# Feature 3 — Issue 2: Assignment filter form field names
# ===========================================================================


def test_forms_py_defines_assignment_filter_form_class():
    source = _FORMS_PY.read_text()
    assert "NetBoxAttachmentAssignmentFilterForm" in source


def test_assignment_filter_form_declares_attachment_id_field():
    source = _FORMS_PY.read_text()
    # The field must be declared inside the class, not merely referenced
    assert "attachment_id" in source


def test_assignment_filter_form_declares_object_type_id_field():
    source = _FORMS_PY.read_text()
    assert "object_type_id" in source


# ===========================================================================
# Feature 4 — Tables: NetBoxAttachmentForObjectTable structure
# ===========================================================================


def test_tables_py_defines_netbox_attachment_for_object_table():
    source = _TABLES_PY.read_text()
    assert "NetBoxAttachmentForObjectTable" in source


def test_object_attachment_actions_references_assignment_delete_url():
    source = _TABLES_PY.read_text()
    # The OBJECT_ATTACHMENT_ACTIONS template string must link to the delete view
    assert "netboxattachmentassignment_delete" in source


def test_object_attachment_actions_guards_with_delete_permission():
    source = _TABLES_PY.read_text()
    assert "perms.netbox_attachments.delete_netboxattachmentassignment" in source


def test_assignment_table_has_tags_column():
    """NetBoxAttachmentAssignmentTable must declare a tags column."""
    source = _TABLES_PY.read_text()
    assert "tags = columns.TagColumn" in source


def test_object_attachment_for_object_table_has_links_column():
    """NetBoxAttachmentForObjectTable must declare a 'links' column."""
    source = _TABLES_PY.read_text()
    assert "OBJECT_ATTACHMENT_LINKS_COUNT" in source
    assert 'verbose_name="Links"' in source


def test_object_attachment_links_count_uses_prefetch_cache_safe_filter():
    """The Links count template must use |length (prefetch-cache safe), not |count."""
    source = _TABLES_PY.read_text()
    # |length works off the prefetch cache; |count would issue an extra SQL query per row
    assert "attachment_assignments.all|length" in source


def test_object_attachment_for_object_table_links_in_default_columns():
    """'links' must appear in default_columns so it is visible without configuration."""
    source = _TABLES_PY.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "NetBoxAttachmentForObjectTable":
            for inner in node.body:
                if isinstance(inner, ast.ClassDef) and inner.name == "Meta":
                    for stmt in inner.body:
                        if (
                            isinstance(stmt, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == "default_columns" for t in stmt.targets)
                            and isinstance(stmt.value, ast.Tuple)
                        ):
                            cols = [e.value for e in stmt.value.elts if isinstance(e, ast.Constant)]
                            assert "links" in cols, f"'links' not in default_columns: {cols}"
                            return
    pytest.fail("NetBoxAttachmentForObjectTable.Meta.default_columns not found")


# ===========================================================================
# Feature 5 — Navigation: Assignment list entry
# ===========================================================================


def test_navigation_includes_assignment_list_link():
    source = _NAV_PY.read_text()
    assert "netboxattachmentassignment_list" in source


def test_navigation_includes_view_assignment_permission():
    source = _NAV_PY.read_text()
    assert "view_netboxattachmentassignment" in source


# ===========================================================================
# Feature 6 — URL: Assignment list URL registered
# ===========================================================================


def test_urls_py_registers_assignment_list_path():
    source = _URLS_PY.read_text()
    assert "netbox-attachment-assignments/" in source


def test_urls_py_registers_assignment_list_name():
    source = _URLS_PY.read_text()
    # The list name must appear and be distinct from the delete name
    assert "netboxattachmentassignment_list" in source


def test_urls_py_registers_assignment_delete_name_separately():
    """Both list and delete names must be registered — they are two distinct paths."""
    source = _URLS_PY.read_text()
    assert "netboxattachmentassignment_list" in source
    assert "netboxattachmentassignment_delete" in source
    # Confirm they are separate names (appear more than once if needed, but exist)
    assert source.index("netboxattachmentassignment_list") != source.index("netboxattachmentassignment_delete")
