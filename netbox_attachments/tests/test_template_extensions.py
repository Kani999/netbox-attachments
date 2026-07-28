"""Unit tests for template display decision helpers."""

from netbox_attachments import template_content
from netbox_attachments.tests.conftest import fake_model


class FakeExtension:
    """Stands in for PluginTemplateExtension: the two attributes the panel body touches."""

    def __init__(self, obj, raises=False):
        self.context = {"object": obj}
        self.raises = raises
        self.rendered = []

    def render(self, template_name, extra_context=None):
        if self.raises:
            raise RuntimeError("template blew up")
        self.rendered.append(template_name)
        return f"<panel:{template_name}>"


def make_object(app_label="netbox_custom_objects", model_name="table3model"):
    """An instance whose type() carries _meta, since the panel inspects the class."""
    return fake_model(app_label, model_name)()


def stub_custom_object_support(monkeypatch, *, is_custom_object=True, in_scope=True, settings=None):
    """
    Pin the collaborators the panel gates on. The real ones need netbox_custom_objects
    installed, which the standalone pytest run does not have.
    """
    monkeypatch.setattr(template_content, "is_custom_object_model", lambda model: is_custom_object)
    monkeypatch.setattr(template_content, "validate_object_type", lambda model: in_scope)
    monkeypatch.setattr(
        template_content,
        "_get_plugin_settings",
        lambda: settings if settings is not None else {"display_default": "full_width_page"},
    )


def test_display_preference_uses_default_when_unset(monkeypatch):
    monkeypatch.setattr(template_content, "_get_plugin_settings", lambda: {})

    assert template_content.resolve_effective_display_preference("dcim.device") == "additional_tab"


def test_display_preference_uses_model_override(monkeypatch):
    monkeypatch.setattr(
        template_content,
        "_get_plugin_settings",
        lambda: {
            "display_default": "right_page",
            "display_setting": {"dcim.device": "left_page"},
        },
    )

    assert template_content.resolve_effective_display_preference("dcim.device") == "left_page"
    assert template_content.resolve_effective_display_preference("dcim.site") == "right_page"


def test_resolver_forces_full_width_for_custom_objects_at_the_resolver_layer(monkeypatch):
    """The no-tab-for-custom-objects rule must hold for ANY caller of the shared
    resolver — not just because the startup loop happens to skip custom objects."""
    stub_custom_object_support(monkeypatch, settings={"display_default": "additional_tab"})
    model = fake_model("netbox_custom_objects", "table3model")

    assert template_content.resolve_display_preference_for_model(model) == "full_width_page"


def test_resolve_effective_display_preference_for_custom_object_auto_converts():
    plugin_settings = {"display_default": "additional_tab", "display_setting": {}}

    assert (
        template_content.resolve_effective_display_preference(
            "netbox_custom_objects.attachment",
            is_custom_object=True,
            plugin_settings=plugin_settings,
        )
        == "full_width_page"
    )


def test_resolve_effective_display_preference_for_non_custom_keeps_tab_mode():
    plugin_settings = {"display_default": "additional_tab", "display_setting": {}}

    assert (
        template_content.resolve_effective_display_preference(
            "dcim.device",
            is_custom_object=False,
            plugin_settings=plugin_settings,
        )
        == "additional_tab"
    )


def test_get_template_extensions_returns_empty_outside_netbox_runtime():
    extensions = template_content.get_template_extensions()

    assert isinstance(extensions, list)
    assert extensions == []


def test_custom_object_panel_renders_at_configured_position(monkeypatch):
    stub_custom_object_support(monkeypatch, settings={"display_default": "full_width_page"})
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "full_width_page") == (
        "<panel:netbox_attachments/netbox_attachment_panel.html>"
    )
    assert template_content.render_panel(extension, "left_page") == ""
    assert template_content.render_panel(extension, "right_page") == ""


def test_custom_object_panel_honours_left_page_setting(monkeypatch):
    stub_custom_object_support(monkeypatch, settings={"display_default": "left_page"})
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "left_page") != ""
    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_falls_back_from_additional_tab_to_full_width(monkeypatch):
    """Custom object pages cannot host a tab, so additional_tab must land on full_width_page."""
    stub_custom_object_support(monkeypatch, settings={"display_default": "additional_tab"})
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "full_width_page") != ""
    assert template_content.render_panel(extension, "left_page") == ""


def test_panel_serves_standard_in_scope_model(monkeypatch):
    """The consolidated panel serves standard models too, not only custom objects."""
    stub_custom_object_support(monkeypatch, is_custom_object=False, settings={"display_default": "full_width_page"})
    extension = FakeExtension(make_object("dcim", "device"))

    assert template_content.render_panel(extension, "full_width_page") != ""


def test_panel_skips_standard_model_out_of_scope(monkeypatch):
    stub_custom_object_support(
        monkeypatch, is_custom_object=False, in_scope=False, settings={"display_default": "full_width_page"}
    )
    extension = FakeExtension(make_object("dcim", "device"))

    assert template_content.render_panel(extension, "full_width_page") == ""
    assert extension.rendered == []


def test_panel_skips_additional_tab_models(monkeypatch):
    """additional_tab models get a startup-registered tab, never a render-time panel."""
    stub_custom_object_support(monkeypatch, is_custom_object=False, settings={"display_default": "additional_tab"})
    extension = FakeExtension(make_object("dcim", "device"))

    for position in ("left_page", "right_page", "full_width_page"):
        assert template_content.render_panel(extension, position) == ""
    assert extension.rendered == []


def test_custom_object_panel_skips_out_of_scope_custom_objects(monkeypatch):
    stub_custom_object_support(monkeypatch, in_scope=False)
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_skips_when_no_object_in_context(monkeypatch):
    """PluginTemplateExtension.render reads context['object'], which can be absent or None."""
    stub_custom_object_support(monkeypatch)
    extension = FakeExtension(None)

    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_skips_objects_without_meta(monkeypatch):
    """NetBox offers global extensions whatever is in context; it need not be a model."""
    stub_custom_object_support(monkeypatch)
    extension = FakeExtension("not a model")

    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_declines_model_classes(monkeypatch):
    """A model CLASS in context must be declined, not crash: type(cls) is the metaclass,
    which has no _meta — the guard must test the class the code actually reads."""
    stub_custom_object_support(monkeypatch)
    model_class = type(make_object())
    extension = FakeExtension(model_class)

    assert template_content.render_panel(extension, "full_width_page") == ""
    assert extension.rendered == []


def test_custom_object_panel_swallows_render_errors(monkeypatch):
    stub_custom_object_support(monkeypatch)
    extension = FakeExtension(make_object(), raises=True)

    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_display_setting_uses_the_type_name_key(monkeypatch):
    """
    display_setting must accept the identifier scope_filter uses (the type name), not the
    internal table*model name, or the documented key silently never matches.
    """
    stub_custom_object_support(
        monkeypatch,
        settings={
            "display_default": "full_width_page",
            "display_setting": {"netbox_custom_objects.cotab2_asset": "left_page"},
        },
    )
    monkeypatch.setattr(
        template_content,
        "custom_object_identifier",
        lambda model: "netbox_custom_objects.cotab2_asset",
    )
    extension = FakeExtension(make_object(model_name="table134model"))

    assert template_content.render_panel(extension, "left_page") != ""
    assert template_content.render_panel(extension, "full_width_page") == ""


def test_custom_object_panel_skips_identifier_lookup_without_display_setting(monkeypatch):
    """Resolving the type name costs a query, so it must not run when no override exists."""
    calls = []
    stub_custom_object_support(monkeypatch, settings={"display_default": "full_width_page"})
    monkeypatch.setattr(template_content, "custom_object_identifier", lambda model: calls.append(model) or None)
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "full_width_page") != ""
    assert calls == []


def test_custom_object_panel_falls_back_when_identifier_unresolvable(monkeypatch):
    stub_custom_object_support(
        monkeypatch,
        settings={
            "display_default": "full_width_page",
            "display_setting": {"netbox_custom_objects.something_else": "left_page"},
        },
    )
    monkeypatch.setattr(template_content, "custom_object_identifier", lambda model: None)
    extension = FakeExtension(make_object())

    assert template_content.render_panel(extension, "full_width_page") != ""


def test_custom_object_panel_defers_scope_check_until_position_matches(monkeypatch):
    """
    validate_object_type can query the database, so it must run only for the one hook
    that will render — not once per hook.
    """
    calls = []
    stub_custom_object_support(monkeypatch, settings={"display_default": "full_width_page"})
    monkeypatch.setattr(template_content, "validate_object_type", lambda model: calls.append(model) or True)
    extension = FakeExtension(make_object())

    for position in ("left_page", "right_page", "full_width_page"):
        template_content.render_panel(extension, position)

    assert len(calls) == 1
