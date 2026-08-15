import time
import unittest
from unittest.mock import Mock

from llama_monitor import LLAMAServerClient, TTUInterface, is_local_server
from llama_monitor_core import BackendKind, parse_prometheus_metrics


VLLM_METRICS = """\
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running{model_name="demo"} 2
vllm:num_requests_waiting{model_name="demo"} 3
vllm:kv_cache_usage_perc{model_name="demo"} 0.625
vllm:prefix_cache_queries{model_name="demo"} 200
vllm:prefix_cache_hits{model_name="demo"} 150
vllm:prompt_tokens_total{model_name="demo"} 1200
vllm:generation_tokens_total{model_name="demo"} 320
vllm:num_preemptions_total{model_name="demo"} 1
"""


class VLLMMetricsTests(unittest.TestCase):
    def setUp(self):
        self.client = LLAMAServerClient("http://localhost:8000")

    def tearDown(self):
        self.client.close()

    def test_vllm_metrics_map_to_dashboard_stats(self):
        stats = self.client._parse_prometheus_metrics(VLLM_METRICS)

        self.assertEqual(stats["running_requests"], 2)
        self.assertEqual(stats["waiting_requests"], 3)
        self.assertEqual(stats["prompt_eval_count"], 1200)
        self.assertEqual(stats["eval_count"], 320)
        self.assertEqual(stats["preemptions"], 1)
        self.assertEqual(stats["kv_cache_usage_percent"], 62.5)
        self.assertEqual(stats["cache_hit_rate"], 75)

    def test_vllm_metrics_select_vllm_backend(self):
        self.client.available_endpoints = {"/metrics": {"raw": VLLM_METRICS}}
        self.client._detect_backend()
        self.assertEqual(self.client.backend, "vllm")

    def test_one_payload_serves_stats_and_tasks_without_network(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("metrics payload must be reused")

            def close(self):
                pass

        self.client.session = NoNetworkSession()
        self.client.backend = BackendKind.VLLM.value
        stats, _, _, _ = self.client.get_fresh_stats(1000, 300, time.time() - 1, metrics_text=VLLM_METRICS)
        tasks, _, _ = self.client.get_fresh_tasks(1000, 300, metrics_text=VLLM_METRICS)

        self.assertEqual(stats["eval_delta"], 20)
        self.assertEqual(len([task for task in tasks if task["status"] == "queued"]), 3)

    def test_normal_tui_refresh_fetches_one_metrics_snapshot(self):
        ui = object.__new__(TTUInterface)
        ui._prev_prompt_count = 1000
        ui._prev_eval_count = 300
        ui._prev_stats_time = time.time() - 1
        ui.endpoint_refresh_counter = 0
        ui.endpoint_refresh_interval = 30
        ui._has_probed_endpoints = True
        ui._next_endpoint_probe = 0.0
        ui._endpoint_probe_backoff = 1.0
        ui.api_consecutive_failures = 0
        ui.api_errors = 0
        ui.last_successful_api = None
        ui.last_update = None
        ui.model_info = None
        ui.stats = None
        ui.tasks = []
        ui.tps_history = []
        ui._slot_tps_tracker = {}
        ui.logger = Mock()

        self.client.backend = BackendKind.VLLM.value
        self.client.available_endpoints = {"/health": {"status": "ok"}}
        self.client.fetch_metrics_text = Mock(return_value=VLLM_METRICS)
        self.client.update_data = Mock(side_effect=AssertionError("normal refresh must not probe"))

        ui.refresh_api_data(self.client)

        self.client.fetch_metrics_text.assert_called_once_with()
        self.client.update_data.assert_not_called()
        self.assertEqual(ui.stats["waiting_requests"], 3)
        self.assertEqual(len([task for task in ui.tasks if task["status"] == "queued"]), 3)

    def test_counter_reset_uses_new_counter_as_delta(self):
        stats, _, _, _ = self.client.get_fresh_stats(5000, 5000, time.time() - 1, metrics_text=VLLM_METRICS)
        self.assertEqual(stats["eval_delta"], 320)
        self.assertEqual(stats["prompt_delta"], 1200)

    def test_typed_parser_aggregates_labeled_workers(self):
        metrics = VLLM_METRICS + 'vllm:generation_tokens_total{model_name="other"} 80\n'
        snapshot = parse_prometheus_metrics(metrics)
        self.assertEqual(snapshot.backend, BackendKind.VLLM)
        self.assertEqual(snapshot.generation_tokens, 400)

    def test_negative_queue_and_request_gauges_are_clamped(self):
        snapshot = parse_prometheus_metrics(
            "vllm:num_requests_running -2\nvllm:num_requests_waiting -3\nvllm:num_preemptions_total -1\n"
        )

        self.assertEqual(snapshot.running_requests, 0)
        self.assertEqual(snapshot.waiting_requests, 0)
        self.assertEqual(snapshot.preemptions, 0)

    def test_local_server_detection(self):
        self.assertTrue(is_local_server("http://127.0.0.1:8000"))
        self.assertTrue(is_local_server("http://localhost:8000"))
        self.assertFalse(is_local_server("https://inference.example.com"))


if __name__ == "__main__":
    unittest.main()
