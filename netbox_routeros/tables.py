from django_tables2 import tables, TemplateColumn, Column

from netbox_routeros.models import ConfigurationTemplate, ConfiguredDevice
from netbox_routeros.template_code import (
    TEMPLATE_LINK,
    TEMPLATE_BUTTONS,
    CONFIGURED_DEVICE_LINK,
    CONFIGURED_DEVICE_BUTTONS,
)
from netbox_routeros.utilities.tables import TagColumn
from tenancy.tables import COL_TENANT
from utilities.tables import (
    BaseTable,
    ToggleColumn,
)


class ConfiguredDeviceTable(BaseTable):
    pk = ToggleColumn()
    name = TemplateColumn(
        accessor="device.name",
        order_by=("_name",),
        template_code=CONFIGURED_DEVICE_LINK,
    )
    primary_ip4 = Column(
        linkify=True, accessor="device.primary_ip4", verbose_name="IPv4 Address"
    )
    primary_ip6 = Column(
        linkify=True, accessor="device.primary_ip6", verbose_name="IPv6 Address"
    )
    tags = TagColumn(accessor="device.tags", url_name="dcim:device_list")

    actions = TemplateColumn(template_code=CONFIGURED_DEVICE_BUTTONS,)

    class Meta(BaseTable.Meta):
        model = ConfiguredDevice
        fields = (
            "pk",
            "name",
            "primary_ip4",
            "primary_ip6",
            "tags",
            "last_config_fetched_at",
            "last_config_pushed_at",
            "actions",
        )
        default_columns = (
            "name",
            "slug",
            "primary_ip4",
            "primary_ip6",
            "tags",
            "last_config_fetched_at",
            "last_config_pushed_at",
            "actions",
        )


class ConfigurationTemplateTable(BaseTable):
    pk = ToggleColumn()
    name = TemplateColumn(order_by=("_name",), template_code=TEMPLATE_LINK)
    tenant = TemplateColumn(template_code=COL_TENANT)

    actions = TemplateColumn(template_code=TEMPLATE_BUTTONS,)

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ("pk", "name", "slug", "tenant", "actions")
        default_columns = ("name", "slug", "actions")
