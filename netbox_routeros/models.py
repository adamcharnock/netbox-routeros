from typing import Optional

import napalm
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from napalm.base import ModuleImportError
from routeros_diff import RouterOSConfig
from taggit.managers import TaggableManager

from extras.models import ChangeLoggedModel, TaggedItem
from netbox.api.exceptions import ServiceUnavailable
from netbox_routeros.ros_config_maker import render_ros_config
from netbox_routeros.utilities.napalm import get_napalm_driver
from utilities.querysets import RestrictedQuerySet


class ConfiguredDevice(ChangeLoggedModel):
    device = models.OneToOneField(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="routeros_configured_devices",
    )
    configuration_template = models.ForeignKey(
        to="netbox_routeros.ConfigurationTemplate",
        on_delete=models.PROTECT,
        related_name="configured_devices",
    )
    extra_configuration = models.TextField(
        default="",
        blank=True,
        help_text=(
            "Extra configuration to include in addition to the config template. "
            "You can use the Jinja2 template syntax, and you have access to all "
            "of the device's template context."
        ),
    )

    tenant = models.ForeignKey(
        to="tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="routeros_configured_devices",
        blank=True,
        null=True,
    )

    last_config_fetched = models.TextField(
        default="",
        blank=True,
        verbose_name="The last config which was fetched from the device",
    )
    last_verbose_config_fetched = models.TextField(
        default="",
        blank=True,
        verbose_name="The last config which was fetched from the device (the verbose version)",
    )
    last_config_fetched_at = models.DateTimeField(default=None, null=True, blank=True)

    last_config_pushed_at = models.DateTimeField(default=None, null=True, blank=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ["device__name"]

    def __str__(self):
        if self.device_id:
            return str(self.device)
        else:
            return "New configured device"

    def generate_config(self) -> RouterOSConfig:
        config = render_ros_config(
            self.device,
            template_name=self.configuration_template.slug,
            template_content=self.configuration_template.content,
            extra_config=self.extra_configuration,
        )
        return RouterOSConfig.parse(config)

    def parse_last_config_fetched(self) -> Optional[RouterOSConfig]:
        if self.last_config_fetched:
            return RouterOSConfig.parse(self.last_config_fetched)
        else:
            return None

    def parse_last_verbose_config_fetched(self) -> Optional[RouterOSConfig]:
        if self.last_verbose_config_fetched:
            return RouterOSConfig.parse(self.last_verbose_config_fetched)
        else:
            return None

    def generate_diff(self) -> Optional[RouterOSConfig]:
        old = self.parse_last_config_fetched()
        if not old:
            return
        return self.generate_config().diff(
            old=self.parse_last_config_fetched(),
            old_verbose=self.parse_last_verbose_config_fetched(),
        )

    @cached_property
    def problems(self):
        """There are a bunch of things that may cause issues. Let's check for them
        proactively and let the user know"""
        problems = []
        if not self.device.primary_ip:
            problems.append(
                "Device has no primary IP set. Set a primary IP to enable connecting to this device"
            )

        # Check device has a platform
        if not self.device.platform:
            problems.append("No platform has been configured for this device")

        # Check that NAPALM is installed
        try:
            import napalm
            from napalm.base.exceptions import ModuleImportError
        except ModuleNotFoundError as e:
            if getattr(e, "name") == "napalm":
                problems.append(
                    "NAPALM is not installed. Please install the napalm package."
                )
            return problems

        # Validate the configured driver
        if not self.device.platform:
            problems.append("No platform configured for device")
            return

        if not self.device.platform.napalm_driver:
            problems.append("Device's platform has no napalm driver set")
            return

        try:
            napalm.get_network_driver(self.device.platform.napalm_driver)
        except ModuleImportError:
            problems.append(
                f"NAPALM driver for platform {self.device.platform} not found: {self.device.platform.napalm_driver}."
            )

        return problems

    def fetch_config(self):
        driver = get_napalm_driver(self.device)
        self.last_config_fetched = driver.get_config(
            retrieve="running", full=False, sanitized=False
        )["running"]
        self.last_verbose_config_fetched = driver.get_config(
            retrieve="running", full=True, sanitized=False
        )["running"]
        self.last_config_fetched_at = now()
        self.save()

    def push_config(self):
        driver = get_napalm_driver(self.device)
        driver.load_replace_candidate(
            config=self.generate_config(),
            current_config=self.parse_last_config_fetched(),
        )
        self.last_config_pushed_at = now()
        self.fetch_config()
        self.save()


class ConfigurationTemplate(ChangeLoggedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    tenant = models.ForeignKey(
        to="tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="routeros_configuration_templates",
        blank=True,
        null=True,
    )
    tags = TaggableManager(through=TaggedItem)
    content = models.TextField()

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
