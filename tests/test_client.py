import unittest
from unittest.mock import Mock

import requests

from llama_monitor import LLAMAServerClient, validate_server_url


class ClientConfigurationTests(unittest.TestCase):
    @staticmethod
    def _response(body: bytes, status_code: int = 200) -> requests.Response:
        response = requests.Response()
        response.status_code = status_code
        response._content = body
        response._content_consumed = True
        response.headers["Content-Length"] = str(len(body))
        response.encoding = "utf-8"
        return response

    def test_url_rejects_credentials_query_and_non_http_schemes(self):
        invalid_urls = [
            "http://user:pass@localhost:8000",
            "http://localhost:8000?token=secret",
            "file:///tmp/socket",
        ]
        for value in invalid_urls:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_server_url(value)

    def test_bearer_token_and_ca_are_configured_without_url_credentials(self):
        client = LLAMAServerClient(
            "https://inference.example.com",
            backend="vllm",
            api_key="secret-token",
            verify="/tmp/internal-ca.pem",
        )
        self.addCleanup(client.close)

        self.assertEqual(client.session.headers["Authorization"], "Bearer secret-token")
        self.assertEqual(client.session.verify, "/tmp/internal-ca.pem")
        self.assertNotIn("secret-token", client.base_url)

    def test_metrics_fetch_detects_backend(self):
        client = LLAMAServerClient("http://localhost:8000")
        response = self._response(b"vllm:num_requests_running 1\n")
        client.session.get = Mock(return_value=response)

        self.assertEqual(client.fetch_metrics_text(), response.text)
        self.assertEqual(client.backend, "vllm")
        client.session.get.assert_called_once_with(
            "http://localhost:8000/metrics",
            timeout=0.75,
            stream=True,
            allow_redirects=False,
        )
        client.close()

    def test_metrics_response_size_is_bounded(self):
        client = LLAMAServerClient("http://localhost:8000")
        self.addCleanup(client.close)
        client.MAX_RESPONSE_BYTES = 64
        client.session.get = Mock(return_value=self._response(b"x" * 65))

        self.assertIsNone(client.fetch_metrics_text())
        self.assertEqual(client.last_scrape_error, "RequestException")

    def test_streamed_response_without_content_length_is_still_bounded(self):
        client = LLAMAServerClient("http://localhost:8000")
        self.addCleanup(client.close)
        client.MAX_RESPONSE_BYTES = 64
        response = self._response(b"x" * 65)
        del response.headers["Content-Length"]
        client.session.get = Mock(return_value=response)

        self.assertIsNone(client.fetch_metrics_text())
        self.assertEqual(client.last_scrape_error, "RequestException")

    def test_metrics_response_at_limit_remains_supported(self):
        client = LLAMAServerClient("http://localhost:8000")
        self.addCleanup(client.close)
        body = b"vllm:num_requests_running 1\n".ljust(64, b" ")
        client.MAX_RESPONSE_BYTES = len(body)
        client.session.get = Mock(return_value=self._response(body))

        self.assertEqual(client.fetch_metrics_text(), body.decode())

    def test_waiting_task_rows_are_bounded_without_losing_aggregate(self):
        client = LLAMAServerClient("http://localhost:8000", backend="vllm")
        self.addCleanup(client.close)
        metrics = "vllm:num_requests_waiting 50000\n"

        tasks, _, _ = client.get_fresh_tasks(metrics_text=metrics)
        stats, _, _, _ = client.get_fresh_stats(metrics_text=metrics)

        self.assertEqual(len(tasks), client.MAX_DISPLAY_TASK_ROWS)
        self.assertEqual(stats["waiting_requests"], 50000)


if __name__ == "__main__":
    unittest.main()
