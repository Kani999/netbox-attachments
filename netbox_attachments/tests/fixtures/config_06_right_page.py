# Configuration 6: Right Page Panel Display
# Test right page panel display mode instead of tab
#
# Expected behavior:
# - Attachments display in right sidebar panel (instead of tab)
# - Applies to all models in scope_filter
# - Complements left_page for balanced layout

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
        'display_default': 'right_page',
    }
}
