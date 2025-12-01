import ipaddress
import unittest

import run


class NormalizationTests(unittest.TestCase):
    def test_ipv4_relaxed_leading_zeros(self):
        ip, ip_valid, version, subnet, steps, issues = run.normalize_ip("192.168.010.005")
        self.assertEqual(ip, "192.168.10.5")
        self.assertEqual(ip_valid, "true")
        self.assertEqual(version, "4")
        self.assertEqual(subnet, "192.168.10.0/24")
        self.assertIn("ip_parse_relaxed", steps)
        self.assertEqual(issues, [])

    def test_ipv6_zone_id_drop(self):
        ip, ip_valid, version, subnet, steps, issues = run.normalize_ip("fe80::1%eth0")
        self.assertEqual(ip, "fe80::1")
        self.assertEqual(ip_valid, "true")
        self.assertEqual(version, "6")
        self.assertEqual(subnet, "fe80::/64")
        self.assertIn("ip_drop_zone", steps)
        self.assertEqual(issues, [])

    def test_invalid_ipv4_returns_issue(self):
        ip, ip_valid, version, subnet, steps, issues = run.normalize_ip("10.0.1.300")
        self.assertEqual(ip_valid, "false")
        self.assertEqual(version, "")
        self.assertEqual(subnet, "")
        self.assertEqual(ip, "10.0.1.300")
        self.assertTrue(any(issue["type"] == "invalid" for issue in issues))
        self.assertIn("ip_invalid_parse", steps)

    def test_reserved_edge_flagged(self):
        _, ip_valid, _, _, steps, issues = run.normalize_ip("192.168.1.255")
        self.assertEqual(ip_valid, "true")
        self.assertIn("ip_reserved_edge", steps)
        self.assertTrue(any(issue["type"] == "reserved_edge" for issue in issues))

    def test_hostname_from_fqdn_and_validation(self):
        host, host_valid, fqdn, consistent, steps, issues = run.normalize_names("", "srv-1.example.com")
        self.assertEqual(host, "srv-1")
        self.assertEqual(host_valid, "true")
        self.assertEqual(fqdn, "srv-1.example.com")
        self.assertEqual(consistent, "true")
        self.assertIn("hostname_from_fqdn", steps)
        self.assertEqual(issues, [])

        host2, host2_valid, _, _, _, issues2 = run.normalize_names("bad_host", "")
        self.assertEqual(host2, "bad_host")
        self.assertEqual(host2_valid, "false")
        self.assertTrue(any(issue["field"] == "hostname" for issue in issues2))

    def test_mac_normalization_and_invalid(self):
        mac, mac_valid, steps, issues = run.normalize_mac("AA-BB-CC-DD-EE-FF")
        self.assertEqual(mac, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(mac_valid, "true")
        self.assertIn("mac_normalize", steps)
        self.assertEqual(issues, [])

        mac2, mac2_valid, _, issues2 = run.normalize_mac("AABBCC")
        self.assertEqual(mac2_valid, "false")
        self.assertTrue(any(issue["field"] == "mac" for issue in issues2))

    def test_owner_parsing_with_team_and_email(self):
        owner, email, team, steps = run.parse_owner("priya (platform) priya@corp.example.com")
        self.assertEqual(owner, "Priya")
        self.assertEqual(email, "priya@corp.example.com")
        self.assertEqual(team, "Platform")
        self.assertIn("owner_email_extract", steps)
        self.assertIn("owner_team_paren", steps)

    def test_device_inference_and_confidence(self):
        device, confidence, steps = run.normalize_device_type("", "edge-gw", "edge gw")
        self.assertEqual(device, "router")
        self.assertEqual(confidence, "medium")
        self.assertIn("device_inferred", steps)

        device2, confidence2, steps2 = run.normalize_device_type("server", "srv-1", "")
        self.assertEqual(device2, "server")
        self.assertEqual(confidence2, "high")
        self.assertIn("device_from_input", steps2)

    def test_site_normalization_mapping(self):
        site, site_norm, steps = run.normalize_site("HQ-BUILDING-1")
        self.assertEqual(site, "HQ-BUILDING-1")
        self.assertEqual(site_norm, "HQ BLDG 1")
        self.assertIn("site_normalize", steps)

    def test_default_subnet_private_and_link_local(self):
        self.assertEqual(run.default_subnet(ipaddress.ip_address("10.0.0.5")), "10.0.0.0/24")
        self.assertEqual(run.default_subnet(ipaddress.ip_address("169.254.1.1")), "169.254.0.0/16")


if __name__ == "__main__":
    unittest.main()
