from django_tables2 import tables, Column, TemplateColumn

from netbox_routeros.models import ConfigurationTemplate
from netbox_routeros.template_code import TEMPLATE_LINK, TEMPLATE_BUTTONS
from tenancy.tables import COL_TENANT
from utilities.tables import (
    BaseTable, ToggleColumn, ButtonsColumn, )


class ConfigurationTemplateTable(BaseTable):
    pk = ToggleColumn()
    name = TemplateColumn(
        order_by=('_name',),
        template_code=TEMPLATE_LINK
    )
    tenant = TemplateColumn(
        template_code=COL_TENANT
    )

    actions = TemplateColumn(
        template_code=TEMPLATE_BUTTONS,
    )

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('pk', 'name', 'slug', 'tenant', 'actions')
        default_columns = ('name', 'slug', 'actions')


