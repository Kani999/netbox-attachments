"""Django system checks.

Warns about settings that were removed in v7.1.0 when ``apps`` and
``allowed_models`` were merged into ``scope_filter`` and ``mode`` became
``applied_scope``. NetBox's ``PluginConfig.validate()`` only fills in *missing*
keys, so a removed setting is not an error: it survives untouched in
``PLUGINS_CONFIG`` while nothing reads it, and the replacement silently falls
back to its default. That default covers several core apps, so part of the
configuration keeps working and the rest fails without a clue (issue #110).
"""

from django.core.checks import Warning, register

from netbox_attachments.utils import _get_plugin_settings

# Removed setting -> the setting that replaced it (v7.1.0).
REMOVED_SETTINGS = {
    "apps": "scope_filter",
    "allowed_models": "scope_filter",
    "mode": "applied_scope",
}

# Neither replacement is a plain rename, so spell out what to actually write:
# `apps` and `allowed_models` were merged into one list (renaming both would make the
# second clobber the first), and `mode` changed its values as well as its name.
EXTRA_HINTS = {
    "apps": "'apps' and 'allowed_models' were merged, so combine both into the single 'scope_filter' list.",
    "allowed_models": "'apps' and 'allowed_models' were merged, so combine both into the single 'scope_filter' list.",
    "mode": "Its values changed too: 'applied_scope' accepts 'app' or 'model', not 'permissive'/'restrictive'.",
}


@register()
def check_removed_settings(app_configs, **kwargs):
    """Warn for each removed plugin setting still present in PLUGINS_CONFIG."""
    plugin_settings = _get_plugin_settings()

    warnings = []
    for index, (removed, replacement) in enumerate(REMOVED_SETTINGS.items(), start=1):
        if removed not in plugin_settings:
            continue

        hint = (
            f"Use '{replacement}' in PLUGINS_CONFIG['netbox_attachments'] instead. "
            f"{EXTRA_HINTS.get(removed, '')} "
            "See https://github.com/Kani999/netbox-attachments/blob/main/docs/configuration.md"
        )
        warnings.append(
            Warning(
                f"netbox-attachments: the '{removed}' setting was removed in v7.1.0 and is ignored. "
                f"'{replacement}' is being used instead, with its default value.",
                hint=" ".join(hint.split()),
                id=f"netbox_attachments.W{index:03d}",
            )
        )

    return warnings
