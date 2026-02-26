"""Unit tests for standalone pytest execution."""

from types import SimpleNamespace

from netbox_attachments import utils


class FakeModel:
    def __init__(self, app_label, model_name):
        self._meta = SimpleNamespace(app_label=app_label, model_name=model_name, abstract=False)


class FakeInstance:
    def __init__(self, name):
        self.name = name


def test_package_import_is_safe_outside_netbox():
    import netbox_attachments

    assert hasattr(netbox_attachments, "NetBoxAttachmentsConfig")


def test_choice_default_returns_value_when_valid():
    assert utils.choice_default("model", ("app", "model"), "app") == "model"


def test_choice_default_returns_default_when_invalid():
    assert utils.choice_default("invalid", ("app", "model"), "app") == "app"


def test_attachment_upload_preserves_extension_when_renamed():
    instance = FakeInstance("new-name")

    upload_path = utils.attachment_upload(instance, "old-name.tar.gz")

    assert upload_path == "netbox-attachments/new-name.tar.gz"


def test_attachment_upload_keeps_original_filename_when_name_matches():
    instance = FakeInstance("same-name.txt")

    upload_path = utils.attachment_upload(instance, "same-name.txt")

    assert upload_path == "netbox-attachments/same-name.txt"


def test_validate_object_type_app_scope(monkeypatch):
    monkeypatch.setattr(
        utils,
        "_get_plugin_settings",
        lambda: {"applied_scope": "app", "scope_filter": ["dcim", "ipam"]},
    )

    assert utils.validate_object_type(FakeModel("dcim", "device")) is True
    assert utils.validate_object_type(FakeModel("ipam", "ipaddress")) is True
    assert utils.validate_object_type(FakeModel("tenancy", "tenant")) is False


def test_validate_object_type_model_scope_specific_and_mixed(monkeypatch):
    monkeypatch.setattr(
        utils,
        "_get_plugin_settings",
        lambda: {
            "applied_scope": "model",
            "scope_filter": ["dcim", "ipam.ipaddress", "virtualization.cluster"],
        },
    )

    assert utils.validate_object_type(FakeModel("dcim", "device")) is True
    assert utils.validate_object_type(FakeModel("ipam", "ipaddress")) is True
    assert utils.validate_object_type(FakeModel("virtualization", "cluster")) is True
    assert utils.validate_object_type(FakeModel("ipam", "prefix")) is False


def test_validate_object_type_invalid_config_graceful(monkeypatch):
    monkeypatch.setattr(
        utils,
        "_get_plugin_settings",
        lambda: {"applied_scope": "invalid", "scope_filter": "dcim"},
    )

    assert utils.validate_object_type(FakeModel("dcim", "device")) is False


def test_validate_object_type_empty_scope_disables_all(monkeypatch):
    monkeypatch.setattr(
        utils,
        "_get_plugin_settings",
        lambda: {"applied_scope": "model", "scope_filter": []},
    )

    assert utils.validate_object_type(FakeModel("dcim", "device")) is False
    assert utils.validate_object_type(FakeModel("ipam", "ipaddress")) is False
