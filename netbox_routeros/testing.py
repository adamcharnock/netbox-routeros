from ipaddress import IPv4Address, IPv6Address
from typing import Sequence, Union

from dcim.models import Site, DeviceRole, DeviceType, Device, Manufacturer, Interface
from ipam.models import IPAddress, Prefix, VLAN

FlexibleIpType = Union[str, IPv4Address, IPv6Address, IPAddress]


class TestCaseMixin:
    data: "DataProvider"

    def setUp(self):
        self.data = DataProvider()


class DataProvider:

    def device(self, device_type: DeviceType=None, device_role: DeviceRole=None, site: Site=None, **kwargs):
        values = dict(
            device_type=device_type or self.any_device_type(),
            device_role=device_role or self.any_device_role(),
            site=site or self.any_site(),
        )
        values.update(**kwargs)
        return Device.objects.create(**values)

    def any_device(self, device_type: DeviceType=None, device_role: DeviceRole=None, site: Site=None, **kwargs):
        try:
            return Device.objects.latest('pk')
        except Device.DoesNotExist:
            return self.device(device_type=device_type, device_role=device_role, site=site, **kwargs)

    def device_role(self, name: str=None, slug: str=None, **kwargs):
        number = DeviceRole.objects.count() + 1
        values = dict(
            name=name or f"Test device role {number}",
            slug=slug or f"test-device-role-{number}",
            **kwargs
        )
        values.update(**kwargs)
        return DeviceRole.objects.create(**values)

    def any_device_role(self, name: str=None, slug: str=None, **kwargs):
        try:
            return DeviceRole.objects.latest('pk')
        except DeviceRole.DoesNotExist:
            return self.device_role(name=name, slug=slug, **kwargs)

    def device_type(self, manufacturer: Manufacturer=None, model:str=None, slug: str=None, **kwargs):
        number = DeviceType.objects.count() + 1
        values = dict(
            manufacturer=manufacturer or self.any_manufacturer(),
            model="LASER-PANTHER-2000",
            slug=slug or f"test-device-type-{number}",
            **kwargs
        )
        values.update(**kwargs)
        return DeviceType.objects.create(**values)

    def any_device_type(self, manufacturer: Manufacturer=None, model:str=None, slug: str=None, **kwargs):
        try:
            return DeviceType.objects.latest('pk')
        except DeviceType.DoesNotExist:
            return self.device_type(manufacturer=manufacturer, model=model, slug=slug, **kwargs)

    def manufacturer(self, name: str=None, slug: str=None, **kwargs):
        number = DeviceType.objects.count() + 1
        values = dict(
            name=name or f"Test manufacturer {number}",
            slug=slug or f"test-manufacturer-{number}",
            **kwargs
        )
        values.update(**kwargs)
        return Manufacturer.objects.create(**values)

    def any_manufacturer(self, name: str=None, slug: str=None, **kwargs):
        try:
            return Manufacturer.objects.latest('pk')
        except Manufacturer.DoesNotExist:
            return self.manufacturer(name=name, slug=slug, **kwargs)

    def site(self, name: str=None, slug: str=None, **kwargs):
        number = DeviceType.objects.count() + 1
        values = dict(
            name=name or f"Test site {number}",
            slug=slug or f"test-site-{number}",
            **kwargs
        )
        values.update(**kwargs)
        return Site.objects.create(**values)

    def any_site(self, name: str=None, slug: str=None, **kwargs):
        try:
            return Site.objects.latest('pk')
        except Site.DoesNotExist:
            return self.site(name=name, slug=slug, **kwargs)

    def interface(self, device: Device, name: str=None, ip_address: Union[FlexibleIpType, Sequence[FlexibleIpType]]=None, vlan: VLAN=None, **kwargs):
        """Create an interface, as well as an IP addresses specified"""
        number = Interface.objects.count() + 1
        values = dict(
            device=device,
            name=name or f"ether{number}",
            **kwargs
        )
        interface = Interface.objects.create(**values)

        ip_address = ip_address or []
        ip_addresses = ip_address if isinstance(ip_address, (tuple, list)) else [ip_address]
        for ip in ip_addresses:
            if isinstance(ip, IPAddress):
                ip.assigned_object = interface
                ip.save()
            else:
                IPAddress.objects.create(
                    address=ip,
                    assigned_object=interface,
                )

        if vlan:
            interface.tagged_vlans.add(vlan)

        return interface

    def prefix(self, prefix: str=None, **kwargs):
        number = Prefix.objects.count()
        values = dict(
            prefix=prefix or f'10.123.{number}.0/24',
        )
        return Prefix.objects.create(**values)

    def vlan(self, vid: int=None, name: str=None):
        number = VLAN.objects.count() + 1
        values = dict(
            vid=number + 1000 if vid is None else vid,
            name=name or f'Test VLAN {number}',
        )
        return VLAN.objects.create(**values)

    def ip_address(self, address=None, **kwargs):
        number = IPAddress.objects.count()
        values = dict(
            address=address or f'10.99.99.{number}',
            **kwargs
        )
        return IPAddress.objects.create(**values)
