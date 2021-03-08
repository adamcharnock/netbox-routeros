from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_routeros:configurationtemplate_list',
        link_text='Configuration templates',
        buttons=(
            PluginMenuButton('plugins:netbox_routeros:configurationtemplate_add', 'Add', 'mdi mdi-plus-thick', ButtonColorChoices.GREEN),
            # PluginMenuButton('home', 'Button B', 'fa fa-warning', ButtonColorChoices.GREEN),
        )
    ),
)
