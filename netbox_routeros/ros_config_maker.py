from ipaddress import collapse_addresses, IPv4Interface, IPv6Address, IPv6Network, IPv4Network, ip_network
from typing import Union

import django.apps
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func
from django.db.models.functions import Cast
from jinja2 import Environment, DictLoader
from netaddr import IPNetwork

from dcim.models import Device, Interface
from ipam.fields import IPAddressField
from ipam.models import IPAddress, VLAN, Q, Prefix
from netbox_routeros.models import ConfigurationTemplate


class Any(Func):
    function = 'ANY'


def render_ros_config(device: Device, template_name: str, template_content: str = None):
    templates = dict(ConfigurationTemplate.objects.all().values_list('slug', 'content'))
    if template_content:
        templates[template_name] = template_content

    # Make all models available for custom querying
    models = {m._meta.object_name: m for m in django.apps.apps.get_models()}

    env = Environment(
        loader=DictLoader(templates),
    )
    template = env.get_template(template_name)

    return template.render(
        device=device,
        ip_addresses=_context_ip_addresses(device),
        vlans=_context_vlans(device),
        prefixes=_context_prefixes(device),
        **get_template_functions(),
        **models
    )


def _context_ip_addresses(device: Device):
    # TODO: Test
    return IPAddress.objects.filter(interface__device=device)


def _context_vlans(device: Device):
    # TODO: Test
    return VLAN.objects.filter(prefixes__prefix__net_contains=_any_address(device))


def _context_prefixes(device: Device):
    # TODO: Test
    return Prefix.objects.filter(prefix__net_contains=_any_address(device))


def _any_address(device: Device):
    """Utility for querying against any device address"""
    addresses = [str(ip.ip) for ip in IPAddress.objects.filter(interface__device=device).values_list('address', flat=True)]
    addresses = Cast(addresses, output_field=ArrayField(IPAddressField()))
    return Any(addresses)


def get_template_functions():
    return dict(
        get_loopback=get_loopback,
        combine_prefixes=combine_prefixes,
        get_interface=get_interface,
    )


def get_loopback(device: Device) -> IPAddress:
    loopback = IPAddress.objects.filter(interface__device=device, role="loopback").first()
    if loopback:
        return loopback.address.ip


def combine_prefixes(prefixes, only_combined=False):
    in_prefixes = [ip_network(p.prefix if isinstance(p, Prefix) else p) for p in prefixes]
    out_prefixes = list(
        collapse_addresses([p for p in in_prefixes if p.version == 4])
    ) + list(
        collapse_addresses([p for p in in_prefixes if p.version == 6])
    )

    if only_combined:
        out_prefixes = [p for p in out_prefixes if p not in in_prefixes]

    # Ensure we use the netaddr IPAddress, rather than the ipaddress.IPvXNetwork
    return [IPNetwork(str(p)) for p in out_prefixes]


def get_interface(device: Device, obj: Union[str, IPv4Interface, IPv4Network, IPv6Address, IPv6Network, Prefix, VLAN]):
    if isinstance(obj, Prefix):
        obj = obj.prefix

    if isinstance(obj, str):
        obj = ip_network(obj)

    if isinstance(obj, VLAN):
        vlan_filter = Q(untagged_vlan=obj) | Q(tagged_vlans=obj)
        return device.interfaces.filter(vlan_filter).first()

    if obj.max_prefixlen == obj.prefixlen:
        # A /32 or /128, so query based on the IP host
        query = dict(ip_addresses__address__net_host=str(obj))
    else:
        # A subnet of some sort
        query = dict(ip_addresses__address__net_contained_or_equal=str(obj))

    # Get the smallest matching subnet
    return device.interfaces.filter(**query).order_by('ip_addresses__address__net_mask_length').last()
