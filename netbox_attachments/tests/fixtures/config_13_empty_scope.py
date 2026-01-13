# Configuration 13: Empty Scope Filter
# Test with empty scope_filter (attachments disabled everywhere)
#
# Expected behavior:
# - Attachments disabled on ALL models
# - No attachment tabs or panels visible
# - Useful for testing plugin disabling without removing from PLUGINS
# - Edge case: effective way to disable plugin without uninstalling

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [],
    }
}
