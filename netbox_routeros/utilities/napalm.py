from typing import TYPE_CHECKING

from django.conf import settings

from netbox.api.exceptions import ServiceUnavailable

if TYPE_CHECKING:
    from dcim.models import Device


def get_napalm_driver(device: "Device"):
    # Credit: Code pulled from netbox core
    # Check that NAPALM is installed
    try:
        import napalm
        from napalm.base.exceptions import ModuleImportError
    except ModuleNotFoundError as e:
        if getattr(e, "name") == "napalm":
            raise ServiceUnavailable(
                "NAPALM is not installed. Please see the documentation for instructions."
            )
        raise e

    # Validate the configured driver
    try:
        driver = napalm.get_network_driver(device.platform.napalm_driver)
    except ModuleImportError:
        raise ServiceUnavailable(
            "NAPALM driver for platform {} not found: {}.".format(
                device.platform, device.platform.napalm_driver
            )
        )

    host = str(device.primary_ip.address.ip)
    username = settings.NAPALM_USERNAME
    password = settings.NAPALM_PASSWORD
    optional_args = settings.NAPALM_ARGS.copy()
    if device.platform.napalm_args is not None:
        optional_args.update(device.platform.napalm_args)

    # Connect to the device
    d = driver(
        hostname=host,
        username=username,
        password=password,
        timeout=settings.NAPALM_TIMEOUT,
        optional_args=optional_args,
    )

    # Note that we don't open the connection as
    # we do not require API access

    return d
