from netbox_routeros.models import ConfigurationTemplate
from tenancy.filters import TenancyFilterSet
from utilities.filters import BaseFilterSet, NameSlugSearchFilterSet


class ConfigurationTemplateFilterSet(
    BaseFilterSet,
    TenancyFilterSet,
    NameSlugSearchFilterSet
):
    class Meta:
        model = ConfigurationTemplate
        fields = ['id', 'name', 'slug']
