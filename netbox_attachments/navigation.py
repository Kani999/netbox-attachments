from extras.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='Attachments',
    icon_class="mdi mdi-paperclip",
    groups=(
        ("", (PluginMenuItem(link="plugins:netbox_attachments:netboxattachment_list",
         link_text="NetBox Attachments"),),),
    ),
)
