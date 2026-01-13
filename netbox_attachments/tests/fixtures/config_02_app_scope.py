# Configuration 2: App Scope
# Test app scope filtering with common apps
#
# Expected behavior:
# - Attachments enabled on ALL models from: dcim, ipam, circuits, custom_objects
# - Attachments disabled on: tenancy, virtualization, wireless
# - Display mode: additional_tab (default)

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
            'circuits',
            'netbox_custom_objects',
        ],
    }
}
