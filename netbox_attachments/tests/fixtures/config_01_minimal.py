# Configuration 1: Minimal (Defaults)
# Use this to test plugin with all default settings
#
# Expected behavior:
# - applied_scope: 'app' (default)
# - scope_filter: Default list (dcim, ipam, circuits, tenancy, virtualization, wireless)
# - display_default: 'additional_tab' (default)
# - create_add_button: True (default)

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        # All settings use defaults - no explicit configuration
    }
}
