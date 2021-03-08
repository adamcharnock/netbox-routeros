from django.shortcuts import render
from jinja2 import TemplateError

from netbox.views import generic
from netbox_routeros.models import ConfigurationTemplate

from . import filters
from . import forms
from . import tables
from .ros_config_maker import render_ros_config


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

        try:
            config_preview = render_ros_config(device=form.cleaned_data['preview_for_device'], template_name=obj.slug, template_content=form.cleaned_data['content'])
        except TemplateError as e:
            config_preview = f"{e.__class__.__name__}: {e}"

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
