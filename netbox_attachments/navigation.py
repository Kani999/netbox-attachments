from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Attachments",
    icon_class="mdi mdi-paperclip",
    groups=(
        (
            "Files",
            (
                PluginMenuItem(
                    link="plugins:netbox_attachments:netboxattachment_list",
                    link_text="Attachments",
                    permissions=["netbox_attachments.view_netboxattachment"],
                ),
            ),
        ),
        (
            "Assignments",
            (
                PluginMenuItem(
                    link="plugins:netbox_attachments:netboxattachmentassignment_list",
                    link_text="Assignments",
                    permissions=["netbox_attachments.view_netboxattachmentassignment"],
                ),
            ),
        ),
    ),
)
