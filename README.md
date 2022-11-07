# netbox-attachments

Manage attachments for any model in NetBox

### Configuration / Installation
- `configuration.py`
```
# Add plugin
PLUGINS = ['netbox_attachments']
# Set to which app (and models under it) could be attachments stored
PLUGINS_CONFIG = {
    'netbox_attachments': {
        'apps': ['dcim', 'ipam', 'circuits', 'tenancy', 'virtualization', 'wireless', '<custom_plugin>'],
    }
}
```

- Caveats
    - If you want to enable appending attachments to your plugin, you have to add some code to your plugin codebase
    - Extending your views at `templates/<plugin>/<detail_view>.html`
    - ```
        # At the TOP
        {% load plugins %}
        ...
        # Then under the comments section 
        {% plugin_right_page object %}
      ```
    - It's same as for the core models e.g.
        - https://github.com/netbox-community/netbox/blob/c1b7f09530f0293d0f053b8930539b1d174cd03b/netbox/templates/dcim/device.html#L288

# Usage
- Install Plugin 
- Open any model in netbox 
- Add attachment under the `Attachments` panel

# TODO: 
- adding templates to list all attachments
- delete attachments from disk