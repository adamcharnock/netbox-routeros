from django.shortcuts import render
from jinja2 import TemplateError

from dcim.models import Device
from gn.gnms.ros_conf.ros_parser import RouterOSConfig
from netbox.views import generic
from netbox_routeros.models import ConfigurationTemplate, ConfiguredDevice

from . import filters
from . import forms
from . import tables
from .ros_config_maker import render_ros_config


class ConfiguredDeviceListView(generic.ObjectListView):
    queryset = ConfiguredDevice.objects.select_related('device', 'configuration_template').all()
    filterset = filters.ConfiguredDeviceFilterSet
    filterset_form = forms.ConfiguredDeviceForm
    table = tables.ConfiguredDeviceTable
    template_name = 'routeros/configured_device_list.html'
    action_buttons = []


class ConfiguredDeviceEditView(generic.ObjectEditView):
    # TODO: Don't allow editing of device field
    queryset = ConfiguredDevice.objects.all()
    model_form = forms.ConfiguredDeviceForm
    template_name = 'routeros/configured_device_edit.html'
    default_return_url = 'plugins:netbox_routeros:configureddevice_list'


class ConfiguredDeviceView(generic.ObjectView):
    queryset = ConfiguredDevice.objects.all()
    template_name = 'routeros/configured_device.html'

    def get_extra_context(self, request, instance: ConfiguredDevice):
        return {
            'config_preview': make_config_for_display(device=instance.device, template_name=instance.configuration_template.slug, prettify=True)
        }


# Configuration templates

class ConfigurationTemplateListView(generic.ObjectListView):
    queryset = ConfigurationTemplate.objects.all()
    filterset = filters.ConfigurationTemplateFilterSet
    filterset_form = forms.ConfigurationTemplateForm
    table = tables.ConfigurationTemplateTable
    template_name = 'routeros/configuration_template_list.html'
    action_buttons = []


class ConfigurationTemplateEditView(generic.ObjectEditView):
    queryset = ConfigurationTemplate.objects.all()
    model_form = forms.ConfigurationTemplateForm
    template_name = 'routeros/configuration_template_edit.html'
    default_return_url = 'plugins:netbox_routeros:configurationtemplate_list'

    def post(self, request, *args, **kwargs):
        if not request.POST.get("_preview"):
            return super().post(request, *args, **kwargs)
        else:
            return self.render_preview(request, *args, **kwargs)

    def render_preview(self, request, *args, **kwargs):
        obj = self.alter_obj(self.get_object(kwargs), request, args, kwargs)
        form = self.model_form(
            data=request.POST,
            files=request.FILES,
            instance=obj
        )
        if not form.is_valid():
            return super().post(request, *args, **kwargs)

        config_preview = make_config_for_display(device=form.cleaned_data['preview_for_device'], template_name=obj.slug, template_content=form.cleaned_data['content'])

        return render(request, self.template_name, {
            'obj': obj,
            'obj_type': self.queryset.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(request, obj),
            'config_preview': config_preview
        })


class ConfigurationTemplateView(generic.ObjectView):
    queryset = ConfigurationTemplate.objects.all()
    template_name = 'routeros/configuration_template.html'


def make_config_for_display(device: Device, template_name: str, template_content: str="", prettify=False):
    """Render a config for display to a user

    Adds some niceties around error rendering
    """
    try:
        config = render_ros_config(device, template_name, template_content)
    except TemplateError as e:
        if hasattr(e, 'lineno'):
            config = f"{e.__class__.__name__} on line {e.lineno}: {e}"
        else:
            config = f"{e.__class__.__name__}: {e}"
    else:
        if prettify:
            config = str(RouterOSConfig.parse(config))

    return config
