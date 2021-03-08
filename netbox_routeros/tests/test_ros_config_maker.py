from netaddr import IPAddress, IPNetwork

from dcim.models import DeviceType
from ipam.models import Prefix
from netbox_routeros.ros_config_maker import _context_prefixes, get_interface, combine_prefixes, get_loopback
from netbox_routeros.testing import TestCaseMixin
from utilities.testing import TestCase


class TestContextData(TestCaseMixin, TestCase):

    def test_context_ip_addresses(self):
        pass
    

class GetLoopbackCase(TestCaseMixin, TestCase):

    def test_has_loopback(self):
        device = self.data.device()
        ip_address_obj = self.data.ip_address('100.127.0.1', role='loopback')
        self.ether1 = self.data.interface(device=device, ip_address=ip_address_obj)
        self.assertEqual(get_loopback(device), IPAddress('100.127.0.1'))

    def test_has_no_loopback(self):
        device = self.data.device()
        ip_address_obj = self.data.ip_address('10.0.0.1')
        self.assertEqual(get_loopback(device), None)


class CombinePrefixesTestCase(TestCaseMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.prefix1 = self.data.prefix('10.0.0.0/24')
        self.prefix2 = self.data.prefix('10.0.1.0/24')
        self.prefix3 = self.data.prefix('10.0.5.0/24')

    def test_list(self):
        self.assertEqual(
            combine_prefixes([self.prefix1, self.prefix2, self.prefix3]), [IPNetwork('10.0.0.0/23'), IPNetwork('10.0.5.0/24')]
        )

    def test_queryset(self):
        self.assertEqual(
            combine_prefixes(Prefix.objects.all()), [IPNetwork('10.0.0.0/23'), IPNetwork('10.0.5.0/24')]
        )

    def test_only_combined(self):
        self.assertEqual(
            combine_prefixes([self.prefix1, self.prefix2, self.prefix3], only_combined=True), [IPNetwork('10.0.0.0/23')]
        )


class GetInterfaceTestCase(TestCaseMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.device = self.data.device()
        self.vlan1 = self.data.vlan()
        self.ether1 = self.data.interface(device=self.device, ip_address=['10.0.0.1/24'])
        self.ether2 = self.data.interface(device=self.device, ip_address=['10.5.0.1/24'], vlan=self.vlan1)

    def test_from_ip_address(self):
        self.assertEqual(get_interface(self.device, '10.5.0.1'), self.ether2)

    def test_from_prefix_obj(self):
        prefix = self.data.prefix('10.5.0.0/24')
        self.assertEqual(get_interface(self.device, prefix), self.ether2)

    def test_from_prefix_network(self):
        self.assertEqual(get_interface(self.device, '10.5.0.0/24'), self.ether2)

    def test_from_vlan(self):
        self.assertEqual(get_interface(self.device, self.vlan1), self.ether2)

