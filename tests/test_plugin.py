import json
import unittest
from unittest.mock import patch

import httpx
from dify_plugin import DifyPluginEnv
from dify_plugin.core.plugin_registration import PluginRegistration
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from page_tools_client import BASE_URL, MAX_RESPONSE_BYTES, fetch_page, validate_url
from provider.circadian_page_tools import CircadianPageToolsProvider
from tools.extract_page import ExtractPageTool
from tools.page_metadata import PageMetadataTool

CLIENT = httpx.Client
KEY = "test-key-for-offline-tests-only"
TARGET = "https://example.com/path?source=dify&nested=a%26b&unicode=%C3%B8"
EXTRACT = {"ok": True, "httpStatus": 200, "truncated": False, "title": "Example",
           "markdown": "# Example\n\nReference text", "url": TARGET, "finalUrl": TARGET,
           "description": None, "wordCount": 3, "links": []}
META = {"ok": True, "httpStatus": 200, "truncated": False, "title": "Example",
        "openGraph": {}, "twitter": {}, "jsonLd": [], "canonical": None}


class PluginTests(unittest.TestCase):
    def transport(self, handler):
        def factory(**kwargs):
            self.assertFalse(kwargs["follow_redirects"])
            self.assertEqual(kwargs["timeout"].connect, 5)
            self.assertEqual(kwargs["timeout"].read, 25)
            return CLIENT(transport=httpx.MockTransport(handler), **kwargs)
        return patch("page_tools_client.httpx.Client", side_effect=factory)

    def test_sdk_registers_both_tools_and_secret_field(self):
        registration = PluginRegistration(DifyPluginEnv())
        config, provider, tools = registration.tools_mapping["circadian_page_tools"]
        self.assertEqual(set(tools), {"extract_page", "page_metadata"})
        self.assertEqual(provider.__name__, "CircadianPageToolsProvider")
        provider()._validate_credentials({"api_key": KEY})
        self.assertEqual(next(c for c in config.credentials_schema if c.name == "api_key").type.value, "secret-input")
        self.assertIsNone(registration.configuration.resource.permission.model)

    def test_save_credential_makes_no_network_call(self):
        with patch("page_tools_client.httpx.Client", side_effect=AssertionError("network forbidden")):
            CircadianPageToolsProvider()._validate_credentials({"api_key": KEY})
            for value in (None, "", "a\nb", "a b", "key\rheader", "ø", "a" * 513):
                with self.subTest(value=value):
                    with self.assertRaises(ToolProviderCredentialValidationError):
                        CircadianPageToolsProvider()._validate_credentials({"api_key": value})

    def test_exact_request_and_real_sdk_outputs(self):
        for cls, endpoint, payload in ((ExtractPageTool, "extract", EXTRACT),
                                       (PageMetadataTool, "meta", META)):
            seen = []
            def handler(request):
                seen.append(request)
                self.assertEqual(request.method, "GET")
                self.assertEqual(str(request.url).split("?", 1)[0], BASE_URL + endpoint)
                self.assertEqual(list(request.url.params.multi_items()), [("url", TARGET)])
                self.assertEqual(request.headers["x-api-market-key"], KEY)
                self.assertEqual(request.content, b"")
                return httpx.Response(200, json=payload)
            with self.subTest(tool=endpoint), self.transport(handler):
                messages = list(cls.from_credentials({"api_key": KEY}).invoke({"url": TARGET}))
                self.assertEqual(messages[0].message.json_object, payload)
                if endpoint == "extract":
                    self.assertEqual(messages[1].message.text, EXTRACT["markdown"])
                else:
                    self.assertEqual(len(messages), 1)
                self.assertEqual(len(seen), 1)

    def test_bad_inputs_never_reach_gateway(self):
        invalid = (None, "", "not-a-url", "file:///etc/passwd", "ftp://example.com/",
                   "https://user:password@example.com/", "https://example.com/#private",
                   "https://example.com:8443/", "https://example.com:bad/", "https://example.com\\@localhost/",
                   "http://127.0.0.1/", "http://[::1]/", "http://[fe80::1%eth0]/",
                   "http://10.0.0.1/", "http://169.254.169.254/", "http://localhost/",
                   "http://x.local/", "http://x.internal/", "http://localhost./", "http://singlelabel/",
                   "https://example.com/\n", "https://example.com/" + "a" * 8192)
        with patch("page_tools_client.httpx.Client", side_effect=AssertionError("network forbidden")):
            for url in invalid:
                with self.subTest(url=url):
                    with self.assertRaises(ValueError):
                        fetch_page("extract", KEY, url)
            with self.assertRaises(ValueError):
                fetch_page("https://other.example/", KEY, TARGET)

    def test_common_public_urls_remain_intact(self):
        for url in (TARGET, "https://example.com/", "http://example.com:80/", "https://example.com:443/",
                    "https://8.8.8.8/", "https://[2606:4700:4700::1111]/"):
            self.assertEqual(validate_url(url), url)

    def test_gateway_errors_do_not_leak_or_retry(self):
        for status in (301, 302, 307, 400, 401, 402, 403, 422, 429, 500, 503):
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status, headers={"location": "https://other.example/"},
                                      text=KEY + TARGET)
            with self.subTest(status=status), self.transport(handler):
                with self.assertRaises(ValueError) as raised:
                    fetch_page("meta", KEY, TARGET)
                self.assertIn(f"HTTP {status}", str(raised.exception))
                self.assertNotIn(KEY, str(raised.exception))
                self.assertNotIn(TARGET, str(raised.exception))
                self.assertEqual(len(calls), 1)

    def test_timeout_is_safe_and_not_retried(self):
        seen = []
        def handler(request):
            seen.append(request)
            raise httpx.ReadTimeout(KEY + TARGET, request=request)
        with self.transport(handler):
            with self.assertRaisesRegex(ValueError, "already have been charged") as raised:
                fetch_page("extract", KEY, TARGET)
            self.assertNotIn(KEY, str(raised.exception))
            self.assertNotIn(TARGET, str(raised.exception))
            self.assertEqual(len(seen), 1)

    def test_malformed_and_oversized_responses_fail_safely(self):
        for content, headers in ((b"not json " + KEY.encode(), {"content-type": "application/json"}),
                                 (b"x" * (MAX_RESPONSE_BYTES + 1), {"content-type": "application/json"}),
                                 (b"<html>not API data</html>", {"content-type": "text/html"}),
                                 (b"\xff", {"content-type": "application/json"})):
            with self.subTest(size=len(content)), self.transport(lambda _: httpx.Response(200, content=content, headers=headers)):
                with self.assertRaises(ValueError) as raised:
                    fetch_page("extract", KEY, TARGET)
                self.assertNotIn(KEY, str(raised.exception))

    def test_target_error_cannot_masquerade_as_success(self):
        for status in (400, 403, 404, 500):
            payload = dict(EXTRACT, httpStatus=status)
            with self.subTest(status=status), self.transport(lambda _: httpx.Response(200, json=payload)):
                with self.assertRaisesRegex(ValueError, f"target page returned HTTP {status}"):
                    list(ExtractPageTool.from_credentials({"api_key": KEY}).invoke({"url": TARGET}))

    def test_incomplete_api_shapes_are_rejected(self):
        for payload in ([], None, {"ok": False, "error": KEY}, {}, dict(EXTRACT, httpStatus=True),
                        dict(EXTRACT, httpStatus="200"), dict(EXTRACT, truncated=None),
                        dict(EXTRACT, markdown=None)):
            with self.subTest(payload=payload), self.transport(lambda _: httpx.Response(200, json=payload)):
                with self.assertRaises(ValueError) as raised:
                    fetch_page("extract", KEY, TARGET)
                self.assertNotIn(KEY, str(raised.exception))
        with self.transport(lambda _: httpx.Response(200, json=dict(META, jsonLd="wrong"))):
            with self.assertRaisesRegex(ValueError, "incomplete metadata"):
                fetch_page("meta", KEY, TARGET)

    def test_truncation_flag_and_empty_metadata_are_preserved(self):
        with self.transport(lambda _: httpx.Response(200, json=dict(EXTRACT, truncated=True))):
            self.assertTrue(fetch_page("extract", KEY, TARGET)["truncated"])
        with self.transport(lambda _: httpx.Response(200, json=META)):
            self.assertEqual(fetch_page("meta", KEY, TARGET)["jsonLd"], [])


if __name__ == "__main__":
    unittest.main()
