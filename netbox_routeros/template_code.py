CONFIGURED_DEVICE_LINK = """
<a href="{% url 'plugins:netbox_routeros:configureddevice' pk=record.pk %}">
    {{ record.device.name }}
</a>
"""

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


CONFIGURED_DEVICE_BUTTONS = """
    <a href="{% url 'dcim:device' record.device.pk %}" class="btn btn-xs btn-default" title="View device">
        <i class="mdi mdi-router-network"></i>
    </a>
    {% if perms.netbox_routeros.change_configureddevice %}
        <a href="{% url 'plugins:netbox_routeros:configureddevice_edit' record.pk %}?return_url={{ request.path }}{{ return_url_extra }}" class="btn btn-xs btn-warning" title="Edit">
            <i class="mdi mdi-pencil"></i>
        </a>
    {% endif %}
    {% if perms.netbox_routeros.delete_configureddevice %}
        <a href="{% url 'plugins:netbox_routeros:configureddevice_delete' record.pk %}?return_url={{ request.path }}{{ return_url_extra }}" class="btn btn-xs btn-danger" title="Delete">
            <i class="mdi mdi-trash-can-outline"></i>
        </a>
    {% endif %}
"""
