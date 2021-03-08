TEMPLATE_LINK = """
<a href="{% url 'plugins:netbox_routeros:configurationtemplate' pk=record.pk %}">
    {{ record.name }}
</a>
"""


TEMPLATE_BUTTONS = """
    {% if perms.netbox_routeros.change_configurationtemplate %}
        <a href="{% url 'plugins:netbox_routeros:configurationtemplate_edit' record.pk %}?return_url={{ request.path }}{{ return_url_extra }}" class="btn btn-xs btn-warning" title="Edit">
            <i class="mdi mdi-pencil"></i>
        </a>
    {% endif %}
    {% if perms.netbox_routeros.delete_configurationtemplate %}
        <a href="{% url 'plugins:netbox_routeros:configurationtemplate_delete' record.pk %}?return_url={{ request.path }}{{ return_url_extra }}" class="btn btn-xs btn-danger" title="Delete">
            <i class="mdi mdi-trash-can-outline"></i>
        </a>
    {% endif %}
"""
