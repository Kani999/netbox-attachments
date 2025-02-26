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
        "apps": ["dcim", "ipam", "circuits", "tenancy", "virtualization", "wireless"],
        "display_default": "additional_tab",
        "create_add_button": True,  # New setting: specific only to `additional_tab` display setting. If set to True, it will create an "Add Attachment" button at the top of the parent view
        "display_setting": {},
        "mode": "permissive",  # New setting: 'permissive' or 'restrictive'
        "allowed_models": [],  # New setting: specific models to allow in restrictive mode
    }
    required_settings = []
    min_version = "4.2.0"
    max_version = "4.2.99"


config = NetBoxAttachmentsConfig
