# Configuration 5: Left Page Panel Display
# Test left page panel display mode instead of tab
#
# Expected behavior:
# - Attachments display in left sidebar panel (instead of tab)
# - Applies to all models in scope_filter
# - Useful for models with many tabs or lightweight detail pages

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': [
            'dcim',
            'ipam',
        ],
        'display_default': 'left_page',
    }
}
