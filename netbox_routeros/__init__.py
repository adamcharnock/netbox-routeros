__version__ = '0.1.0'

from extras.plugins import PluginConfig


class RouterOsConfig(PluginConfig):
    name = 'netbox_routeros'
    verbose_name = 'Netbox RouterOS'
    description = 'Manage RouterOS configuration from within Netbox'
    version = '0.1.0'
    author = 'Adam Charnock'
    author_email = 'adam.charnock@gardunha.net'
    base_url = 'routeros'
    required_settings = []
    default_settings = {
    }

config = RouterOsConfig
