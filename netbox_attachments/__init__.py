try:
    from netbox.plugins import PluginConfig
except ModuleNotFoundError:

    class PluginConfig:  # type: ignore[no-redef]
        pass


from netbox_attachments.version import __version__


class NetBoxAttachmentsConfig(PluginConfig):
    name = "netbox_attachments"
    verbose_name = "Netbox Attachments"
    description = "Netbox plugin to manage attachments for any model"
    version = __version__
    author = "Jan Krupa"
    base_url = "netbox-attachments"
    default_settings = {
        "applied_scope": "app",
        "scope_filter": [
            "dcim",
            "ipam",
            "circuits",
            "tenancy",
            "virtualization",
            "wireless",
        ],
        "display_default": "additional_tab",
        "create_add_button": True,
        "display_setting": {},
    }
    required_settings = []
    min_version = "4.5.0"
    max_version = "4.6.99"

    def ready(self):
        super().ready()

        # Import for the @register side effect; see checks.py for what it warns about.
        from netbox_attachments import checks  # noqa: F401


config = NetBoxAttachmentsConfig
