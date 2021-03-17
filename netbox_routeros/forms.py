from django import forms

from dcim.models import Device
from extras.models import Tag
from netbox_routeros.models import ConfigurationTemplate, ConfiguredDevice
from tenancy.forms import TenancyForm
from utilities.forms import BootstrapMixin, DynamicModelMultipleChoiceField, SlugField, DynamicModelChoiceField

TEMPLATE_PLACEHOLDER = (
    "/ip address\n"
    "add address={{ device.loopback_address }} interface=loopback"
)


class ConfiguredDeviceForm(BootstrapMixin, TenancyForm, forms.ModelForm):
    # TODO: API
    # device = DynamicModelChoiceField(
    #     queryset=Device.objects.all(),
    # )
    # configuration_template = DynamicModelChoiceField(
    #     queryset=ConfigurationTemplate.objects.all(),
    # )

    class Meta:
        model = ConfiguredDevice
        fields = [
            'device',
            'configuration_template',
        ]



class ConfigurationTemplateForm(BootstrapMixin, TenancyForm, forms.ModelForm):
    slug = SlugField()
    tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False
    )
    content = forms.CharField(widget=forms.Textarea(attrs=dict(placeholder=TEMPLATE_PLACEHOLDER)), label="")
    preview_for_device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        display_field='display_name',
        required=False,
    )

    class Meta:
        model = ConfigurationTemplate
        fields = ['name', 'slug', 'tenant_group', 'tenant', 'content', 'tags']

