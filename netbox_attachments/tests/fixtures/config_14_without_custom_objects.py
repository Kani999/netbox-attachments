# Configuration 14: Without Custom Objects Plugin
# Test attachments when custom_objects plugin is NOT installed
#
# Expected behavior:
# - Attachments enabled on standard NetBox models (dcim, ipam, circuits, tenancy, virtualization, wireless)
# - Custom objects not available (plugin not in PLUGINS list)
# - Plugin gracefully handles missing netbox_custom_objects
# - No errors or warnings related to missing plugin

PLUGINS = [
    'netbox_attachments',
    # 'netbox_custom_objects',  # Commented out - plugin not installed
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': [
            'dcim',
            'ipam',
            'circuits',
            'tenancy',
            'virtualization',
            'wireless',
        ],
    }
}
