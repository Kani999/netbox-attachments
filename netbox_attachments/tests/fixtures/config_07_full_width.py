# Configuration 7: Full Width Page Display
# Test full width page panel display mode
#
# Expected behavior:
# - Attachments display in full-width panel at bottom of page
# - Applies to all models in scope_filter
# - Best for models where attachments are the primary content

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
        'display_default': 'full_width_page',
    }
}
