# Configuration 4: Model Scope - Mixed Mode
# Test model scope with both app-level and specific model filters
#
# Expected behavior:
# - ALL dcim models enabled (app-level)
# - ONLY ipam.ipaddress enabled (specific model)
# - ONLY virtualization.cluster enabled (specific model)
# - Demonstrates mixed filtering capability

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'model',
        'scope_filter': [
            'dcim',                      # Entire app
            'ipam.ipaddress',            # Specific model
            'virtualization.cluster',    # Specific model
        ],
    }
}
