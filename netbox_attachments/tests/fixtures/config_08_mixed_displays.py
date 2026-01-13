# Configuration 8: Mixed Display Settings
# Test per-model display_setting overrides
#
# Expected behavior:
# - Device: full_width_page (override)
# - Site: left_page (override)
# - Rack: right_page (override)
# - Other dcim models: additional_tab (default)
# - Demonstrates per-model customization

PLUGINS = [
    'netbox_attachments',
    'netbox_custom_objects',
]

PLUGINS_CONFIG = {
    'netbox_attachments': {
        'applied_scope': 'app',
        'scope_filter': [
            'dcim',
        ],
        'display_default': 'additional_tab',
        'display_setting': {
            'dcim.device': 'full_width_page',
            'dcim.site': 'left_page',
            'dcim.rack': 'right_page',
        },
    }
}
