from netbox_routeros.models import ConfigurationTemplate, ConfiguredDevice
from tenancy.filters import TenancyFilterSet
from utilities.filters import BaseFilterSet, NameSlugSearchFilterSet


class ConfiguredDeviceFilterSet(
    BaseFilterSet, TenancyFilterSet, NameSlugSearchFilterSet
):
    class Meta:
        # TODO: Include device fields
        model = ConfiguredDevice
        fields = [
            "device",
            "configuration_template",
            "last_config_fetched_at",
            "last_config_pushed_at",
        ]


class ConfigurationTemplateFilterSet(
    BaseFilterSet, TenancyFilterSet, NameSlugSearchFilterSet
):
    class Meta:
        model = ConfigurationTemplate
        fields = ["id", "name", "slug"]
