import napalm
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from napalm.base import ModuleImportError
from taggit.managers import TaggableManager

from extras.models import ChangeLoggedModel, TaggedItem
from netbox.api.exceptions import ServiceUnavailable
from netbox_routeros.utilities.napalm import get_napalm_driver
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
    extra_configuration = models.TextField(
        default="",
        blank=True,
        help_text="Extra configuration to include in addition to the config template"
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

    @cached_property
    def problems(self):
        """There are a bunch of things that may cause issues. Let's check for them
        proactively and let the user know"""
        problems = []
        if not self.device.primary_ip:
            problems.append("Device has no primary IP set. Set a primary IP to enable connecting to this device")

        # Check device has a platform
        if not self.device.platform:
            problems.append("No platform has been configured for this device")

        # Check that NAPALM is installed
        try:
            import napalm
            from napalm.base.exceptions import ModuleImportError
        except ModuleNotFoundError as e:
            if getattr(e, 'name') == 'napalm':
                problems.append("NAPALM is not installed. Please install the napalm package.")
            return problems

        # Validate the configured driver
        try:
            napalm.get_network_driver(self.device.platform.napalm_driver)
        except ModuleImportError:
            problems.append("NAPALM driver for platform {self.device.platform} not found: {self.device.platform.napalm_driver}.")

        return problems

    def fetch_config(self):
        # Validate the configured driver
        driver = get_napalm_driver(self.device)
        config = driver.get_config(retrieve='running', full=True, sanitized=False)['running']
        self.last_config_fetched = config
        self.last_config_fetched_at = now()
        self.save()


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
