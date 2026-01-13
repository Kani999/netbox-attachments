# Configuration 9: Add Button Disabled
# Test with create_add_button disabled
#
# Expected behavior:
# - Attachments tab is present (additional_tab mode)
# - "Add Attachment" button is NOT shown
# - Users cannot add new attachments (view-only mode)
# - Only relevant when display_default='additional_tab'

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
        'display_default': 'additional_tab',
        'create_add_button': False,
    }
}
