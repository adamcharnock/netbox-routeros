from functools import partial
from ipaddress import (
    collapse_addresses,
    IPv4Interface,
    IPv6Address,
    IPv6Network,
    IPv4Network,
    ip_network,
    ip_interface,
)
from typing import Union, List, Optional

import django.apps
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func
from django.db.models.functions import Cast
from jinja2 import Environment, BaseLoader, TemplateNotFound
import netaddr

from dcim.models import Device, Interface
from ipam.fields import IPAddressField
from ipam.models import IPAddress, VLAN, Q, Prefix
from utilities.utils import deepmerge


class Any(Func):
    function = "ANY"


class RosTemplateLoader(BaseLoader):
    def __init__(self, overrides: dict = None):
        self.overrides = overrides or {}

    def get_source(self, environment, template):
        from netbox_routeros.models import ConfigurationTemplate

        # TODO: Does not support tenants
        if template in self.overrides:
            return (
                self.overrides[template],
                template,
                lambda: content == self.overrides[template],
            )

        try:
            content = ConfigurationTemplate.objects.get(slug=template).content
        except ConfigurationTemplate.DoesNotExist:
            raise TemplateNotFound(template)
        else:
            return (
                content,
                template,
                lambda: content
                == ConfigurationTemplate.objects.get(slug=template).content,
            )

    def list_templates(self):
        from netbox_routeros.models import ConfigurationTemplate

        return ConfigurationTemplate.objects.all().values_list("slug", flat=True)


def render_ros_config(
    device: Device,
    template_name: str,
    template_content: str = None,
    extra_config: str = "",
):
    overrides = {}
    if template_name and template_content:
        overrides[template_name] = template_content
    if extra_config:
        overrides["_extra_config"] = extra_config

    env = Environment(loader=RosTemplateLoader(overrides),)
    template = env.get_template(template_name)
    context = make_ros_config_context(device)

    config = template.render(**context)

    if extra_config:
        template = env.get_template("_extra_config")
        rendered_extra_config = template.render(**context)
        config += f"\n{rendered_extra_config}"

    return config


def make_ros_config_context(device: Device):
    # Make all models available for custom querying
    models = {m._meta.object_name: m for m in django.apps.apps.get_models()}

    context = dict(
        device=device,
        vlans=_context_vlans(device),
        **_context_ip_addresses(device),
        **_context_prefixes(device),
        **get_template_functions(device),
        **models,
    )
    return dict(deepmerge(context, device.get_config_context()))


def _context_ip_addresses(device: Device):
    # TODO: Test
    addresses = IPAddress.objects.filter(interface__device=device)
    return dict(
        ip_addresses=addresses,
        ip_addresses_v4=addresses.filter(address__family=4),
        ip_addresses_v6=addresses.filter(address__family=6),
    )


def _context_vlans(device: Device):
    # TODO: Test
    return VLAN.objects.filter(prefixes__prefix__net_contains=_any_address(device))


def _context_prefixes(device: Device):
    # TODO: Test
    prefixes = Prefix.objects.filter(prefix__net_contains=_any_address(device))
    return dict(
        prefixes=prefixes,
        prefixes_v4=prefixes.filter(prefix__family=4),
        prefixes_v6=prefixes.filter(prefix__family=6),
    )


def _any_address(device: Device):
    """Utility for querying against any device address"""
    addresses = [
        str(ip.ip)
        for ip in IPAddress.objects.filter(interface__device=device).values_list(
            "address", flat=True
        )
    ]
    addresses = Cast(addresses, output_field=ArrayField(IPAddressField()))
    return Any(addresses)


def get_template_functions(device):
    return dict(
        get_loopback=get_loopback,
        get_prefix=get_prefix,
        combine_prefixes=combine_prefixes,
        get_interface=partial(get_interface, device),
        get_address=get_address,
        orm_or=orm_or,
    )


def get_loopback(device: Device, number=1) -> Optional[IPAddress]:
    qs = IPAddress.objects.filter(interface__device=device, role="loopback").order_by(
        "address"
    )
    try:
        loopback = qs[number - 1 : number].get()
    except IPAddress.DoesNotExist:
        return None

    if loopback:
        return loopback.address.ip


def combine_prefixes(prefixes, only_combined=False):
    in_prefixes = [
        ip_network(p.prefix if isinstance(p, Prefix) else p) for p in prefixes
    ]
    out_prefixes = list(
        collapse_addresses([p for p in in_prefixes if p.version == 4])
    ) + list(collapse_addresses([p for p in in_prefixes if p.version == 6]))

    if only_combined:
        out_prefixes = [p for p in out_prefixes if p not in in_prefixes]

    # Ensure we use the netaddr IPAddress, rather than the ipaddress.IPvXNetwork
    return [netaddr.IPNetwork(str(p)) for p in out_prefixes]


def get_interface(
    device: Device,
    obj: Union[
        str,
        IPv4Interface,
        IPv4Network,
        IPv6Address,
        IPv6Network,
        netaddr.IPNetwork,
        netaddr.IPAddress,
        IPAddress,
        Prefix,
        VLAN,
    ],
    include_vlans=True,
):
    if isinstance(obj, Prefix):
        obj = obj.prefix
    elif isinstance(obj, IPAddress):
        obj = obj.address

    if isinstance(obj, (str, netaddr.IPNetwork, netaddr.IPAddress)):
        obj = ip_interface(str(obj))

    if isinstance(obj, VLAN):
        vlan_filter = Q(untagged_vlan=obj) | Q(tagged_vlans=obj)
        return device.interfaces.filter(vlan_filter).first()

    if include_vlans:
        # Get the vlan interface for this IP if the router has one
        vlan_interface = VLAN.objects.filter(
            interfaces_as_tagged__device=device,
            prefixes__prefix__net_contains_or_equals=str(obj),
        ).last()
        if vlan_interface:
            return vlan_interface

    if obj.network.max_prefixlen == obj.network.prefixlen:
        # A /32 or /128, so query based on the IP host
        query = dict(ip_addresses__address__net_host=str(obj))
    else:
        # A subnet of some sort
        query = dict(ip_addresses__address__net_contained_or_equal=str(obj))

    # Get the smallest matching subnet
    return (
        device.interfaces.filter(**query)
        .order_by("ip_addresses__address__net_mask_length")
        .last()
    )


def get_prefix(ip_address):
    return (
        Prefix.objects.filter(prefix__net_contained_or_equal=str(ip_address))
        .order_by("prefix__net_mask_length")
        .last()
    )


def get_address(device: Device, interface: Union[Interface, VLAN]):
    if isinstance(interface, Interface):
        return interface.ip_addresses.first()
    else:
        vlan_prefixes = [str(p.prefix) for p in interface.prefixes.all()]
        vlan_prefixes = Cast(vlan_prefixes, output_field=ArrayField(IPAddressField()))
        return IPAddress.objects.filter(
            interface__device=device, address__net_contained_or_equal=Any(vlan_prefixes)
        ).first()


def orm_or(**filters):
    query = Q()
    for k, v in filters.items():
        query |= Q(**{k: v})
    return query
