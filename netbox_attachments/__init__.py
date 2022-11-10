from extras.plugins import PluginConfig

from .version import __version__


class NetBoxAttachmentsConfig(PluginConfig):
    name = 'netbox_attachments'
    verbose_name = 'Netbox Attachments'
    description = 'Netbox plugin to manage attachments for any model'
    version = __version__
    author = 'Jan Krupa'
    base_url = 'netbox-attachments'
    default_settings = {
        'apps': ['dcim', 'ipam', 'circuits', 'tenancy', 'virtualization', 'wireless'],
        'display_default': "right_page",
        'display_setting': {}
    }
    required_settings = []
    min_version = '3.3.4'
    max_version = '3.3.99'


config = NetBoxAttachmentsConfig
