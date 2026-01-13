# Configuration 3: Model Scope - Specific Models Only
# Test model scope filtering with only specified models
#
# Expected behavior:
# - Attachments enabled ONLY on: Device, Site, IPAddress
# - Attachments disabled on all other models
# - Allows fine-grained control over which models support attachments

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'dcim.device',
            'dcim.site',
            'ipam.ipaddress',
        ],
    }
}
