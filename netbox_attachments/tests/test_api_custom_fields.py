"""Regression guard: custom_fields must be exposed by the REST API serializers.

NetBox declares ``custom_fields`` on the CustomFieldModelSerializer base class,
and DRF exempts base-class fields from the "declared fields must appear in
Meta.fields" assertion — so omitting it from ``Meta.fields`` silently drops the
field instead of crashing. The UI (forms, tables, filtersets) picks up custom
fields automatically, which makes the omission invisible everywhere except the
API. These tests parse the serializer source, in line with the rest of this
standalone suite.
"""

import ast
import pathlib

_SERIALIZERS_PY = pathlib.Path(__file__).parent.parent / "api" / "serializers.py"


def _meta_list(serializer_name: str, attr: str):
    """Return the literal list/tuple assigned to Meta.<attr> of a serializer class."""
    tree = ast.parse(_SERIALIZERS_PY.read_text())
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == serializer_name):
            continue
        for child in node.body:
            if not (isinstance(child, ast.ClassDef) and child.name == "Meta"):
                continue
            for stmt in child.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == attr for t in stmt.targets)
                    and isinstance(stmt.value, (ast.List, ast.Tuple))
                ):
                    return [el.value for el in stmt.value.elts if isinstance(el, ast.Constant)]
    raise AssertionError(f"Meta.{attr} not found on {serializer_name}")


def test_attachment_serializer_exposes_custom_fields():
    assert "custom_fields" in _meta_list("NetBoxAttachmentSerializer", "fields")


def test_assignment_serializer_exposes_custom_fields():
    assert "custom_fields" in _meta_list("NetBoxAttachmentAssignmentSerializer", "fields")


def test_brief_fields_stay_lean():
    """Nested (brief) representations follow NetBox core and omit custom_fields."""
    assert "custom_fields" not in _meta_list("NetBoxAttachmentSerializer", "brief_fields")
    assert "custom_fields" not in _meta_list("NetBoxAttachmentAssignmentSerializer", "brief_fields")
