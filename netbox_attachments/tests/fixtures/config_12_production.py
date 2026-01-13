# Configuration 12: Production Config
# Recommended configuration for production use
#
# Expected behavior:
# - Attachments enabled on common infrastructure models (dcim, ipam, circuits, tenancy, virtualization, wireless)
# - Custom objects supported if plugin installed
# - Attachments display in convenient additional_tab mode
# - Add button enabled for users to upload attachments

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
            'tenancy',
            'virtualization',
            'wireless',
            'netbox_custom_objects',
        ],
        'display_default': 'additional_tab',
        'create_add_button': True,
    }
}
