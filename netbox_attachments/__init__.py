from netbox.plugins import PluginConfig

from netbox_attachments.version import __version__


class NetBoxAttachmentsConfig(PluginConfig):
    name = "netbox_attachments"
    verbose_name = "Netbox Attachments"
    description = "Netbox plugin to manage attachments for any model"
    version = __version__
    author = "Jan Krupa"
    base_url = "netbox-attachments"
    default_settings = {
        "applied_scope": "app",  # Changed from 'mode' - options: 'app' or 'model'
        "scope_filter": [
            "dcim",
            "ipam",
            "circuits",
            "tenancy",
            "virtualization",
            "wireless",
        ],  # Merged from 'apps' and 'allowed_models'
        "display_default": "additional_tab",
        "create_add_button": True,
        "display_setting": {},
    }
    required_settings = []
    min_version = "4.5.0"
    max_version = "4.5.99"


config = NetBoxAttachmentsConfig
