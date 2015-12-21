import sys
from unittest import TestCase, makeSuite, TextTestRunner
from blockadjust import adjust

class TargetRangeAdjustTest(TestCase):

    def test_bogus_network(self):
        adjustments = (
            (['1.0.0.0/33'], []),
            (['1.0.0.0/32', '1.0.0.0/33'], ['1.0.0.0/32']),
            (['1::/129'], []),
            (['1::/128', '1::/129'], ['1::/128']),
        )
        for networks, expected_networks in adjustments:
            self.assertEqual(adjust(networks), expected_networks)

    def test_single_network(self):
        adjustments = (
            (['1.0.0.0/8'], ['1.0.0.0/8']),
            (['1::/48'], ['1::/48']),
        )
        for networks, expected_networks in adjustments:
            self.assertEqual(adjust(networks), expected_networks)

    def test_v6(self):
        networks = ['1::/48', '1::/64']
        expected_networks = ['1::/64', '1:0:0:1::/64', '1:0:0:2::/63',
                             '1:0:0:4::/62', '1:0:0:8::/61', '1:0:0:10::/60',
                             '1:0:0:20::/59', '1:0:0:40::/58', '1:0:0:80::/57',
                             '1:0:0:100::/56', '1:0:0:200::/55', '1:0:0:400::/54',
                             '1:0:0:800::/53', '1:0:0:1000::/52', '1:0:0:2000::/51',
                             '1:0:0:4000::/50', '1:0:0:8000::/49']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_largest_subnet_pos_first(self):
        networks = ['1.0.0.0/8', '1.0.0.0/9']
        expected_networks = ['1.0.0.0/9', '1.128.0.0/9']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_largest_subnet_pos_last(self):
        networks = ['1.0.0.0/8', '1.128.0.0/9']
        expected_networks = ['1.0.0.0/9', '1.128.0.0/9']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_large_subnet_pos_first(self):
        networks = ['1.0.0.0/8', '1.0.0.0/10']
        expected_networks = ['1.0.0.0/10', '1.64.0.0/10', '1.128.0.0/9']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_large_subnet_pos_second(self):
        networks = ['1.0.0.0/8', '1.64.0.0/10']
        expected_networks = ['1.0.0.0/10', '1.64.0.0/10', '1.128.0.0/9']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_large_subnet_pos_third(self):
        networks = ['1.0.0.0/8', '1.128.0.0/10']
        expected_networks = ['1.0.0.0/9', '1.128.0.0/10', '1.192.0.0/10']
        self.assertEqual(adjust(networks), expected_networks)

    def test_supernet_large_subnet_pos_last(self):
        networks = ['1.0.0.0/8', '1.192.0.0/10']
        expected_networks = ['1.0.0.0/9', '1.128.0.0/10', '1.192.0.0/10']
        self.assertEqual(adjust(networks), expected_networks)

    def test_small_network(self):
        networks = ['1.0.0.0/24', '1.0.0.5/32']
        expected_networks = ['1.0.0.0/30', '1.0.0.4/32', '1.0.0.5/32',
                             '1.0.0.6/31', '1.0.0.8/29', '1.0.0.16/28',
                             '1.0.0.32/27', '1.0.0.64/26', '1.0.0.128/25']
        self.assertEqual(adjust(networks), expected_networks)

if __name__ == '__main__':
    test_suite = makeSuite(TargetRangeAdjustTest)
    test_runner = TextTestRunner(verbosity=1)
    results = test_runner.run(test_suite)
    failures = len(results.errors) + len(results.failures)
    sys.exit(0 if failures == 0 else 2)
