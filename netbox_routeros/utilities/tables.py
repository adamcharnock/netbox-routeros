from netbox_routeros import tables


class TagColumn(tables.TemplateColumn):
    """
    Display a list of tags assigned to the object.
    """
    template_code = """
    {% for tag in value.all %}
        {% include 'utilities/templatetags/tag.html' %}
    {% empty %}
        <span class="text-muted">&mdash;</span>
    {% endfor %}
    """

    def __init__(self, url_name=None, **kwargs):
        super().__init__(
            template_code=self.template_code,
            extra_context={'url_name': url_name},
            **kwargs
        )
