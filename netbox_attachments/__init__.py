from extras.plugins import PluginConfig


class NetBoxAttachmentsConfig(PluginConfig):
    name = 'netbox_attachments'
    verbose_name = 'Netbox Attachments'
    description = 'Netbox plugin to manage attachments for any model'
    version = '0.0.1'
    base_url = 'netbox-attachments'


config = NetBoxAttachmentsConfig
