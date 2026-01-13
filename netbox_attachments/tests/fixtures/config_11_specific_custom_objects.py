# Configuration 11: Specific Custom Objects
# Test with attachments on specific custom object types only
#
# Expected behavior:
# - Attachments enabled ONLY on custom object type "attachment"
# - Other custom object types do not have attachments
# - Demonstrates model scope filtering for custom objects
# - Requires netbox_custom_objects plugin installed
#
# Note: Replace 'attachment' with actual CustomObjectType name in your environment

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'netbox_custom_objects.attachment',
        ],
    }
}
