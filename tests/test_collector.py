"""
تست‌های NoizVpn Subscription Service
اجرا: python -m unittest discover -s tests -v
"""

import base64
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import parser


class TestExtraction(unittest.TestCase):
    def test_extract_vless(self):
        text = "join vless://11111111-1111-1111-1111-111111111111@1.2.3.4:443?security=tls&type=ws#old"
        self.assertEqual(len(parser.extract_uris(text)), 1)

    def test_extract_multiple_schemes(self):
        text = (
            "vless://uuid@1.2.3.4:443?type=tcp#a\n"
            "vmess://eyJhZGQiOiI1LjYuNy44IiwicG9ydCI6NDQzLCJpZCI6InV1aWQiLCJwcyI6Im9sZCJ9\n"
            "trojan://pass@1.2.3.4:443#b\n"
            "ss://YWVzLTI1Ni1nY206cGFzcw==@1.2.3.4:8388#c\n"
        )
        uris = parser.extract_uris(text)
        self.assertEqual(len(uris), 4)

    def test_ss_not_matched_inside_vless(self):
        text = "vless://uuid@1.2.3.4:443?type=tcp#x"
        uris = parser.extract_uris(text)
        self.assertTrue(all(u.startswith("vless://") for u in uris))

    def test_trailing_junk_stripped(self):
        text = "vless://uuid@1.2.3.4:443?type=tcp#x),"
        uris = parser.extract_uris(text)
        self.assertTrue(uris[0].endswith("#x"))


class TestRename(unittest.TestCase):
    def test_vless_remark_replaced(self):
        uri = "vless://uuid@1.2.3.4:443?security=tls&type=ws&path=/x#old name"
        new = parser.set_remark(uri, "NEW")
        self.assertIn("#NEW", new)
        self.assertNotIn("old name", new)
        self.assertIn("security=tls", new)
        self.assertIn("path=/x", new)

    def test_vmess_remark_replaced_and_params_kept(self):
        payload = base64.b64encode(json.dumps({
            "v": "2", "ps": "old", "add": "1.2.3.4", "port": "443",
            "id": "uuid", "aid": "0", "net": "ws", "tls": "tls", "path": "/x",
        }).encode()).decode()
        uri = f"vmess://{payload}"
        new = parser.set_remark(uri, "NEW")
        data = json.loads(base64.b64decode(new[len("vmess://"):]).decode())
        self.assertEqual(data["ps"], "NEW")
        self.assertEqual(data["add"], "1.2.3.4")
        self.assertEqual(data["path"], "/x")

    def test_ss_remark_replaced(self):
        uri = "ss://YWVzLTI1Ni1nY206cGFzcw==@1.2.3.4:8388#old"
        new = parser.set_remark(uri, "NEW")
        self.assertIn("#NEW", new)
        self.assertTrue(new.startswith("ss://"))

    def test_strip_remark_for_dedup(self):
        a = parser.strip_remark("vless://uuid@1.2.3.4:443?type=tcp#one")
        b = parser.strip_remark("vless://uuid@1.2.3.4:443?type=tcp#two")
        self.assertEqual(a, b)


class TestOutput(unittest.TestCase):
    def test_base64_roundtrip(self):
        payload = "vless://uuid@1.2.3.4:443?type=tcp#x\nvmess://abc\n"
        encoded = base64.b64encode(payload.encode()).decode()
        self.assertEqual(base64.b64decode(encoded).decode(), payload)

    def test_signature_is_valid_vless(self):
        self.assertTrue(config.SIGNATURE_URI.startswith("vless://"))
        self.assertIn("127.0.0.1", config.SIGNATURE_URI)
        self.assertIn(config.SIGNATURE_REMARK, config.SIGNATURE_URI)

    def test_remark_template(self):
        remark = config.REMARK_TEMPLATE.format(emoji="⚡️")
        self.assertEqual(remark, "[⚡️]==>@NoizVpn جوین شو تلگرام")


class TestCollectorIntegration(unittest.TestCase):
    def test_build_configs_caps_at_max(self):
        import collector
        raw = "\n".join(
            f"vless://uuid{i}@1.2.3.4:443?type=tcp#old{i}" for i in range(3000)
        )
        configs = collector.build_configs(raw)
        self.assertEqual(len(configs), 3000)  # build_configs does not cap
        final = [config.SIGNATURE_URI] + configs[: config.MAX_CONFIGS - 1]
        self.assertEqual(len(final), config.MAX_CONFIGS)

    def test_dedup_collapses_same_server(self):
        import collector
        raw = (
            "vless://uuid@1.2.3.4:443?type=tcp#one\n"
            "vless://uuid@1.2.3.4:443?type=tcp#two\n"
        )
        configs = collector.build_configs(raw)
        self.assertEqual(len(configs), 1)


if __name__ == "__main__":
    unittest.main()
