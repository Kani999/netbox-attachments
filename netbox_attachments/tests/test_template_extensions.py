"""Unit tests for template display decision helpers."""

from netbox_attachments import template_content


def test_get_display_preference_uses_default_when_unset(monkeypatch):
    monkeypatch.setattr(template_content, "_get_plugin_settings", lambda: {})

    assert template_content.get_display_preference("dcim.device") == "additional_tab"


def test_get_display_preference_uses_model_override(monkeypatch):
    monkeypatch.setattr(
        template_content,
        "_get_plugin_settings",
        lambda: {
            "display_default": "right_page",
            "display_setting": {"dcim.device": "left_page"},
        },
    )

    assert template_content.get_display_preference("dcim.device") == "left_page"
    assert template_content.get_display_preference("dcim.site") == "right_page"


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
