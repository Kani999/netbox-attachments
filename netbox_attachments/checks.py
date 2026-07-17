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
from netbox_attachments.version import __version__

_MERGED_HINT = "'apps' and 'allowed_models' were merged, so combine both into the single 'scope_filter' list."

# Removed setting -> (replacement, stable check ID, extra hint).
# The IDs are a published contract (CHANGELOG, SILENCED_SYSTEM_CHECKS): never
# renumber or reuse one, even if an entry is dropped from this table.
# `mode` is not a pure rename — its values changed along with its name.
REMOVED_SETTINGS = {
    "apps": ("scope_filter", "netbox_attachments.W001", _MERGED_HINT),
    "allowed_models": ("scope_filter", "netbox_attachments.W002", _MERGED_HINT),
    "mode": (
        "applied_scope",
        "netbox_attachments.W003",
        "Its values changed too: 'applied_scope' accepts 'app' or 'model', not 'permissive'/'restrictive'.",
    ),
}

# Pinned to this release's tag so the linked page describes the settings this
# install actually has; a moving main-branch URL would drift or 404.
_DOCS_URL = f"https://github.com/Kani999/netbox-attachments/blob/v{__version__}/docs/configuration.md"


@register()
def check_removed_settings(app_configs, **kwargs):
    """Warn for each removed plugin setting still present in PLUGINS_CONFIG."""
    plugin_settings = _get_plugin_settings()

    warnings = []
    for removed, (replacement, check_id, extra_hint) in REMOVED_SETTINGS.items():
        if removed not in plugin_settings:
            continue

        if replacement in plugin_settings:
            effect = f"Your configured '{replacement}' is in effect; delete the stale '{removed}' key."
        else:
            effect = f"'{replacement}' falls back to its default value."

        hint = f"Use '{replacement}' in PLUGINS_CONFIG['netbox_attachments'] instead. {extra_hint} See {_DOCS_URL}"
        warnings.append(
            Warning(
                f"netbox-attachments: the '{removed}' setting was removed in v7.1.0 and is ignored. {effect}",
                hint=hint,
                id=check_id,
            )
        )

    return warnings
