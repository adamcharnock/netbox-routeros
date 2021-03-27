import traceback
from inspect import isclass
from typing import Optional, Tuple

from django.contrib import messages
from django.db.models import Model
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.views import View
from jinja2 import TemplateError, TemplateNotFound
from napalm.base.exceptions import CommandErrorException

from dcim.models import Device
from routeros_diff import RouterOSConfig
from netbox.views import generic
from netbox_routeros.models import ConfigurationTemplate, ConfiguredDevice
from pprint import pformat

from utilities.views import GetReturnURLMixin
from . import filters
from . import forms
from . import tables
from .ros_config_maker import render_ros_config, make_ros_config_context


class ConfiguredDeviceListView(generic.ObjectListView):
    queryset = ConfiguredDevice.objects.select_related(
        "device", "configuration_template"
    ).all()
    filterset = filters.ConfiguredDeviceFilterSet
    filterset_form = forms.ConfiguredDeviceForm
    table = tables.ConfiguredDeviceTable
    template_name = "routeros/configured_device_list.html"
    action_buttons = []


class ConfiguredDeviceEditView(generic.ObjectEditView):
    # TODO: Don't allow editing of device field
    queryset = ConfiguredDevice.objects.all()
    model_form = forms.ConfiguredDeviceForm
    template_name = "routeros/configured_device_edit.html"
    default_return_url = "plugins:netbox_routeros:configureddevice_list"


class PullConfigView(GetReturnURLMixin, View):
    def post(self, request):
        # Verify user permission
        if not request.user.has_perm("dcim.napalm_write_device"):
            return HttpResponseForbidden()

        pks = request.POST.getlist("pk")
        objs = ConfiguredDevice.objects.filter(pk__in=pks)
        for configured_device in objs:
            if not configured_device.problems:
                configured_device.fetch_config()

        messages.success(request, f"Fetched {len(pks)} device configurations")
        return HttpResponseRedirect(self.get_return_url(request))


class PushConfigView(GetReturnURLMixin, View):
    def post(self, request):
        # Verify user permission
        if not request.user.has_perm("dcim.napalm_write_device"):
            return HttpResponseForbidden()

        pks = request.POST.getlist("pk")
        objs = ConfiguredDevice.objects.filter(pk__in=pks)

        successes = 0
        for configured_device in objs:
            if not configured_device.problems:
                try:
                    configured_device.push_config()
                except CommandErrorException as e:
                    messages.error(request, str(e))
                else:
                    successes += 1

        message = f"Pushed {successes} device configuration(s)"
        if successes:
            messages.success(request, message)
        else:
            messages.warning(request, message)

        return HttpResponseRedirect(self.get_return_url(request))


class ConfiguredDeviceView(generic.ObjectView):
    queryset = ConfiguredDevice.objects.all()
    template_name = "routeros/configured_device.html"

    def get_extra_context(self, request, instance: ConfiguredDevice):
        config_generated, error = render_configured_device_config_for_display(
            configured_device=instance,
        )
        bootstrap_config, bootstrap_error = render_bootstrap_for_display(
            device=instance.device
        )

        if not error:
            diff = instance.generate_diff()
        else:
            diff = None

        return {
            **get_template_context(instance.device),
            "config_generated": config_generated.__html__()
            if config_generated and config_generated.sections
            else f"<pre>{error}</pre>",
            "config_latest": instance.parse_last_config_fetched().__html__()
            if instance.last_config_fetched
            else None,
            "config_diff": diff.__html__() if diff and diff.sections else None,
            "config_bootstrap": bootstrap_config or f"<pre>{bootstrap_error}</pre>",
        }


# Configuration templates


class ConfigurationTemplateListView(generic.ObjectListView):
    queryset = ConfigurationTemplate.objects.all()
    filterset = filters.ConfigurationTemplateFilterSet
    filterset_form = forms.ConfigurationTemplateForm
    table = tables.ConfigurationTemplateTable
    template_name = "routeros/configuration_template_list.html"
    action_buttons = []


class ConfigurationTemplateEditView(generic.ObjectEditView):
    queryset = ConfigurationTemplate.objects.all()
    model_form = forms.ConfigurationTemplateForm
    template_name = "routeros/configuration_template_edit.html"
    default_return_url = "plugins:netbox_routeros:configurationtemplate_list"

    def post(self, request, *args, **kwargs):
        if not request.POST.get("_preview"):
            return super().post(request, *args, **kwargs)
        else:
            return self.render_preview(request, *args, **kwargs)

    def render_preview(self, request, *args, **kwargs):
        obj = self.alter_obj(self.get_object(kwargs), request, args, kwargs)
        form = self.model_form(data=request.POST, files=request.FILES, instance=obj)

        if not form.is_valid():
            return super().post(request, *args, **kwargs)

        form.instance.content = form.cleaned_data["content"]
        temporary_configured_device = ConfiguredDevice(
            device=form.cleaned_data["preview_for_device"],
            configuration_template=form.instance,
        )

        config_preview, error = render_configured_device_config_for_display(
            configured_device=temporary_configured_device,
        )

        return render(
            request,
            self.template_name,
            {
                "obj": obj,
                "obj_type": self.queryset.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                "config_preview": str(config_preview) if config_preview else error,
            },
        )


class ConfigurationTemplateView(generic.ObjectView):
    queryset = ConfigurationTemplate.objects.all()
    template_name = "routeros/configuration_template.html"


def get_template_context(device: Device):
    context = make_ros_config_context(device=device)
    context_models = {
        k: v for k, v in context.items() if isclass(v) and issubclass(v, Model)
    }
    context_functions = {
        k: v for k, v in context.items() if callable(v) and k not in context_models
    }
    context_values = {
        k: v
        for k, v in context.items()
        if k not in context_models and k not in context_functions
    }

    return {
        "context_values": pformat(context_values, sort_dicts=True),
        "context_functions": pformat(context_functions, sort_dicts=True),
        "context_models": pformat(context_models, sort_dicts=True),
    }


def render_configured_device_config_for_display(
    configured_device: ConfiguredDevice,
) -> Tuple[Optional[RouterOSConfig], Optional[str]]:
    """Render a config for display to a user

    Adds some niceties around error rendering
    """
    error = None
    config = None
    try:
        config = configured_device.generate_config()
    except Exception:
        error = traceback.format_exc()

    return config, error


def render_bootstrap_for_display(
    device: Device,
) -> Tuple[Optional[str], Optional[str]]:
    error = None
    config = None
    try:
        config = render_ros_config(device=device, template_name="bootstrap")
    except TemplateNotFound:
        # Just return None
        pass
    except Exception:
        error = traceback.format_exc()

    return config, error
