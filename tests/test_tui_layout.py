import unittest
from collections import deque
from unittest.mock import patch

import llama_monitor as monitor


class FakeScreen:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.calls = []

    def getmaxyx(self):
        return self.height, self.width

    def erase(self):
        pass

    def addnstr(self, *args):
        self.calls.append(args)

    def refresh(self):
        pass


class FakeLogger:
    def debug(self, *args):
        pass


def make_ui(height, width, system_scope="local"):
    ui = object.__new__(monitor.TTUInterface)
    ui.stdscr = FakeScreen(height, width)
    ui.logger = FakeLogger()
    ui.system_scope = system_scope
    ui.backend = "vllm"
    ui.last_update = ui.last_successful_api = None
    ui.model_info = {"name": "/private/models/demo.gguf"}
    ui.cpu_info = {"usage": 42, "frequency": 4200, "cores": 8, "threads": 16}
    ui.memory_info = {"percent": 68, "used": 16, "total": 32}
    ui.gpu_info = [{"name": "GPU-A", "utilization": 51, "memory_used": 10, "memory_total": 20, "temperature": 63}]
    ui.stats = {
        "tokens_per_second": 33.2,
        "running_requests": 1,
        "waiting_requests": 2,
        "kv_cache_usage_percent": 50,
    }
    ui.tasks = [{"status": "running", "stage": "decode", "progress": 25, "tps": 33.2}]
    ui.cpu_usage_history = deque([10, 20, 42])
    ui.memory_usage_history = deque([50, 60, 68])
    ui.tps_history = deque([12, 24, 33.2])
    ui.refresh_interval = 1.0
    ui.i18n = monitor.I18n("en")
    return ui


class BtopLayoutTests(unittest.TestCase):
    @patch.object(monitor.curses, "color_pair", side_effect=lambda value: value << 8)
    def test_minimum_supported_layout_renders(self, _color_pair):
        ui = make_ui(24, 74)
        ui._draw_btop_ui()
        self.assertTrue(ui.stdscr.calls)

    @patch.object(monitor.curses, "color_pair", side_effect=lambda value: value << 8)
    def test_remote_scope_is_explicit(self, _color_pair):
        ui = make_ui(32, 120, system_scope="off")
        ui._draw_btop_ui()
        rendered = " ".join(str(call[2]) for call in ui.stdscr.calls)
        self.assertIn("remote API telemetry", rendered)
        self.assertIn("LOCAL METRICS OFF", rendered)
        self.assertIn("demo.gguf", rendered)
        self.assertNotIn("/private/models", rendered)

    @patch.object(monitor.curses, "color_pair", side_effect=lambda value: value << 8)
    def test_small_terminal_gets_resize_message(self, _color_pair):
        ui = make_ui(20, 70)
        ui._draw_btop_ui()
        rendered = " ".join(str(call[2]) for call in ui.stdscr.calls)
        self.assertIn("Terminal too small", rendered)


if __name__ == "__main__":
    unittest.main()
