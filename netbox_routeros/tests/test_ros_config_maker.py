from netaddr import IPAddress, IPNetwork

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

    def test_has_two_loopback(self):
        device = self.data.device()
        ip_address_obj1 = self.data.ip_address('100.127.0.11', role='loopback')
        ip_address_obj2 = self.data.ip_address('100.127.0.10', role='loopback')
        self.ether1 = self.data.interface(device=device, ip_address=ip_address_obj1)
        self.ether1 = self.data.interface(device=device, ip_address=ip_address_obj2)

        self.assertEqual(get_loopback(device), IPAddress('100.127.0.10'))
        self.assertEqual(get_loopback(device, number=1), IPAddress('100.127.0.10'))
        self.assertEqual(get_loopback(device, number=2), IPAddress('100.127.0.11'))

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

    def test_from_ip_address_with_prefix(self):
        self.assertEqual(get_interface(self.device, '10.5.0.1/24'), self.ether2)

    def test_from_prefix_obj(self):
        prefix = self.data.prefix('10.5.0.0/24')
        self.assertEqual(get_interface(self.device, prefix), self.ether2)

    def test_from_ip_address_obj(self):
        prefix = self.data.ip_address('10.5.0.0/24')
        self.assertEqual(get_interface(self.device, prefix), self.ether2)

    def test_from_ip_netaddr_network(self):
        self.assertEqual(get_interface(self.device, IPNetwork('10.5.0.0/24')), self.ether2)

    def test_from_ip_netaddr_address(self):
        self.assertEqual(get_interface(self.device, IPAddress('10.5.0.1')), self.ether2)

    def test_from_prefix_network(self):
        self.assertEqual(get_interface(self.device, '10.5.0.0/24'), self.ether2)

    def test_from_vlan(self):
        self.assertEqual(get_interface(self.device, self.vlan1), self.ether2)


class GetVlanInterfaceTestCase(TestCaseMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.device = self.data.device()
        self.ether1 = self.data.interface(device=self.device, ip_address=[])
        self.ether2 = self.data.interface(device=self.device, ip_address=['10.5.0.1/24'])

        self.ip1 = self.data.ip_address('10.0.0.1/24')
        self.ip2 = self.data.ip_address('10.5.0.1/24')

        self.prefix1 = self.data.prefix('10.0.0.0/24')
        self.prefix2 = self.data.prefix('10.5.0.0/24')

        self.vlan1 = self.data.vlan()
        self.vlan2 = self.data.vlan()

    def test_ok(self):
        # Attach the vlan to the interface
        self.ether1.tagged_vlans.add(self.vlan1)

        # Put the prefixes on the vlan
        self.prefix1.vlan = self.vlan1
        self.prefix2.vlan = self.vlan1
        self.prefix1.save()
        self.prefix2.save()

        vlan = get_interface(self.device, '10.0.0.123', include_vlans=True)
        self.assertEqual(vlan, self.vlan1)

    def test_vlan_not_on_interface(self):
        # Attach the vlan to the interface
        # [NOPE]

        # Put the prefixes on the vlan
        self.prefix1.vlan = self.vlan1
        self.prefix2.vlan = self.vlan1
        self.prefix1.save()
        self.prefix2.save()

        vlan = get_interface(self.device, '10.0.0.123', include_vlans=True)
        self.assertEqual(vlan, None)

    def test_prefix_not_on_vlan(self):
        # Attach the vlan to the interface
        self.ether1.tagged_vlans.add(self.vlan1)

        # Put the prefixes on the vlan
        # [NOPE]

        vlan = get_interface(self.device, '10.0.0.123', include_vlans=True)
        self.assertEqual(vlan, None)


