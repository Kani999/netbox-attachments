"""Unit tests for the removed-settings system check."""

from netbox_attachments import checks


def test_no_warnings_for_modern_config(monkeypatch):
    monkeypatch.setattr(
        checks,
        "_get_plugin_settings",
        lambda: {
            "applied_scope": "app",
            "scope_filter": ["dcim", "netbox_custom_objects"],
            "display_default": "additional_tab",
        },
    )

    assert checks.check_removed_settings(None) == []


def test_no_warnings_when_plugin_unconfigured(monkeypatch):
    monkeypatch.setattr(checks, "_get_plugin_settings", lambda: {})

    assert checks.check_removed_settings(None) == []


def test_apps_setting_warns_and_names_replacement(monkeypatch):
    """'apps' is silently ignored without this check."""
    monkeypatch.setattr(
        checks,
        "_get_plugin_settings",
        lambda: {"apps": ["dcim", "netbox_custom_objects"], "display_default": "additional_tab"},
    )

    warnings = checks.check_removed_settings(None)

    assert len(warnings) == 1
    assert "'apps' setting was removed" in warnings[0].msg
    assert "scope_filter" in warnings[0].hint


def test_allowed_models_setting_warns(monkeypatch):
    monkeypatch.setattr(checks, "_get_plugin_settings", lambda: {"allowed_models": ["dcim.device"]})

    warnings = checks.check_removed_settings(None)

    assert len(warnings) == 1
    assert "scope_filter" in warnings[0].hint


def test_mode_setting_warns_that_values_also_changed(monkeypatch):
    monkeypatch.setattr(checks, "_get_plugin_settings", lambda: {"mode": "permissive"})

    warnings = checks.check_removed_settings(None)

    assert len(warnings) == 1
    assert "applied_scope" in warnings[0].hint
    assert "permissive" in warnings[0].hint


def test_check_ids_are_stable_not_positional(monkeypatch):
    """W-ids are a published contract (SILENCED_SYSTEM_CHECKS); they must not renumber
    when earlier table entries are absent from the user's config."""
    monkeypatch.setattr(checks, "_get_plugin_settings", lambda: {"mode": "permissive"})

    warnings = checks.check_removed_settings(None)

    assert [w.id for w in warnings] == ["netbox_attachments.W003"]


def test_message_acknowledges_configured_replacement(monkeypatch):
    """A half-migrated config (old and new key both set) must not claim the default is in use."""
    monkeypatch.setattr(
        checks,
        "_get_plugin_settings",
        lambda: {"apps": ["dcim"], "scope_filter": ["dcim", "netbox_custom_objects"]},
    )

    warnings = checks.check_removed_settings(None)

    assert len(warnings) == 1
    assert "Your configured 'scope_filter' is in effect" in warnings[0].msg
    assert "default" not in warnings[0].msg


def test_each_removed_setting_warns_once_with_a_unique_id(monkeypatch):
    monkeypatch.setattr(
        checks,
        "_get_plugin_settings",
        lambda: {"apps": ["dcim"], "allowed_models": ["dcim.device"], "mode": "permissive"},
    )

    warnings = checks.check_removed_settings(None)

    assert len(warnings) == 3
    assert len({w.id for w in warnings}) == 3
