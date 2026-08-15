import unittest

from llama_monitor_core import BackendKind, parse_prometheus_metrics


LLAMACPP_METRICS = """\
llamacpp:requests_processing 1
llamacpp:predicted_tokens_seconds 42.5
llamacpp:prompt_tokens_seconds 128.0
llamacpp:tokens_predicted_total 200
llamacpp:prompt_tokens_total 500
llamacpp:n_busy_slots_per_decode 1.0
"""


class LlamaCppMetricTests(unittest.TestCase):
    def test_llamacpp_metric_adapter(self):
        snapshot = parse_prometheus_metrics(LLAMACPP_METRICS)
        self.assertEqual(snapshot.backend, BackendKind.LLAMA_CPP)
        self.assertEqual(snapshot.running_requests, 1)
        self.assertEqual(snapshot.generation_tokens, 200)
        self.assertEqual(snapshot.prompt_tokens, 500)
        self.assertEqual(snapshot.tokens_per_second, 42.5)
        self.assertEqual(snapshot.prompt_tokens_per_second, 128.0)

    def test_non_finite_samples_are_ignored(self):
        snapshot = parse_prometheus_metrics("llamacpp:predicted_tokens_seconds NaN\n")
        self.assertEqual(snapshot.tokens_per_second, 0)


if __name__ == "__main__":
    unittest.main()
