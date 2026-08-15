"""Prometheus metric parsing and backend-specific normalization."""

import math
import re
from typing import Dict, Iterable, Tuple

from .models import BackendKind, MetricSnapshot


_SAMPLE_RE = re.compile(
    r"^([A-Za-z_:][A-Za-z0-9_:]*)"
    r"(?:\{.*\})?\s+"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[+-]?(?:Inf|NaN))"
    r"(?:\s+\d+)?$"
)


def detect_backend(metrics_text: str) -> BackendKind:
    if "vllm:" in metrics_text or "vllm_" in metrics_text:
        return BackendKind.VLLM
    if "llamacpp:" in metrics_text or "llama_" in metrics_text:
        return BackendKind.LLAMA_CPP
    return BackendKind.OPENAI_COMPATIBLE


def _samples(metrics_text: str) -> Iterable[Tuple[str, float]]:
    for raw_line in metrics_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _SAMPLE_RE.match(line)
        if not match:
            continue
        try:
            value = float(match.group(2))
        except ValueError:
            continue
        if math.isfinite(value):
            yield match.group(1), value


def parse_prometheus_metrics(metrics_text: str) -> MetricSnapshot:
    """Normalize supported llama.cpp and vLLM samples into one snapshot."""
    backend = detect_backend(metrics_text)
    values: Dict[str, float] = {}

    sum_metrics = {
        "vllm:num_requests_running",
        "vllm:num_requests_waiting",
        "vllm:prefix_cache_queries",
        "vllm:prefix_cache_hits",
        "vllm:prompt_tokens_total",
        "vllm:generation_tokens_total",
        "vllm:num_preemptions_total",
    }
    max_metrics = {"vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"}

    for name, value in _samples(metrics_text):
        if name in sum_metrics:
            values[name] = values.get(name, 0.0) + value
        elif name in max_metrics:
            values[name] = max(values.get(name, 0.0), value)
        else:
            values[name] = value

    snapshot = MetricSnapshot(backend=backend)

    if backend == BackendKind.VLLM:
        snapshot.running_requests = max(0, int(values.get("vllm:num_requests_running", 0)))
        snapshot.waiting_requests = max(0, int(values.get("vllm:num_requests_waiting", 0)))
        snapshot.prompt_tokens = max(0, int(values.get("vllm:prompt_tokens_total", 0)))
        snapshot.generation_tokens = max(0, int(values.get("vllm:generation_tokens_total", 0)))
        snapshot.preemptions = max(0, int(values.get("vllm:num_preemptions_total", 0)))
        snapshot.kv_cache_usage_percent = (
            max(
                values.get("vllm:kv_cache_usage_perc", 0),
                values.get("vllm:gpu_cache_usage_perc", 0),
            )
            * 100
        )
        cache_queries = values.get("vllm:prefix_cache_queries", 0)
        if cache_queries > 0:
            snapshot.cache_hit_rate = values.get("vllm:prefix_cache_hits", 0) / cache_queries * 100
        return snapshot

    snapshot.running_requests = int(
        values.get("llamacpp:requests_processing", values.get("llama_processing_running", 0))
    )
    snapshot.generation_tokens = int(
        values.get("llamacpp:tokens_predicted_total", values.get("llama_request_eval_count_sum", 0))
    )
    snapshot.prompt_tokens = int(
        values.get("llamacpp:prompt_tokens_total", values.get("llama_request_prompt_eval_count_sum", 0))
    )
    snapshot.tokens_per_second = values.get(
        "llamacpp:predicted_tokens_seconds", values.get("llama_token_per_second_decode", 0)
    )
    snapshot.prompt_tokens_per_second = values.get(
        "llamacpp:prompt_tokens_seconds", values.get("llama_token_per_second_prompt_eval", 0)
    )
    snapshot.total_decode_time = values.get(
        "llamacpp:tokens_predicted_seconds_total", values.get("llama_token_decode_seconds_sum", 0)
    )
    snapshot.total_prompt_time = values.get(
        "llamacpp:prompt_seconds_total", values.get("llama_token_prompt_eval_seconds_sum", 0)
    )
    snapshot.avg_busy_slots = values.get("llamacpp:n_busy_slots_per_decode", 0)
    snapshot.total_requests = int(values.get("llama_request_counter", 0))
    snapshot.cache_hit_rate = values.get("llama_context_hit_ratio", 0) * 100

    if snapshot.tokens_per_second <= 0 and snapshot.total_decode_time > 0:
        snapshot.tokens_per_second = snapshot.generation_tokens / snapshot.total_decode_time
    if snapshot.prompt_tokens_per_second <= 0 and snapshot.total_prompt_time > 0:
        snapshot.prompt_tokens_per_second = snapshot.prompt_tokens / snapshot.total_prompt_time
    return snapshot
