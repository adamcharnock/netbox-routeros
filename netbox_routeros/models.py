from django.db import models
from taggit.managers import TaggableManager

from extras.models import ChangeLoggedModel, TaggedItem
from utilities.querysets import RestrictedQuerySet


class ConfiguredDevice(ChangeLoggedModel):
    device = models.OneToOneField(
        to='dcim.Device',
        on_delete=models.CASCADE,
        related_name='routeros_configured_devices',
    )
    configuration_template = models.ForeignKey(
        to='netbox_routeros.ConfigurationTemplate',
        on_delete=models.PROTECT,
        related_name='configured_devices',
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='routeros_configured_devices',
        blank=True,
        null=True
    )

    last_config_fetched = models.TextField(
        default="",
        blank=True,
        verbose_name="The last config which was fetched from the device"
    )
    last_config_fetched_at = models.DateTimeField(default=None, null=True, blank=True)

    last_config_pushed = models.TextField(
        default="",
        blank=True,
        verbose_name="The last config which was pushed to the device"
    )
    last_config_pushed_at = models.DateTimeField(default=None, null=True, blank=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ['device__name']

    def __str__(self):
        if self.device_id:
            return self.device.name
        else:
            return "New configured device"


class ConfigurationTemplate(ChangeLoggedModel):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='routeros_configuration_templates',
        blank=True,
        null=True
    )
    tags = TaggableManager(through=TaggedItem)
    content = models.TextField()

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
