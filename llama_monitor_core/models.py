"""Typed telemetry snapshots shared by collectors, adapters, and the TUI."""

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any, Dict, List, Optional


class BackendKind(str, Enum):
    AUTO = "auto"
    LLAMA_CPP = "llama.cpp"
    VLLM = "vllm"
    OPENAI_COMPATIBLE = "openai-compatible"


class SystemScope(str, Enum):
    AUTO = "auto"
    LOCAL = "local"
    OFF = "off"


@dataclass
class MetricSnapshot:
    backend: BackendKind = BackendKind.OPENAI_COMPATIBLE
    running_requests: int = 0
    waiting_requests: int = 0
    prompt_tokens: int = 0
    generation_tokens: int = 0
    tokens_per_second: float = 0.0
    prompt_tokens_per_second: float = 0.0
    cache_hit_rate: float = 0.0
    kv_cache_usage_percent: float = 0.0
    preemptions: int = 0
    total_requests: int = 0
    total_decode_time: float = 0.0
    total_prompt_time: float = 0.0
    avg_busy_slots: float = 0.0
    collected_at: float = field(default_factory=time)

    def to_stats(self) -> Dict[str, Any]:
        """Return the legacy dict shape consumed by the existing TUI."""
        return {
            "running_requests": self.running_requests,
            "waiting_requests": self.waiting_requests,
            "prompt_eval_count": self.prompt_tokens,
            "eval_count": self.generation_tokens,
            "tokens_per_second": self.tokens_per_second,
            "eval_per_second": self.tokens_per_second,
            "prompt_eval_per_second": self.prompt_tokens_per_second,
            "cache_hit_rate": self.cache_hit_rate,
            "kv_cache_usage_percent": self.kv_cache_usage_percent,
            "preemptions": self.preemptions,
            "total_requests": self.total_requests,
            "total_decode_time": self.total_decode_time,
            "total_prompt_time": self.total_prompt_time,
            "avg_busy_slots": self.avg_busy_slots,
        }


@dataclass
class ServerSnapshot:
    backend: BackendKind
    metrics: MetricSnapshot
    model: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    version: Optional[str] = None
    scrape_duration: float = 0.0
    error: Optional[str] = None
    collected_at: float = field(default_factory=time)

    @property
    def healthy(self) -> bool:
        return self.error is None
