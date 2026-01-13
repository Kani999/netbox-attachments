# Configuration 10: Custom Objects Only
# Test with attachments enabled ONLY for custom objects
#
# Expected behavior:
# - Attachments enabled on ALL custom object types
# - Attachments disabled on standard NetBox models (dcim, ipam, etc.)
# - Useful for testing custom objects integration
# - Requires netbox_custom_objects plugin installed

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': [
            'netbox_custom_objects',
        ],
    }
}
