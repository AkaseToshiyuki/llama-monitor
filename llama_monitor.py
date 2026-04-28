#!/usr/bin/env python3
"""
LLAMA.cpp Monitor - Real-time monitoring tool for llama-server

A cross-platform CLI tool to monitor LLAMA.cpp (llama-server) status
with beautiful 256-color TUI interface.

Author: LLAMA.cpp Monitor Team
Version: 1.0.0
"""

import argparse
import curses
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional, Tuple

import requests

# Type hints for optional imports
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None  # type: ignore

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

# AMD GPU support (experimental)
try:
    import amdsmi
    AMDSMI_AVAILABLE = True
except ImportError:
    AMDSMI_AVAILABLE = False
    amdsmi = None  # type: ignore

# GPU support flag (NVIDIA, AMD, Apple Metal, or Intel)
# Defined after all individual GPU availability flags are set
GPU_SUPPORTED = False

# Apple Metal GPU support (macOS only)
METAL_AVAILABLE = False
if platform.system() == 'Darwin':
    try:
        import ctypes
        # Basic Metal support check - C bindings exist on macOS
        METAL_AVAILABLE = True
    except ImportError:
        METAL_AVAILABLE = False

# Intel GPU support (Linux only, via sysfs)
INTEL_AVAILABLE = False
if platform.system() == 'Linux':
    try:
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
        if 'Intel' in result.stdout and 'VGA' in result.stdout:
            INTEL_AVAILABLE = True
    except Exception:
        pass

# Final GPU support flag
GPU_SUPPORTED = PYNVML_AVAILABLE or AMDSMI_AVAILABLE or METAL_AVAILABLE or INTEL_AVAILABLE

# ============================================================================
# Internationalization (i18n)
# ============================================================================

TRANSLATIONS = {
    'zh': {
        'title': 'LLAMA.cpp Monitor',
        'cpu_info': 'CPU 信息',
        'gpu_info': 'GPU 信息',
        'model_status': '模型状态',
        'realtime_metrics': '实时指标',
        'active_tasks': '活跃任务',
        'waiting_tasks': '等待任务',
        'system_info': '系统信息',
        'model': '模型',
        'state': '状态',
        'context': '上下文',
        'batch': '批处理',
        'usage': '占用率',
        'freq': '频率',
        'gpu_usage': 'GPU 占用',
        'vram': '显存',
        'temp': '温度',
        'gpu_freq': 'GPU 频率',
        'fan_speed': '风扇',
        'power': '功率',
        'not_available': '不可用',
        'metrics_disabled': '服务端未启用metrics',
        'running': '运行中',
        'queued': '排队中',
        'completed': '已完成',
        'failed': '失败',
        'prefill': '预处理',
        'decode': '解码',
        'waiting': '等待中',
        'tokens_per_sec': 'Token/秒',
        'prompt_eval': '提示词评估',
        'decoding': '解码',
        'cache_hit': '缓存命中率',
        'tasks_active': '活跃',
        'tasks_queued': '排队',
        'tasks_completed': '完成',
        'avg_tps_1m': '平均 TPS(1 分)',
        'avg_tps_5m': '平均 TPS(5 分)',
        'last_update': '最后更新',
        'refresh': '刷新',
        'log_path': '日志路径',
        'language': '语言',
        'detail_mode': '详细模式',
        'quit': '退出',
        'connecting': '正在连接',
        'connected': '已连接',
        'connect_failed': '连接失败',
        'probe_endpoints': '探测端点',
        'manual_input': '手动输入',
        'press_enter': '按回车确认',
        'invalid_url': '无效的 URL',
        'help': '帮助',
        'shortcuts': '快捷键',
        'refresh_now': '手动刷新',
        'show_log': '显示日志路径',
        'toggle_lang': '切换语言',
        'toggle_detail': '切换详细/简洁',
        'quick_quit': '快速退出',
        'exit_graceful': '优雅退出',
        'version': '版本',
        'no_tasks': '无活跃任务',
        'gpu_not_detected': '未检测到 NVIDIA GPU',
        'gpu_init_failed': 'GPU 监控初始化失败',
        'log_rotation': '日志轮转',
        'log_info': '信息',
        'log_warn': '警告',
        'log_error': '错误',
        'log_debug': '调试',
        'task_id': '任务 ID',
        'status': '状态',
        'stage': '阶段',
        'progress': '进度',
        'tps': 'TPS',
        'tokens': 'tokens',
        'avg': '平均',
        'queue_pos': '队位',
        'memory': '内存',
        'mem_usage': '内存占用',
        'cpu_model': '型号',
        'mem_type': '类型',
        'mem_freq': '频率',
        'slots': '插槽',
    },
    'en': {
        'title': 'LLAMA.cpp Monitor',
        'cpu_info': 'CPU Info',
        'gpu_info': 'GPU Info',
        'model_status': 'Model Status',
        'realtime_metrics': 'Real-time Metrics',
        'active_tasks': 'Active Tasks',
        'waiting_tasks': 'Waiting Tasks',
        'system_info': 'System Info',
        'model': 'Model',
        'state': 'State',
        'context': 'Context',
        'batch': 'Batch',
        'usage': 'Usage',
        'freq': 'Freq',
        'gpu_usage': 'GPU Usage',
        'vram': 'VRAM',
        'temp': 'Temp',
        'gpu_freq': 'GPU Freq',
        'fan_speed': 'Fan',
        'power': 'Power',
        'not_available': 'N/A',
        'metrics_disabled': 'Server metrics disabled',
        'running': 'Running',
        'queued': 'Queued',
        'completed': 'Completed',
        'failed': 'Failed',
        'prefill': 'Prefill',
        'decode': 'Decode',
        'waiting': 'Waiting',
        'tokens_per_sec': 'Tokens/s',
        'prompt_eval': 'Prompt Eval',
        'decoding': 'Decoding',
        'cache_hit': 'Cache Hit',
        'tasks_active': 'Active',
        'tasks_queued': 'Queued',
        'tasks_completed': 'Completed',
        'avg_tps_1m': 'Avg TPS (1m)',
        'avg_tps_5m': 'Avg TPS (5m)',
        'last_update': 'Last Update',
        'refresh': 'Refresh',
        'log_path': 'Log Path',
        'language': 'Language',
        'detail_mode': 'Detail Mode',
        'quit': 'Quit',
        'connecting': 'Connecting',
        'connected': 'Connected',
        'connect_failed': 'Connection Failed',
        'probe_endpoints': 'Probe Endpoints',
        'manual_input': 'Manual Input',
        'press_enter': 'Press Enter',
        'invalid_url': 'Invalid URL',
        'help': 'Help',
        'shortcuts': 'Shortcuts',
        'refresh_now': 'Refresh Now',
        'show_log': 'Show Log Path',
        'toggle_lang': 'Toggle Language',
        'toggle_detail': 'Toggle Detail/Simple',
        'quick_quit': 'Quick Quit',
        'exit_graceful': 'Graceful Exit',
        'version': 'Version',
        'no_tasks': 'No Active Tasks',
        'gpu_not_detected': 'No NVIDIA GPU Detected',
        'gpu_init_failed': 'GPU Monitor Init Failed',
        'log_rotation': 'Log Rotation',
        'log_info': 'Info',
        'log_warn': 'Warning',
        'log_debug': 'Debug',
        'task_id': 'Task ID',
        'status': 'Status',
        'stage': 'Stage',
        'progress': 'Progress',
        'tps': 'TPS',
        'tokens': 'tokens',
        'avg': 'Avg',
        'queue_pos': 'Queue',
        'memory': 'Memory',
        'mem_usage': 'Mem Usage',
        'cpu_model': 'Model',
        'mem_type': 'Type',
        'mem_freq': 'Freq',
        'slots': 'Slots',
    }
}


class I18n:
    """Internationalization manager"""
    
    def __init__(self, lang: str = 'zh'):
        self.lang = lang if lang in TRANSLATIONS else 'zh'
    
    def set_language(self, lang: str) -> bool:
        if lang in TRANSLATIONS:
            self.lang = lang
            return True
        return False
    
    def get(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS['en']).get(key, key)
    
    def toggle(self) -> str:
        self.lang = 'en' if self.lang == 'zh' else 'zh'
        return self.lang


# ============================================================================
# Logging System
# ============================================================================

class LogManager:
    """Manages logging with rotation"""
    
    def __init__(self, log_dir: str, max_size: int = 30 * 1024 * 1024, backup_count: int = 5):
        self.log_dir = log_dir
        self.max_size = max_size
        self.backup_count = backup_count
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        os.makedirs(self.log_dir, exist_ok=True)
        
        log_file = os.path.join(self.log_dir, 'monitor.log')
        
        self.logger = logging.getLogger('llama_monitor')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rotating file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(logging.DEBUG)
        
        # Console handler (only for errors)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.addHandler(console_handler)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def get_log_path(self) -> str:
        return os.path.join(self.log_dir, 'monitor.log')


# ============================================================================
# System Information Collector
# ============================================================================

class SystemCollector:
    """Collects system information (CPU, GPU)"""

    def __init__(self):
        self.gpu_available = GPU_SUPPORTED
        self.gpu_initialized = False
        self.gpu_count = 0
        self.gpu_type = None  # 'nvidia' (stable) | 'amd', 'apple', 'intel' (experimental)
        self.logger = logging.getLogger('llama_monitor')

        # CPU usage tracking for instant reading
        self._cpu_usage = 0.0
        self._cpu_usage_lock = threading.Lock()
        self._cpu_stop_event = threading.Event()
        self._cpu_thread = None

        # Start background CPU monitoring thread
        if platform.system() == 'Linux':
            self._start_cpu_thread()

    def _start_cpu_thread(self):
        """Start background thread for instant CPU usage reading via /proc/stat"""
        def cpu_reader():
            # Read initial CPU times
            prev_idle = prev_total = 0
            first_read = True

            while not self._cpu_stop_event.is_set():
                try:
                    with open('/proc/stat', 'r') as f:
                        cpu_line = f.readline()
                    # cpu  user nice system idle iowait irq softirq steal guest guest_nice
                    fields = cpu_line.split()
                    if fields[0] == 'cpu':
                        values = [int(x) for x in fields[1:8]]
                        user, nice, system, idle, iowait, irq, softirq = values
                        idle += iowait
                        total = user + nice + system + idle + irq + softirq

                        if first_read:
                            prev_idle = idle
                            prev_total = total
                            first_read = False
                        else:
                            total_delta = total - prev_total
                            idle_delta = idle - prev_idle
                            if total_delta > 0:
                                with self._cpu_usage_lock:
                                    self._cpu_usage = 100.0 * (1.0 - idle_delta / total_delta)
                            prev_idle = idle
                            prev_total = total
                except Exception as e:
                    self.logger.debug(f"CPU read failed: {e}")

                # Sample every 100ms for responsive but not CPU-intensive monitoring
                self._cpu_stop_event.wait(0.1)

        self._cpu_thread = threading.Thread(target=cpu_reader, daemon=True)
        self._cpu_thread.start()
        self.logger.debug("CPU monitoring thread started")

        if self.gpu_available:
            # Try NVIDIA first
            if PYNVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    self.gpu_count = pynvml.nvmlDeviceGetCount()
                    self.gpu_initialized = True
                    self.gpu_type = 'nvidia'
                    self.logger.info(f"GPU monitoring initialized (NVIDIA): {self.gpu_count} device(s)")
                except Exception as e:
                    self.logger.debug(f"NVIDIA GPU init failed: {e}")

            # Try AMD if NVIDIA failed
            if not self.gpu_initialized and AMDSMI_AVAILABLE:
                try:
                    amdsmi.amdsmi_init()
                    devices = amdsmi.amdsmi_get_processor_handles()
                    if devices:
                        self.gpu_count = len(devices)
                        self.gpu_initialized = True
                        self.gpu_type = 'amd'
                        self.logger.warning(f"GPU monitoring initialized (AMD, experimental): {self.gpu_count} device(s)")
                except Exception as e:
                    self.logger.debug(f"AMD GPU init failed: {e}")

            # Try Apple Metal if NVIDIA and AMD both failed
            if not self.gpu_initialized and METAL_AVAILABLE and platform.system() == 'Darwin':
                try:
                    self.gpu_count = 1
                    self.gpu_initialized = True
                    self.gpu_type = 'apple'
                    self.logger.warning("GPU monitoring initialized (Apple Metal, experimental)")
                except Exception as e:
                    self.logger.debug(f"Apple Metal GPU init failed: {e}")

            # Try Intel GPU if NVIDIA, AMD, Apple Metal all failed
            if not self.gpu_initialized and INTEL_AVAILABLE and platform.system() == 'Linux':
                try:
                    self.gpu_initialized = True
                    self.gpu_type = 'intel'
                    self.gpu_count = 1
                    self.logger.warning("GPU monitoring initialized (Intel, experimental)")
                except Exception as e:
                    self.logger.debug(f"Intel GPU init failed: {e}")

            if not self.gpu_initialized:
                self.gpu_available = False
                self.logger.warning("GPU monitoring unavailable (no NVIDIA GPU detected; AMD/Apple/Intel are experimental)")
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        cpu_info = {
            'model': 'Unknown',
            'usage': 0.0,
            'frequency': 0.0,
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True)
        }
        
        # CPU model
        if platform.system() == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_info['model'] = line.split(':')[1].strip()
                            break
            except Exception as e:
                self.logger.debug(f"CPU model read failed: {e}")
        elif platform.system() == 'Darwin':  # macOS
            try:
                result = os.popen('sysctl -n machdep.cpu.brand_string').read().strip()
                if result:
                    cpu_info['model'] = result
            except Exception as e:
                self.logger.debug(f"CPU model read failed (macOS): {e}")

        # CPU usage - instant read from background thread (Linux /proc/stat)
        # On non-Linux or if thread failed, fall back to psutil
        if platform.system() == 'Linux' and self._cpu_thread is not None:
            with self._cpu_usage_lock:
                cpu_info['usage'] = self._cpu_usage
        else:
            cpu_info['usage'] = psutil.cpu_percent(interval=None)

        # CPU frequency - try multiple methods
        cpu_info['frequency'] = 0.0

        # Method 1: psutil.cpu_freq() - works on most systems
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current > 0:
                cpu_info['frequency'] = freq.current  # MHz
        except Exception as e:
            self.logger.debug(f"CPU freq via psutil unavailable: {e}")

        # Method 2: /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq (Linux)
        if cpu_info['frequency'] <= 0 and platform.system() == 'Linux':
            try:
                import glob
                for path in glob.glob('/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq'):
                    try:
                        with open(path, 'r') as f:
                            # Value is in kHz, convert to MHz
                            val = int(f.read().strip()) / 1000
                            if val > 0:
                                cpu_info['frequency'] = val
                                break
                    except Exception as e:
                        self.logger.debug(f"CPU freq sysfs read error: {e}")
            except Exception as e:
                self.logger.debug(f"CPU freq via sysfs unavailable: {e}")

        # Method 3: /proc/cpuinfo (Linux/macOS)
        if cpu_info['frequency'] <= 0:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'cpu MHz' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                val = parts[1].strip().replace('MHz', '').strip()
                                try:
                                    cpu_info['frequency'] = float(val)
                                    break
                                except ValueError as e:
                                    self.logger.debug(f"CPU freq parse error: {e}")
            except Exception as e:
                self.logger.debug(f"CPU freq via cpuinfo unavailable: {e}")

        return cpu_info

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        mem_info = {
            'total': 0.0,
            'used': 0.0,
            'available': 0.0,
            'percent': 0.0,
            'type': 'Unknown',
            'frequency': 0
        }

        try:
            mem = psutil.virtual_memory()
            mem_info['total'] = mem.total / (1024 ** 3)  # GB
            mem_info['used'] = mem.used / (1024 ** 3)   # GB
            mem_info['available'] = mem.available / (1024 ** 3)  # GB
            mem_info['percent'] = mem.percent
        except Exception as e:
            self.logger.debug(f"Memory info via psutil unavailable: {e}")

        # Try to get memory type and speed from dmidecode
        if platform.system() == 'Linux':
            try:
                import subprocess
                result = subprocess.run(
                    ['dmidecode', '--type', 'memory'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        # Look for memory type
                        if 'Type:' in line and 'Detail' not in line:
                            mem_type = line.split(':')[1].strip()
                            if mem_type and mem_type != 'Unknown':
                                mem_info['type'] = mem_type
                        # Look for speed (frequency)
                        if 'Speed:' in line and 'Detail' not in line:
                            speed_str = line.split(':')[1].strip()
                            # Format: "3600 MT/s" or "Unknown"
                            if 'MT/s' in speed_str:
                                try:
                                    mem_info['frequency'] = int(speed_str.split()[0])
                                except ValueError as e:
                                    self.logger.debug(f"Memory speed parse error: {e}")
                            break  # Only take first memory stick info
            except Exception as e:
                self.logger.debug(f"Memory type/freq via dmidecode unavailable: {e}")

        return mem_info

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information (supports NVIDIA and AMD)"""
        gpu_info = []

        if not self.gpu_available or not self.gpu_initialized:
            return gpu_info

        if self.gpu_type == 'nvidia':
            return self._get_nvidia_gpu_info()
        elif self.gpu_type == 'amd':
            return self._get_amd_gpu_info()
        elif self.gpu_type == 'apple':
            return self._get_apple_gpu_info()
        elif self.gpu_type == 'intel':
            return self._get_intel_gpu_info()

        return gpu_info

    def _get_nvidia_gpu_info(self) -> List[Dict[str, Any]]:
        """Get NVIDIA GPU information"""
        gpu_info = []

        try:
            for i in range(self.gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                gpu_data = {
                    'index': i,
                    'name': pynvml.nvmlDeviceGetName(handle),
                    'type': 'NVIDIA',
                    'utilization': 0,
                    'memory_used': 0,
                    'memory_total': 0,
                    'temperature': 0,
                    'gpu_clock': 0,
                    'mem_clock': 0,
                    'fan_speed': 0,
                    'power': 0
                }

                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_data['utilization'] = util.gpu
                except Exception as e:
                    self.logger.debug(f"GPU utilization unavailable: {e}")

                try:
                    memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_data['memory_used'] = memory.used / (1024 ** 2)  # MB
                    gpu_data['memory_total'] = memory.total / (1024 ** 2)  # MB
                except Exception as e:
                    self.logger.debug(f"GPU memory info unavailable: {e}")

                try:
                    gpu_data['temperature'] = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                except Exception as e:
                    self.logger.debug(f"GPU temperature unavailable: {e}")

                try:
                    gpu_data['gpu_clock'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS) / 1000
                except Exception as e:
                    self.logger.debug(f"GPU clock info unavailable: {e}")

                try:
                    gpu_data['mem_clock'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM) / 1000
                except Exception as e:
                    self.logger.debug(f"GPU mem clock unavailable: {e}")

                try:
                    gpu_data['fan_speed'] = pynvml.nvmlDeviceGetFanSpeed(handle)
                except Exception as e:
                    self.logger.debug(f"GPU fan speed unavailable: {e}")

                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle)
                    gpu_data['power'] = power / 1000  # Convert to Watts
                except Exception as e:
                    self.logger.debug(f"GPU power usage unavailable: {e}")


                gpu_info.append(gpu_data)
        except Exception as e:
            self.logger.warning(f"NVIDIA GPU info collection failed: {e}")

        return gpu_info

    def _get_amd_gpu_info(self) -> List[Dict[str, Any]]:
        """Get AMD GPU information (experimental)"""
        gpu_info = []

        try:
            devices = amdsmi.amdsmi_get_processor_handles()

            for i, device in enumerate(devices):
                try:
                    gpu_data = {
                        'index': i,
                        'name': 'AMD GPU',
                        'type': 'AMD',
                        'utilization': 0,
                        'memory_used': 0,
                        'memory_total': 0,
                        'temperature': 0,
                        'gpu_clock': 0,
                        'mem_clock': 0,
                        'fan_speed': 0,
                        'power': 0
                    }

                    # Get name
                    try:
                        name = amdsmi.amdsmi_get_gpu_device_name(device)
                        if name:
                            gpu_data['name'] = name
                    except Exception as e:
                        self.logger.debug(f"AMD GPU name unavailable: {e}")

                    # Get utilization
                    try:
                        util = amdsmi.amdsmi_get_gpu_utilization(device)
                        if util:
                            gpu_data['utilization'] = util.get('gpu_utilization', 0)
                    except Exception as e:
                        self.logger.debug(f"AMD GPU utilization unavailable: {e}")

                    # Get VRAM usage
                    try:
                        mem = amdsmi.amdsmi_get_gpu_memory_usage(device)
                        if mem:
                            gpu_data['memory_used'] = mem.get('vram_used', 0) / (1024 ** 2)  # bytes to MB
                            gpu_data['memory_total'] = mem.get('vram_total', 0) / (1024 ** 2)
                    except Exception as e:
                        self.logger.debug(f"AMD GPU memory info unavailable: {e}")


                    # Get temperature
                    try:
                        temp = amdsmi.amdsmi_get_gpu_temperature(device)
                        if temp:
                            gpu_data['temperature'] = temp.get('temperature', 0)
                    except Exception as e:
                        self.logger.debug(f"AMD GPU temperature unavailable: {e}")

                    # Get clock frequencies
                    try:
                        clocks = amdsmi.amdsmi_get_gpu_clk_freq(device)
                        if clocks:
                            gpu_data['gpu_clock'] = clocks.get('sclk', 0) / 1000  # MHz to GHz
                            gpu_data['mem_clock'] = clocks.get('mclk', 0) / 1000
                    except Exception as e:
                        self.logger.debug(f"AMD GPU clock info unavailable: {e}")

                    # Get fan speed
                    try:
                        fan = amdsmi.amdsmi_get_gpu_fan_speed(device)
                        if fan:
                            gpu_data['fan_speed'] = fan.get('fan_speed', 0)
                    except Exception as e:
                        self.logger.debug(f"AMD GPU fan speed unavailable: {e}")

                    # Get power consumption
                    try:
                        power = amdsmi.amdsmi_get_gpu_power(device)
                        if power:
                            gpu_data['power'] = power.get('power', 0) / 1000  # mW to W
                    except Exception as e:
                        self.logger.debug(f"AMD GPU power usage unavailable: {e}")

                    gpu_info.append(gpu_data)

                except Exception as e:
                    self.logger.debug(f"AMD GPU {i} info failed: {e}")

        except Exception as e:
            self.logger.warning(f"AMD GPU info collection failed: {e}")

        return gpu_info

    def _get_intel_gpu_info(self) -> List[Dict[str, Any]]:
        """Get Intel GPU information via sysfs and lspci"""
        gpu_info = []
        gpu_data = {
            'index': 0,
            'name': 'Intel GPU',
            'type': 'Intel',
            'utilization': 0,
            'memory_used': 0,
            'memory_total': 0,
            'temperature': 0,
            'gpu_clock': 0,
            'mem_clock': 0,
            'fan_speed': 0,
            'power': 0
        }

        # Get GPU name from lspci
        try:
            result = subprocess.run(
                ['lspci', '-mm', '-n'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if '0300' in line and 'Intel' in line:
                    name_result = subprocess.run(
                        ['lspci', '-mm', '-n', '-nn'],
                        capture_output=True, text=True, timeout=5
                    )
                    for nline in name_result.stdout.split('\n'):
                        if 'VGA' in nline and 'Intel' in nline:
                            try:
                                gpu_data['name'] = nline.split('"')[1] if '"' in nline else 'Intel GPU'
                            except Exception:
                                pass
                    break
        except Exception as e:
            self.logger.debug(f"Intel GPU name unavailable: {e}")

        # Read utilization from sysfs
        try:
            for card in ['card0', 'card1', 'card2']:
                busy_path = f'/sys/class/drm/{card}/device/gpu_busy_percent'
                if os.path.exists(busy_path):
                    with open(busy_path, 'r') as f:
                        gpu_data['utilization'] = float(f.read().strip())
                    break
        except Exception as e:
            self.logger.debug(f"Intel GPU utilization unavailable: {e}")

        # Read memory info from sysfs
        try:
            for card in ['card0', 'card1', 'card2']:
                mem_path = f'/sys/class/drm/{card}/device/mem_info_vram_total'
                if os.path.exists(mem_path):
                    with open(mem_path, 'r') as f:
                        gpu_data['memory_total'] = int(f.read().strip()) / (1024 * 1024)  # bytes to MB
                    used_path = f'/sys/class/drm/{card}/device/mem_info_vram_used'
                    if os.path.exists(used_path):
                        with open(used_path, 'r') as f:
                            gpu_data['memory_used'] = int(f.read().strip()) / (1024 * 1024)
                    break
        except Exception as e:
            self.logger.debug(f"Intel GPU memory info unavailable: {e}")

        # Read GPU clock from sysfs
        try:
            for card in ['card0', 'card1', 'card2']:
                paths = [
                    f'/sys/class/drm/{card}/device/gt_cur_freq_mhz',
                    f'/sys/class/drm/{card}/device/gt_max_freq_mhz',
                ]
                for fp in paths:
                    if os.path.exists(fp):
                        with open(fp, 'r') as f:
                            mhz = int(f.read().strip())
                            gpu_data['gpu_clock'] = mhz / 1000  # MHz to GHz
                        break
        except Exception as e:
            self.logger.debug(f"Intel GPU clock unavailable: {e}")

        gpu_info.append(gpu_data)
        return gpu_info

    def _get_apple_gpu_info(self) -> List[Dict[str, Any]]:
        """Get Apple GPU information via system_profiler and powermetrics"""
        gpu_info = []
        gpu_data = {
            'index': 0,
            'name': 'Apple GPU',
            'type': 'Apple',
            'utilization': 0,
            'memory_used': 0,
            'memory_total': 0,
            'temperature': 0,
            'gpu_clock': 0,
            'mem_clock': 0,
            'fan_speed': 0,
            'power': 0
        }

        # Get GPU name from system_profiler
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType', '-json'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if 'SPDisplaysDataType' in data and len(data['SPDisplaysDataType']) > 0:
                    display = data['SPDisplaysDataType'][0]
                    gpu_data['name'] = display.get('sppci_model', 'Apple GPU')
        except Exception as e:
            self.logger.debug(f"Apple GPU name unavailable: {e}")

        # Get GPU utilization from powermetrics (requires sudo, fallback gracefully)
        try:
            result = subprocess.run(
                ['sudo', 'powermetrics', '--samplers', 'gpu', '-i', '1000', '-n', '1'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout
                # Parse gpu_active (activity percentage)
                for line in output.split('\n'):
                    if 'gpu_active' in line.lower():
                        try:
                            val = float(''.join(filter(lambda x: x.isdigit() or x == '.', line.split('gpu_active')[-1])))
                            gpu_data['utilization'] = min(val, 100)
                        except:
                            pass
        except Exception as e:
            self.logger.debug(f"Apple GPU utilization unavailable: {e}")

        # Get memory info from memory_pressure if available
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                total_mem = int(result.stdout.strip())
                gpu_data['memory_total'] = total_mem / (1024 ** 2)  # MB
                # Apple shares system memory, approximate VRAM as 1/4 of system RAM for dGPU
                if 'Apple' not in gpu_data['name'] and 'M' in gpu_data['name']:
                    gpu_data['memory_total'] = min(gpu_data['memory_total'], 16384)
        except Exception as e:
            self.logger.debug(f"Apple GPU memory info unavailable: {e}")

        gpu_info.append(gpu_data)
        return gpu_info

    def cleanup(self):
        """Cleanup GPU resources"""
        if self.gpu_initialized:
            try:
                if self.gpu_type == 'nvidia':
                    pynvml.nvmlShutdown()
                elif self.gpu_type == 'amd':
                    amdsmi.amdsmi_shut_down()
            except Exception as e:
                self.logger.debug(f"GPU cleanup error: {e}")

        # Stop CPU monitoring thread
        if self._cpu_thread is not None:
            self._cpu_stop_event.set()
            self._cpu_thread.join(timeout=1.0)


# ============================================================================
# LLAMA Server API Client
# ============================================================================

class LLAMAServerClient:
    """Client for llama-server API"""
    
    COMMON_ENDPOINTS = [
        '/metrics',
        '/props',
        '/health',
        '/v1/models',
        '/v1/chat/completions',
        '/slots',
        '/info',
        '/version'
    ]
    
    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger('llama_monitor')
        self.available_endpoints = {}
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'LLAMA-Monitor/1.0'
        })
    
    def test_connection(self) -> bool:
        """Test basic connection"""
        try:
            resp = self.session.get(self.base_url, timeout=self.timeout)
            return resp.status_code < 500
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
    
    def probe_endpoints(self) -> Dict[str, Any]:
        """Probe common endpoints"""
        self.available_endpoints = {}
        
        for endpoint in self.COMMON_ENDPOINTS:
            try:
                url = f"{self.base_url}{endpoint}"
                resp = self.session.get(url, timeout=0.5)
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        self.available_endpoints[endpoint] = data
                        self.logger.debug(f"Endpoint available: {endpoint}")
                    except json.JSONDecodeError:
                        # Might still be useful (e.g., Prometheus metrics)
                        self.available_endpoints[endpoint] = {'raw': resp.text}
            except Exception as e:
                self.logger.debug(f"Endpoint {endpoint} not available: {e}")
                continue
        
        return self.available_endpoints
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        # First try /props endpoint (llama-server specific)
        if '/props' in self.available_endpoints:
            data = self.available_endpoints['/props']
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    pass
            
            if isinstance(data, dict):
                model_info = {}
                if 'model_path' in data:
                    model_info['name'] = data['model_path'].split('/')[-1]
                    self.logger.debug(f"/props model_path: {data['model_path']}")
                elif 'model_alias' in data:
                    model_info['name'] = data['model_alias'].split('/')[-1]
                    self.logger.debug(f"/props model_alias: {data['model_alias']}")
                elif 'model' in data:
                    model_info['name'] = data['model']
                    self.logger.debug(f"/props model: {data['model']}")
                
                # n_ctx can be in different locations
                if 'n_ctx' in data:
                    model_info['context'] = data['n_ctx']
                elif 'default_generation_settings' in data:
                    dgs = data['default_generation_settings']
                    if 'n_ctx' in dgs:
                        model_info['context'] = dgs['n_ctx']
                    elif 'params' in dgs and 'n_ctx' in dgs['params']:
                        model_info['context'] = dgs['params']['n_ctx']
                
                if 'n_batch' in data:
                    model_info['batch'] = data['n_batch']
                if 'n_gpu_layers' in data:
                    model_info['gpu_layers'] = data['n_gpu_layers']
                model_info['state'] = 'Running'
                
                if model_info.get('name'):
                    self.logger.debug(f"Model info from /props: {model_info}")
                    return model_info
        
        # Try /v1/models endpoint (OpenAI compatible)
        if '/v1/models' in self.available_endpoints:
            data = self.available_endpoints['/v1/models']
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    pass
            
            self.logger.debug(f"/v1/models data type: {type(data)}, keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
            
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                first_model = data['data'][0]
                model_info = {}
                model_info['name'] = first_model.get('id', first_model.get('name', 'Unknown'))
                if 'meta' in first_model:
                    meta = first_model['meta']
                    if 'n_ctx_train' in meta:
                        model_info['context'] = meta['n_ctx_train']
                    if 'n_params' in meta:
                        model_info['params'] = meta['n_params']
                model_info['state'] = 'Running'
                self.logger.debug(f"Model info from /v1/models: {model_info}")
                return model_info
            elif isinstance(data, dict):
                self.logger.debug(f"/v1/models available keys: {list(data.keys())}")
        
        # Try /models endpoint
        if '/models' in self.available_endpoints:
            data = self.available_endpoints['/models']
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    pass
            
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                first_model = data['data'][0]
                model_info = {}
                model_info['name'] = first_model.get('id', first_model.get('name', 'Unknown'))
                if 'meta' in first_model:
                    meta = first_model['meta']
                    if 'n_ctx_train' in meta:
                        model_info['context'] = meta['n_ctx_train']
                    if 'n_params' in meta:
                        model_info['params'] = meta['n_params']
                model_info['state'] = 'Running'
                return model_info
        
        # Fallback to other endpoints
        for endpoint in ['/stats', '/health', '/info']:
            if endpoint in self.available_endpoints:
                data = self.available_endpoints[endpoint]
                model_info = {}
                
                if isinstance(data, dict) and 'raw' in data:
                    try:
                        data = json.loads(data['raw'])
                    except json.JSONDecodeError:
                        continue
                
                if isinstance(data, dict):
                    if 'model' in data:
                        model_info['name'] = data['model']
                    if 'model_path' in data:
                        model_info['name'] = data['model_path']
                    if 'n_ctx' in data:
                        model_info['context'] = data['n_ctx']
                    if 'n_batch' in data:
                        model_info['batch'] = data['n_batch']
                    if 'state' in data:
                        model_info['state'] = data['state']
                    if 'loaded' in data:
                        model_info['state'] = 'Running' if data['loaded'] else 'Not loaded'
                    
                    if model_info.get('name'):
                        return model_info
        
        return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics"""
        # First try cached endpoints
        for endpoint in ['/stats', '/v1/stats']:
            if endpoint in self.available_endpoints:
                data = self.available_endpoints[endpoint]
                # Handle raw text format
                if isinstance(data, dict) and 'raw' in data:
                    try:
                        data = json.loads(data['raw'])
                    except json.JSONDecodeError:
                        continue
                if isinstance(data, dict):
                    self.logger.debug(f"Got stats from {endpoint}")
                    return data

        # Try to parse Prometheus metrics from cache
        if '/metrics' in self.available_endpoints:
            data = self.available_endpoints['/metrics']
            if isinstance(data, str):
                stats = self._parse_prometheus_metrics(data)
                if stats:
                    self.logger.debug("Got stats from /metrics (cached string)")
                    return stats
            elif isinstance(data, dict) and 'raw' in data:
                stats = self._parse_prometheus_metrics(data['raw'])
                if stats:
                    self.logger.debug("Got stats from /metrics (cached dict)")
                    return stats

        # Fallback: directly query /metrics endpoint for fresh data
        try:
            resp = self.session.get(f"{self.base_url}/metrics", timeout=0.5)
            if resp.status_code == 200:
                stats = self._parse_prometheus_metrics(resp.text)
                if stats:
                    self.logger.debug("Got fresh stats from /metrics direct query")
                    return stats
        except Exception as e:
            self.logger.debug(f"Direct /metrics query failed: {e}")

        return {}
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get task/queue information"""
        tasks = []
        
        # Try to get from /queue endpoint
        if '/queue' in self.available_endpoints:
            data = self.available_endpoints['/queue']
            # Handle raw text
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    data = None
            if isinstance(data, list):
                tasks.extend(self._parse_task_list(data))
        
        # Try to get from /stats
        if '/stats' in self.available_endpoints:
            data = self.available_endpoints['/stats']
            # Handle raw text
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    data = None
            if isinstance(data, dict):
                tasks.extend(self._parse_stats_tasks(data))
        
        # Try /v1/queue for newer versions
        if '/v1/queue' in self.available_endpoints:
            data = self.available_endpoints['/v1/queue']
            # Handle raw text
            if isinstance(data, dict) and 'raw' in data:
                try:
                    data = json.loads(data['raw'])
                except json.JSONDecodeError:
                    data = None
            if isinstance(data, list):
                tasks.extend(self._parse_task_list(data))
        
        # If no tasks from queue, try to create fake tasks from metrics
        if not tasks and '/metrics' in self.available_endpoints:
            data = self.available_endpoints['/metrics']
            metrics_text = None
            if isinstance(data, str):
                metrics_text = data
            elif isinstance(data, dict) and 'raw' in data:
                metrics_text = data['raw']
            
            if metrics_text:
                stats = self._parse_prometheus_metrics(metrics_text)
                if stats.get('running_requests', 0) > 0:
                    tasks.extend(self._create_tasks_from_stats(stats))
        
        return tasks
    
    def _parse_task_list(self, data: List) -> List[Dict[str, Any]]:
        """Parse task list from queue endpoint"""
        tasks = []
        for i, task in enumerate(data):
            task_info = {
                'id': task.get('id', i),
                'status': 'running' if task.get('running') else 'queued',
                'stage': self._detect_stage(task),
                'progress': task.get('progress', 0),
                'tokens_generated': task.get('tokens_generated', 0),
                'tokens_total': task.get('tokens_total', 0),
                'tps': task.get('tps', 0),
                'queue_position': task.get('queue_position', i + 1)
            }
            tasks.append(task_info)
        return tasks
    
    def _parse_stats_tasks(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse task info from stats endpoint"""
        tasks = []
        
        # Common llama-server stats fields
        if 'running_requests' in data:
            count = data['running_requests']
            if count > 0:
                for i in range(count):
                    tasks.append({
                        'id': i + 1,
                        'status': 'running',
                        'stage': 'decode',  # Assume decode for running
                        'tokens_generated': data.get('eval_count', 0),
                        'tps': data.get('tokens_per_second', 0)
                    })
        
        return tasks
    
    def _parse_metrics_tasks(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse task info from metrics endpoint"""
        tasks = []
        
        # This is a fallback - real metrics parsing depends on format
        if 'running_tasks' in data:
            count = data['running_tasks']
            if count > 0:
                tps = data.get('avg_tokens_per_second', 0)
                for i in range(count):
                    tasks.append({
                        'id': i + 1,
                        'status': 'running',
                        'stage': 'decode',
                        'tps': tps
                    })
        
        return tasks
    
    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse Prometheus format metrics"""
        stats = {}
        
        try:
            for line in metrics_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse metric: metric_name{labels} value or metric_name value
                if '{' in line:
                    parts = line.split('{', 1)
                    if len(parts) >= 2:
                        metric_name = parts[0].strip()
                        rest = parts[1].split('}', 1)
                        if len(rest) >= 2:
                            value_str = rest[1].strip()
                            try:
                                value = float(value_str)
                            except ValueError:
                                continue
                            self._map_metric(metric_name, value, stats)
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        try:
                            value = float(parts[1])
                        except ValueError:
                            continue
                        self._map_metric(metric_name, value, stats)
                        
        except Exception as e:
            self.logger.debug(f"Error parsing Prometheus metrics: {e}")
        
        # Calculate derived metrics
        if 'eval_count' in stats and 'total_decode_time' in stats:
            if stats['total_decode_time'] > 0:
                stats['eval_per_second'] = stats['eval_count'] / stats['total_decode_time']
        
        if 'prompt_eval_count' in stats and 'total_prompt_time' in stats:
            if stats['total_prompt_time'] > 0:
                stats['prompt_eval_per_second'] = stats['prompt_eval_count'] / stats['total_prompt_time']
        
        return stats
    
    def _map_metric(self, metric_name: str, value: float, stats: Dict):
        """Map metric name to internal stats"""
        # llamacpp: format (newer llama-server)
        if metric_name == 'llamacpp:requests_processing':
            stats['running_requests'] = int(value)
        elif metric_name == 'llamacpp:predicted_tokens_seconds':
            stats['tokens_per_second'] = value
            stats['eval_per_second'] = value
        elif metric_name == 'llamacpp:prompt_tokens_seconds':
            stats['prompt_eval_per_second'] = value
        elif metric_name == 'llamacpp:tokens_predicted_total':
            stats['eval_count'] = int(value)
        elif metric_name == 'llamacpp:prompt_tokens_total':
            stats['prompt_eval_count'] = int(value)
        elif metric_name == 'llamacpp:tokens_predicted_seconds_total':
            stats['total_decode_time'] = value
        elif metric_name == 'llamacpp:prompt_seconds_total':
            stats['total_prompt_time'] = value
        elif metric_name == 'llamacpp:n_busy_slots_per_decode':
            stats['avg_busy_slots'] = value
        
        # llama_* format (older/different llama-server)
        elif metric_name == 'llama_request_eval_count_sum':
            stats['eval_count'] = int(value)
        elif metric_name == 'llama_request_prompt_eval_count_sum':
            stats['prompt_eval_count'] = int(value)
        elif metric_name == 'llama_request_counter':
            stats['total_requests'] = int(value)
        elif metric_name == 'llama_processing_running':
            stats['running_requests'] = int(value)
        elif metric_name == 'llama_token_decode_seconds_sum':
            stats['total_decode_time'] = value
        elif metric_name == 'llama_token_prompt_eval_seconds_sum':
            stats['total_prompt_time'] = value
        elif metric_name == 'llama_context_hit_ratio':
            stats['cache_hit_rate'] = value * 100
        elif metric_name == 'llama_token_per_second_decode':
            stats['tokens_per_second'] = value
            stats['eval_per_second'] = value
        elif metric_name == 'llama_token_per_second_prompt_eval':
            stats['prompt_eval_per_second'] = value
    
    def _create_tasks_from_stats(self, stats: Dict) -> List[Dict[str, Any]]:
        """Create fake task list from stats"""
        tasks = []
        running = stats.get('running_requests', 0)
        
        if running > 0:
            tps = stats.get('tokens_per_second', stats.get('eval_per_second', 0))
            for i in range(running):
                tasks.append({
                    'id': i + 1,
                    'status': 'running',
                    'stage': 'decode',
                    'tokens_generated': stats.get('eval_count', 0) // max(running, 1),
                    'tps': tps / max(running, 1)
                })
        
        return tasks
    
    def _detect_stage(self, task: Dict) -> str:
        """Detect task stage (prefill vs decode)"""
        prompt_eval = task.get('prompt_eval_count', 0)
        total_prompt = task.get('total_prompt_tokens', 0)
        tokens_total = task.get('tokens_total', 0)
        eval_count = task.get('eval_count', 0)
        tokens_generated = task.get('tokens_generated', 0)
        progress = task.get('progress', 0)

        # Use tokens_total as fallback for total_prompt
        if total_prompt <= 0:
            total_prompt = tokens_total

        # Prefill stage: still processing prompt tokens
        if total_prompt > 0 and prompt_eval < total_prompt:
            return 'prefill'
        # Decode stage: has generated tokens or eval count
        elif eval_count > 0 or tokens_generated > 0 or progress > 0:
            return 'decode'
        else:
            return 'waiting'
    
    def get_tps_history(self, data: Dict) -> List[float]:
        """Extract TPS history for chart"""
        # Try to get historical data
        if 'tokens_per_second_history' in data:
            return data['tokens_per_second_history'][-30:]
        elif 'eval_rate_history' in data:
            return data['eval_rate_history'][-30:]
        return []
    
    def update_data(self):
        """Refresh data from server - probe endpoints"""
        self.probe_endpoints()

    def get_fresh_stats(self, prev_prompt_count: int = 0, prev_eval_count: int = 0,
                        prev_time: float = 0) -> Tuple[Dict[str, Any], int, int, float]:
        """Get fresh stats directly from /metrics endpoint.
        Returns (stats, current_prompt_count, current_eval_count, current_time)
        """
        stats = {}
        current_prompt_count = 0
        current_eval_count = 0
        current_time = time.time()

        try:
            resp = self.session.get(f"{self.base_url}/metrics", timeout=0.5)
            if resp.status_code == 200:
                raw_stats = self._parse_prometheus_metrics(resp.text)
                if raw_stats:
                    prompt_count = raw_stats.get('prompt_eval_count', 0)
                    eval_count = raw_stats.get('eval_count', 0)
                    running_requests = raw_stats.get('running_requests', 0)

                    current_prompt_count = prompt_count
                    current_eval_count = eval_count

                    # Calculate deltas for phase detection
                    time_delta = current_time - prev_time if prev_time > 0 else 0
                    prompt_delta = prompt_count - prev_prompt_count if prev_prompt_count > 0 else 0
                    eval_delta = eval_count - prev_eval_count if prev_eval_count > 0 else 0

                    # Determine current phase
                    # prefill: prompt being processed, no eval tokens yet
                    # decode: eval tokens are being generated
                    phase = 'waiting'
                    if running_requests > 0:
                        if eval_count == 0:
                            phase = 'prefill'
                        else:
                            phase = 'decode'

                    # If no running requests, TPS should be 0
                    if running_requests == 0:
                        stats['tokens_per_second'] = 0
                        stats['eval_per_second'] = 0
                        stats['prompt_eval_per_second'] = 0
                    else:
                        # Use server-reported rates as base
                        server_tps = raw_stats.get('tokens_per_second', 0)
                        server_prompt_tps = raw_stats.get('prompt_eval_per_second', 0)

                        # If we detected new tokens, calculate instantaneous rate
                        if time_delta > 0:
                            if prompt_delta > 0:
                                stats['prompt_eval_per_second'] = prompt_delta / time_delta
                            else:
                                stats['prompt_eval_per_second'] = server_prompt_tps

                            if eval_delta > 0:
                                stats['tokens_per_second'] = eval_delta / time_delta
                                stats['eval_per_second'] = eval_delta / time_delta
                            else:
                                stats['tokens_per_second'] = server_tps
                                stats['eval_per_second'] = server_tps
                        else:
                            # First call or no time delta, use server values
                            stats['tokens_per_second'] = server_tps
                            stats['eval_per_second'] = server_tps
                            stats['prompt_eval_per_second'] = server_prompt_tps

                    # Include other stats
                    stats['running_requests'] = running_requests
                    stats['cache_hit_rate'] = raw_stats.get('cache_hit_rate', 0)
                    stats['prompt_eval_count'] = prompt_count
                    stats['eval_count'] = eval_count
                    stats['eval_delta'] = eval_delta
                    stats['prompt_delta'] = prompt_delta
                    stats['phase'] = phase

                    self.logger.debug(f"Stats: tps={stats['tokens_per_second']:.1f}, running={stats['running_requests']}, phase={phase}")
        except Exception as e:
            self.logger.debug(f"Fresh stats query failed: {e}")

        return stats, current_prompt_count, current_eval_count, current_time

    def get_slots(self) -> List[Dict[str, Any]]:
        """Get slot information from /slots endpoint"""
        slots = []
        try:
            resp = self.session.get(f"{self.base_url}/slots", timeout=0.5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for slot in data:
                        # Only include slots with valid task IDs (not empty/idle slots)
                        task_id = slot.get('id_task', -1)
                        is_processing = slot.get('is_processing', False)

                        slot_info = {
                            'slot_id': slot.get('id', 0),
                            'task_id': task_id,
                            'is_processing': is_processing,
                            'n_decoded': 0,
                            'n_remain': 0,
                            'prompt_count': 0,
                            'tps': 0.0
                        }
                        # Get token info from next_token array
                        next_token = slot.get('next_token', [])
                        if isinstance(next_token, list) and len(next_token) > 0:
                            slot_info['n_decoded'] = next_token[0].get('n_decoded', 0)
                            slot_info['n_remain'] = next_token[0].get('n_remain', 0)
                        # Get prompt tokens from common_token_ids
                        if 'common_token_ids' in slot:
                            slot_info['prompt_count'] = len(slot.get('common_token_ids', []))
                        # Only add slots that are processing or have valid task
                        if is_processing or task_id > 0:
                            slots.append(slot_info)
                self.logger.debug(f"Got slots: {len(slots)} active slots")
        except Exception as e:
            self.logger.debug(f"Slots query failed: {e}")
        return slots

    def get_fresh_tasks(self, prev_prompt_count: int = 0, prev_eval_count: int = 0) -> Tuple[List[Dict[str, Any]], int, int]:
        """Get fresh tasks from /slots endpoint with per-task details.
        Returns (tasks, current_prompt_count, current_eval_count) for delta tracking.
        Tasks are organized as a tree structure grouped by task_id (job_id).
        """
        tasks = []
        current_prompt_count = 0
        current_eval_count = 0

        # First try to get real tasks from /slots endpoint
        slots = self.get_slots()

        # Also query /metrics for stage detection (prefill vs decode)
        prompt_eval_count = 0
        eval_count = 0
        running_requests = 0
        try:
            resp = self.session.get(f"{self.base_url}/metrics", timeout=0.5)
            if resp.status_code == 200:
                metrics = self._parse_prometheus_metrics(resp.text)
                if metrics:
                    prompt_eval_count = metrics.get('prompt_eval_count', 0)
                    eval_count = metrics.get('eval_count', 0)
                    running_requests = metrics.get('running_requests', 0)
        except Exception as e:
            self.logger.debug(f"Fresh tasks metrics query failed: {e}")


        # Determine global stage: prefill if prompt being processed but no output yet
        global_stage = 'decode'
        if running_requests > 0 and eval_count == 0 and prompt_eval_count > 0:
            global_stage = 'prefill'

        if slots:
            # Only show slots that are actually processing (is_processing=True)
            # These are real-time active tasks, not completed slots
            active_slots = [s for s in slots if s.get('is_processing')]

            for slot in active_slots:
                n_decoded = slot.get('n_decoded', 0)
                n_remain = slot.get('n_remain', 0)
                prompt_count = slot.get('prompt_count', 0)

                # Detect stage: if n_decoded == 0, definitely prefill
                if n_decoded == 0:
                    stage = 'prefill'
                else:
                    stage = global_stage

                # Calculate progress percentage if we have remain info
                progress = 0
                total = n_decoded + n_remain
                if total > 0:
                    progress = int(n_decoded / total * 100)

                # TPS will be calculated after we get stats
                task_info = {
                    'id': slot.get('slot_id', 0),
                    'task_id': slot.get('task_id', 0),
                    'status': 'running',
                    'stage': stage,
                    'tokens_generated': n_decoded,
                    'tokens_remain': n_remain,
                    'prompt_tokens': prompt_count,
                    'progress': progress,
                    'tps': 0.0,
                    'prompt_tps': 0.0
                }
                tasks.append(task_info)

            # Sum up total tokens from slots for stats tracking
            current_eval_count = sum(s.get('n_decoded', 0) for s in slots)
            current_prompt_count = sum(s.get('prompt_count', 0) for s in slots)

            self.logger.debug(f"Got {len(tasks)} tasks from slots, total decoded={current_eval_count}")

        # Fallback to /metrics if no slots data
        if not tasks:
            try:
                resp = self.session.get(f"{self.base_url}/metrics", timeout=0.5)
                if resp.status_code == 200:
                    stats = self._parse_prometheus_metrics(resp.text)
                    if stats:
                        running = stats.get('running_requests', 0)
                        tps = stats.get('tokens_per_second', 0)
                        prompt_tps = stats.get('prompt_eval_per_second', 0)
                        eval_count = stats.get('eval_count', 0)
                        prompt_count = stats.get('prompt_eval_count', 0)

                        current_prompt_count = prompt_count
                        current_eval_count = eval_count

                        # Calculate deltas to detect actual current phase
                        prompt_delta = prompt_count - prev_prompt_count if prev_prompt_count > 0 else 0
                        eval_delta = eval_count - prev_eval_count if prev_eval_count > 0 else 0

                        self.logger.debug(f"Stage: running={running}, prompt_delta={prompt_delta}, eval_delta={eval_delta}")

                        # Determine stage: prefill if prompt still being processed, decode if generating tokens
                        if running > 0:
                            # prefill: prompt being processed, no eval tokens yet
                            # decode: eval tokens are being generated
                            if eval_count == 0:
                                stage = 'prefill'
                            else:
                                stage = 'decode'

                            task_info = {
                                'id': 1,
                                'status': 'running',
                                'stage': stage,
                                'tokens_generated': eval_count,
                                'tokens_delta': eval_delta,
                                'prompt_tokens': prompt_count,
                                'prompt_delta': prompt_delta,
                                'tps': tps,
                                'prompt_tps': prompt_tps
                            }
                            tasks.append(task_info)
                        elif tps > 0 or eval_delta > 0:
                            # Request just completed, show completion
                            tasks.append({
                                'id': 1,
                                'status': 'completed',
                                'stage': '-',
                                'tokens_generated': eval_count,
                                'prompt_tokens': prompt_count,
                                'tps': tps,
                                'prompt_tps': 0
                            })

                        self.logger.debug(f"Got fresh tasks from metrics: {len(tasks)} tasks, stage={tasks[0].get('stage') if tasks else 'none'}")
            except Exception as e:
                self.logger.debug(f"Fresh tasks query failed: {e}")

        return tasks, current_prompt_count, current_eval_count

    def close(self):
        """Close session"""
        self.session.close()


# ============================================================================
# TUI Interface (curses-based)
# ============================================================================

class TTUInterface:
    """Terminal User Interface using curses"""
    
    # Color pairs
    COLOR_HEADER = 1
    COLOR_CPU = 2
    COLOR_GPU = 3
    COLOR_MODEL = 4
    COLOR_METRICS = 5
    COLOR_TASK = 6
    COLOR_BAR_FILLED = 7
    COLOR_BAR_EMPTY = 8
    COLOR_PREFILL = 9
    COLOR_DECODE = 10
    COLOR_QUEUED = 11
    COLOR_SUCCESS = 12
    COLOR_WARNING = 13
    COLOR_ERROR = 14
    COLOR_TPS_HIGH = 15
    COLOR_TPS_MED = 16
    COLOR_TPS_LOW = 17
    
    def __init__(self, stdscr, i18n: I18n, log_manager: LogManager):
        self.stdscr = stdscr
        self.i18n = i18n
        self.log_manager = log_manager
        self.logger = logging.getLogger('llama_monitor')

        self.running = True
        self.detail_mode = True
        self.last_update = None
        self.server_url = ''
        self.refresh_interval = 1.0  # Default 1000ms

        # Data containers
        self.cpu_info = {}
        self.memory_info = {}
        self.gpu_info = []
        self.model_info = None
        self.stats = None
        self.tasks = []
        self.tps_history = deque(maxlen=60)  # 60 data points for longer history

        # Usage history for line charts - more points for smoother graphs
        self.cpu_usage_history = deque(maxlen=60)
        self.memory_usage_history = deque(maxlen=60)
        # Per-GPU history
        self.gpu_usage_history = []  # List of deques, one per GPU
        self.gpu_mem_usage_history = []  # List of deques, one per GPU

        # Error tracking for stability monitoring
        self.api_errors = 0
        self.api_consecutive_failures = 0
        self.system_errors = 0
        self.last_successful_api = None
        self.last_successful_system = None

        # Endpoint refresh counter
        self.endpoint_refresh_counter = 0
        self.endpoint_refresh_interval = 30  # Re-probe endpoints every 30 refresh cycles

        # Previous metrics for delta calculation
        self._prev_prompt_count = 0
        self._prev_eval_count = 0
        self._prev_stats_time = 0

        # Per-slot TPS tracking: {slot_id: (prev_n_decoded, prev_time)}
        self._slot_tps_tracker = {}

        # Phase 2: Stage icons for status display
        self.STAGE_ICONS = {
            'prefill':  '▶',
            'decode':   '●',
            'waiting':  '○',
            'queued':   '○',
            'running':  '●',
            'completed':'✓',
            'failed':   '✗',
        }

        # Phase 2: Pulse animation flag
        self._pulse_active = False

        # UI style: 'default' or 'btop'
        self.ui_style = os.environ.get('LLAMA_MONITOR_UI', 'default')

        # Initialize curses
        self._init_curses()
    
    def _draw_mini_graph(self, values: List[float], width: int = 20) -> str:
        """Draw a mini line graph using block characters.
        Similar to btop's mini graphs.
        """
        if not values:
            return ' ' * width
        data = list(values)[-width:]
        if len(data) < 2:
            return ' ' * width
        max_val = max(data) if max(data) > 0 else 1
        bars = ''
        for v in data:
            ratio = v / max_val
            if ratio > 0.75:
                bars += '█'
            elif ratio > 0.5:
                bars += '▄'
            elif ratio > 0.25:
                bars += '▀'
            else:
                bars += '░'
        return bars

    def _draw_btop_ui(self):
        """Draw btop-style TUI layout.
        More compact, higher information density with mini graphs.
        """
        try:
            height, width = self.stdscr.getmaxyx()
            self.stdscr.erase()

            # Color pairs for btop mode
            CP = curses.color_pair
            C_GREEN = CP(2)   # CPU
            C_CYAN = CP(19)   # Mem
            C_MAGENTA = CP(20) # GPU
            C_YELLOW = CP(21)  # Metrics
            C_WHITE = CP(1)    # Default

            def color_for(percent: float) -> int:
                """Get color based on usage percentage."""
                if percent < 60:
                    return 2  # Green
                elif percent < 85:
                    return 13  # Yellow
                else:
                    return 14  # Red

            # ── Title bar ─────────────────────────────────────────────
            hostname = socket.gethostname()
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_str = self._format_uptime(uptime_seconds)
            model_name = (self.model_info.get('name', '') if self.model_info else '')[:30]
            title = f'┌─ {self.i18n.get("title")} ──'
            title += f' uptime: {uptime_str} ─'
            if model_name:
                title += f' ─ Model: {model_name} ─'
            title += ' ' * max(0, width - len(title) - 1) + '┐'
            try:
                self.stdscr.addstr(0, 0, title[:width-1], CP(1) | curses.A_BOLD)
            except curses.error:
                pass

            # ── Row 1: CPU + Model │ GPU + Temp ──────────────────────
            # Layout: [CPU info] │ [GPU info]
            # Split width: left ~45%, right ~55%
            mid_x = max(1, width // 2 - 5)
            right_x = mid_x + 1

            row1_y = 1

            # CPU section (left)
            cpu = self.cpu_info
            cpu_usage = cpu.get('usage', 0) if cpu else 0
            cpu_freq = cpu.get('frequency', 0) / 1000 if cpu else 0
            cpu_cores = cpu.get('cores', 0) if cpu else 0
            cpu_threads = cpu.get('threads', 0) if cpu else 0

            # Mini CPU graph (last 30 values)
            cpu_graph = self._draw_mini_graph(list(self.cpu_usage_history), width=20)

            cpu_bar_width = 10
            cpu_bar_filled = int(cpu_usage / 100 * cpu_bar_width)
            cpu_bar = '█' * cpu_bar_filled + '░' * (cpu_bar_width - cpu_bar_filled)

            cpu_line1 = f'│ CPU: {cpu_usage:4.1f}% {cpu_bar}'
            freq_str = f'{cpu_freq:.2f}GHz' if cpu_freq > 0 else ''
            cores_str = f'{cpu_cores}/{cpu_threads}c'
            cpu_line1 += f' {freq_str} {cores_str}' if freq_str else f' {cores_str}'

            # Pad to mid_x
            cpu_line1 = cpu_line1.ljust(mid_x - 1) + '│'
            try:
                self.stdscr.addstr(row1_y, 0, cpu_line1[:width-1], color_for(cpu_usage))
            except curses.error:
                pass

            # GPU section (right)
            gpu = self.gpu_info[0] if self.gpu_info else {}
            gpu_usage = gpu.get('utilization', 0) if gpu else 0
            gpu_mem_used = gpu.get('memory_used', 0) / 1024 if gpu else 0
            gpu_mem_total = gpu.get('memory_total', 0) / 1024 if gpu else 0
            gpu_temp = gpu.get('temperature', 0) if gpu else 0
            gpu_power = gpu.get('power', 0) if gpu else 0

            gpu_mem_pct = (gpu_mem_used / gpu_mem_total * 100) if gpu_mem_total > 0 else 0

            gpu_bar_width = 10
            gpu_bar_filled = int(gpu_usage / 100 * gpu_bar_width)
            gpu_bar = '█' * gpu_bar_filled + '░' * (gpu_bar_width - gpu_bar_filled)

            gpu_line1 = f' GPU: {gpu_usage:4.1f}% {gpu_bar}'
            gpu_line1 += f' {gpu_mem_used:.0f}/{gpu_mem_total:.0f}GB'
            if gpu_temp > 0:
                gpu_line1 += f' {gpu_temp}°C'
            if gpu_power > 0:
                gpu_line1 += f' {gpu_power:.0f}W'
            gpu_line1 = gpu_line1.ljust(width - 1) + '│'
            try:
                gpu_color = C_MAGENTA if gpu_usage < 80 else (C_YELLOW if gpu_usage < 95 else CP(14))
                self.stdscr.addstr(row1_y, right_x, gpu_line1[:width-right_x-1], gpu_color)
            except curses.error:
                pass

            # ── Row 2: Memory │ CPU Graph ──────────────────────────────
            row2_y = 2
            mem = self.memory_info
            mem_usage = mem.get('percent', 0) if mem else 0
            mem_used = mem.get('used', 0) if mem else 0
            mem_total = mem.get('total', 0) if mem else 0

            mem_bar_width = 15
            mem_bar_filled = int(mem_usage / 100 * mem_bar_width)
            mem_bar = '█' * mem_bar_filled + '░' * (mem_bar_width - mem_bar_filled)

            mem_line = f'│ Mem: {mem_usage:4.1f}% {mem_bar} {mem_used:.1f}/{mem_total:.1f}GB'
            mem_line = mem_line.ljust(mid_x - 1) + '│'
            try:
                self.stdscr.addstr(row2_y, 0, mem_line[:width-1], color_for(mem_usage))
            except curses.error:
                pass

            # CPU mini graph (right side of row 2)
            cpu_graph_line = f' [{self._draw_mini_graph(list(self.cpu_usage_history), width=30)}]'
            cpu_graph_line = cpu_graph_line.ljust(width - right_x - 1) + '│'
            try:
                self.stdscr.addstr(row2_y, right_x, cpu_graph_line[:width-right_x-1], C_GREEN)
            except curses.error:
                pass

            # ── Separator ───────────────────────────────────────────────
            sep_y = 3
            sep = '├' + '─' * (mid_x - 2) + '┼' + '─' * (width - mid_x - 2) + '┤'
            try:
                self.stdscr.addstr(sep_y, 0, sep[:width-1], C_WHITE)
            except curses.error:
                pass

            # ── Row 3: TPS metrics │ Tokens ─────────────────────────────
            row3_y = 4
            stats = self.stats if self.stats else {}
            tps = stats.get('tokens_per_second', 0)
            prompt_tps = stats.get('prompt_eval_per_second', 0)
            cache_hit = stats.get('cache_hit_rate', 0)
            running = stats.get('running_requests', 0)
            eval_count = stats.get('eval_count', 0)
            prompt_count = stats.get('prompt_eval_count', 0)

            # TPS bar (mini)
            tps_bar_width = 15
            tps_max = max(max(self.tps_history), 50) if self.tps_history else 50
            tps_bar_filled = min(int(tps / tps_max * tps_bar_width), tps_bar_width)
            tps_bar = '█' * tps_bar_filled + '░' * (tps_bar_width - tps_bar_filled)

            tps_color = C_GREEN if tps > 40 else (C_YELLOW if tps > 20 else CP(14))

            metrics_line = f'│ TPS: {tps:5.1f} {tps_bar}'
            metrics_line += f' cache: {cache_hit:4.0f}%' if cache_hit > 0 else ' cache:  N/A '
            metrics_line += f' prompt: {prompt_count:,}' if prompt_count > 0 else ''
            metrics_line = metrics_line.ljust(width - 1) + '│'
            try:
                self.stdscr.addstr(row3_y, 0, metrics_line[:width-1], tps_color)
            except curses.error:
                pass

            # ── Separator ───────────────────────────────────────────────
            sep2_y = 5
            sep2 = '├' + '─' * (width - 2) + '┤'
            try:
                self.stdscr.addstr(sep2_y, 0, sep2[:width-1], C_WHITE)
            except curses.error:
                pass

            # ── Row 4: Task progress ─────────────────────────────────────
            row4_y = 6

            # Get active task info
            active_tasks = [t for t in self.tasks if t.get('status') == 'running']
            queued_count = len([t for t in self.tasks if t.get('status') == 'queued'])

            if active_tasks:
                task = active_tasks[0]
                stage = task.get('stage', 'decode')
                progress = task.get('progress', 0)
                tokens_gen = task.get('tokens_generated', 0)
                tokens_rem = task.get('tokens_remain', 0)

                stage_color = C_CYAN if stage == 'prefill' else C_MAGENTA
                stage_str = self.i18n.get(stage).upper() if stage in ['prefill', 'decode', 'waiting'] else stage.upper()

                prog_bar_width = 20
                prog_bar_filled = int(progress / 100 * prog_bar_width)
                prog_bar = '█' * prog_bar_filled + '░' * (prog_bar_width - prog_bar_filled)

                task_line = f'│ ● Running: {stage_str} [{prog_bar}] {progress:3d}%'
                task_line += f' out: {tokens_gen:,}' if tokens_gen > 0 else ''
                if queued_count > 0:
                    task_line += f' │ ○ Queued: {queued_count} tasks waiting'
            else:
                task_line = f'│ ● Running: IDLE'
                if queued_count > 0:
                    task_line += f' │ ○ Queued: {queued_count} tasks waiting'

            task_line = task_line.ljust(width - 1) + '│'
            try:
                self.stdscr.addstr(row4_y, 0, task_line[:width-1], C_MAGENTA)
            except curses.error:
                pass

            # ── Bottom border ────────────────────────────────────────────
            bottom_y = 7
            bottom = '└' + '─' * (width - 2) + '┘'
            try:
                self.stdscr.addstr(bottom_y, 0, bottom[:width-1], C_WHITE)
            except curses.error:
                pass

            # ── Footer ───────────────────────────────────────────────────
            footer_y = height - 1
            shortcuts = '  Q=quit  +=faster  -=slower  R=refresh  M=language'
            rate_str = f'Rate: {self.refresh_interval*1000:.0f}ms'
            time_str = self.last_update.strftime('%H:%M:%S') if self.last_update else '--:--:--'
            footer = shortcuts + ' ' * max(0, width - len(shortcuts) - len(rate_str) - len(time_str) - 5) + f'{rate_str}  {time_str}'
            try:
                self.stdscr.addstr(footer_y, 0, footer[:width-1], C_WHITE | curses.A_DIM)
            except curses.error:
                pass

            self.stdscr.refresh()

        except curses.error as e:
            self.logger.debug(f"btop UI draw error: {e}")

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds to human readable string."""
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        if hours > 0:
            return f'{hours}h {mins}m'
        else:
            return f'{mins}m'

    def _init_curses(self):
        """Initialize curses settings and colors - btop style"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(10)  # 10ms timeout for getch - reduces input lag

        # Reduce flicker: Enable optimize mode
        self.stdscr.idlok(True)
        self.stdscr.idcok(True)
        self.stdscr.leaveok(False)

        # Initialize colors if supported
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # btop-inspired color scheme
            # Title/header: bright white
            # CPU: green (low) -> yellow (med) -> red (high)
            # GPU: cyan (low) -> yellow (med) -> magenta (high)
            # Memory: green (low) -> yellow (med) -> red (high)
            # Tasks: magenta for running, cyan for prefill, white for queued

            if curses.can_change_color():
                try:
                    # Basic colors - unified scheme
                    curses.init_pair(self.COLOR_HEADER, curses.COLOR_WHITE, -1)
                    curses.init_pair(self.COLOR_CPU, curses.COLOR_GREEN, -1)      # Green for CPU
                    curses.init_pair(self.COLOR_GPU, curses.COLOR_CYAN, -1)      # Cyan for GPU
                    curses.init_pair(self.COLOR_MODEL, curses.COLOR_MAGENTA, -1) # Magenta for Model
                    curses.init_pair(self.COLOR_METRICS, curses.COLOR_YELLOW, -1) # Yellow for Metrics
                    curses.init_pair(self.COLOR_TASK, curses.COLOR_MAGENTA, -1)  # Magenta for Tasks

                    curses.init_pair(self.COLOR_BAR_FILLED, curses.COLOR_GREEN, -1)
                    curses.init_pair(self.COLOR_BAR_EMPTY, curses.COLOR_BLACK, -1)

                    # Status colors
                    curses.init_pair(self.COLOR_PREFILL, curses.COLOR_CYAN, -1)    # Cyan for prefill
                    curses.init_pair(self.COLOR_DECODE, curses.COLOR_MAGENTA, -1)  # Magenta for decode
                    curses.init_pair(self.COLOR_QUEUED, curses.COLOR_WHITE, -1)    # White for queued

                    # Usage level colors (unified across panels)
                    curses.init_pair(self.COLOR_SUCCESS, curses.COLOR_GREEN, -1)   # Low/normal - green
                    curses.init_pair(self.COLOR_WARNING, curses.COLOR_YELLOW, -1) # Medium - yellow
                    curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)     # High - red

                    # TPS colors
                    curses.init_pair(self.COLOR_TPS_HIGH, curses.COLOR_GREEN, -1)   # >40 t/s - green
                    curses.init_pair(self.COLOR_TPS_MED, curses.COLOR_YELLOW, -1)    # 20-40 t/s - yellow
                    curses.init_pair(self.COLOR_TPS_LOW, curses.COLOR_RED, -1)      # <20 t/s - red
                except curses.error as e:
                    self.logger.debug(f"Color init error: {e}")
            else:
                self._init_basic_colors()
    
    def _init_basic_colors(self):
        """Initialize basic 8-color palette"""
        try:
            curses.init_pair(self.COLOR_HEADER, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_CPU, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_GPU, curses.COLOR_BLUE, -1)
            curses.init_pair(self.COLOR_MODEL, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_METRICS, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_TASK, curses.COLOR_MAGENTA, -1)
            curses.init_pair(self.COLOR_BAR_FILLED, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_BAR_EMPTY, curses.COLOR_BLACK, -1)
            curses.init_pair(self.COLOR_PREFILL, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_DECODE, curses.COLOR_MAGENTA, -1)
            curses.init_pair(self.COLOR_QUEUED, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_SUCCESS, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_WARNING, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)
            curses.init_pair(self.COLOR_TPS_HIGH, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_TPS_MED, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_TPS_LOW, curses.COLOR_RED, -1)
            # Phase 2: Dim/bright color variants
            curses.init_pair(18, curses.COLOR_GREEN, -1)    # Dim green
            curses.init_pair(19, curses.COLOR_CYAN, -1)     # Dim cyan
            curses.init_pair(20, curses.COLOR_MAGENTA, -1)  # Dim magenta
            curses.init_pair(21, curses.COLOR_YELLOW, -1)    # Dim yellow
            curses.init_pair(22, curses.COLOR_WHITE, -1)     # Bright white
            curses.init_pair(23, curses.COLOR_RED, -1)       # Alert red
        except curses.error as e:
            self.logger.debug(f"Basic color init error: {e}")

    def _draw_bar(self, value: float, max_value: float, width: int = 20,
                  filled_color: int = 7, empty_color: int = 8):
        """Draw a progress bar using block characters"""
        if max_value <= 0:
            return '░' * width

        filled = int((value / max_value) * width)
        empty = width - filled

        bar = '█' * filled + '░' * empty
        return bar

    def _draw_shaded_bar_cell(self, row: int, bar_bottom: int, bar_top: int, base_color: int, x: int) -> None:
        """Draw a single shaded bar cell based on vertical position.
        Phase 2: Adds depth with sub-shading based on row position within bar range.
        """
        bar_range = bar_top - bar_bottom
        shade_ratio = (row - bar_bottom) / bar_range if bar_range > 0 else 1.0
        if shade_ratio > 0.66:
            attr = curses.color_pair(base_color) | curses.A_BOLD
        elif shade_ratio > 0.33:
            attr = curses.color_pair(base_color)
        else:
            attr = curses.color_pair(base_color) | curses.A_DIM
        try:
            self.stdscr.addstr(row, x, "█", attr)
        except curses.error:
            pass

    def _get_tps_color(self, tps: float) -> int:
        """Get TPS color with sub-shading based on absolute value.
        Phase 2: Extends TPS coloring to use dim/bright variants.
        Returns a color pair index.
        """
        if tps >= 60:
            return self.COLOR_TPS_HIGH  # Bright green (>60)
        elif tps >= 40:
            return 18  # Dim green (40-60)
        elif tps >= 20:
            return self.COLOR_TPS_MED  # Yellow (20-40)
        elif tps >= 10:
            return 21  # Dim yellow (10-20)
        else:
            return self.COLOR_TPS_LOW  # Red (<10)

    def _draw_sparkline(self, values: List[float], width: int = 20, height: int = 4,
                        min_val: float = None, max_val: float = None,
                        color: int = 2, fill: bool = False) -> List[str]:
        """Draw a sparkline chart using Unicode block characters.
        Uses lower block characters for fill effect, similar to btop.
        Returns list of strings representing the chart rows.
        """
        if not values or len(values) < 2:
            return [' ' * width for _ in range(height)]

        data = list(values)[-width:]  # Take last 'width' values
        if len(data) < 2:
            return [' ' * width for _ in range(height)]

        # Determine min/max for scaling
        if min_val is None:
            min_val = min(data)
        if max_val is None:
            max_val = max(data)

        # Ensure we have a non-zero range
        if max_val == min_val:
            max_val = min_val + 1

        val_range = max_val - min_val
        rows = [' ' * width for _ in range(height)]

        # Calculate y position for each data point
        # y=0 is top, y=height-1 is bottom
        points = []
        for i, val in enumerate(data):
            x = i  # column position
            y = int((val - min_val) / val_range * (height - 1))
            y = max(0, min(height - 1, height - 1 - y))  # Flip and clamp
            points.append((x, y))

        # Draw the line and fill
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            if fill:
                # Fill area under the line
                for x in range(x1, x2 + 1):
                    for y in range(y2, height):
                        if 0 <= y < height and 0 <= x < width:
                            rows[y] = rows[y][:x] + '█' + rows[y][x+1:]
            else:
                # Draw line with vertical segments
                if x1 == x2:
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        if 0 <= y < height and 0 <= x1 < width:
                            rows[y] = rows[y][:x1] + '│' + rows[y][x1+1:]
                else:
                    # Horizontal segment at y1
                    for x in range(x1, x2 + 1):
                        if 0 <= y1 < height and 0 <= x < width:
                            rows[y1] = rows[y1][:x] + '─' + rows[y1][x+1:]

        # Draw endpoints
        if points:
            # First point
            x, y = points[0]
            if 0 <= y < height and 0 <= x < width:
                rows[y] = rows[y][:x] + '●' + rows[y][x+1:]
            # Last point (emphasized)
            x, y = points[-1]
            if 0 <= y < height and 0 <= x < width:
                rows[y] = rows[y][:x] + '●' + rows[y][x+1:]

        return rows

    def _draw_gradient_bar(self, value: float, max_value: float, width: int = 20,
                          low_color: int = 2, med_color: int = 13, high_color: int = 14) -> str:
        """Draw a bar with color gradient based on value percentage.
        Returns tuple of (bar_string, color)."""
        if max_value <= 0:
            return '░' * width, low_color

        percent = value / max_value
        filled = int(percent * width)
        empty = width - filled

        # Choose color based on percentage
        if percent < 0.6:
            color = low_color
        elif percent < 0.85:
            color = med_color
        else:
            color = high_color

        bar = '█' * filled + '░' * empty
        return bar, color
    
    def _draw_tps_chart(self, tps_values: List[float], width: int = 40, height: int = 5):
        """Draw a simple TPS trend chart"""
        if not tps_values:
            return ['No data'] * height
        
        max_val = max(tps_values) if tps_values else 1
        if max_val <= 0:
            max_val = 1
        
        chart = []
        for row in range(height):
            threshold = max_val * (height - row) / height
            line = ''
            for val in tps_values[-width:]:
                if val >= threshold:
                    line += '█'
                else:
                    line += ' '
            chart.append(line)
        
        return chart

    def _draw_line_chart(self, values: List[float], width: int = 20, height: int = 4,
                         min_val: float = 0, max_val: float = 100, color: int = 2) -> List[str]:
        """Draw a line chart for usage percentage history with better visuals.
        Uses box-drawing characters and shows data points.
        Returns list of strings representing the chart rows.
        """
        if not values or len(values) < 2:
            return [' ' * width] * height

        # Take the last 'width' number of values
        data = list(values)[-width:]
        if len(data) < 2:
            return [' ' * width] * height

        chart_rows = [' ' * width for _ in range(height)]

        # Calculate points for each data value
        points = []
        for i, val in enumerate(data):
            x = int((i / (len(data) - 1)) * (width - 1))
            y = height - 1 - int((val - min_val) / (max_val - min_val + 0.001) * (height - 1))
            y = max(0, min(height - 1, y))
            points.append((x, y))

        # Draw the line using box-drawing characters
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            if x1 == x2:
                # Vertical segment
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    row = height - 1 - y
                    if 0 <= row < height:
                        chart_rows[row] = chart_rows[row][:x1] + '│' + chart_rows[row][x1+1:]
            else:
                # Horizontal segment
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    row = height - 1 - y1
                    if 0 <= row < height and 0 <= x < width:
                        chart_rows[row] = chart_rows[row][:x] + '─' + chart_rows[row][x+1:]

        # Draw data points at key positions (first, last, and peaks)
        if points:
            # Last point - prominent marker
            x, y = points[-1]
            row = height - 1 - y
            if 0 <= row < height and 0 <= x < width:
                chart_rows[row] = chart_rows[row][:x] + '●' + chart_rows[row][x+1:]

        return chart_rows

    def _draw_area_chart(self, values: List[float], width: int = 25, height: int = 5,
                        min_val: float = 0, max_val: float = 100, color: int = 2) -> List[str]:
        """Draw an area chart with fill effect, similar to btop.
        Uses Unicode block characters for dense visualization.
        """
        if not values or len(values) < 2:
            return [' ' * width] * height

        data = list(values)[-width:]
        if len(data) < 2:
            return [' ' * width] * height

        val_range = max_val - min_val if max_val != min_val else 1
        rows = [' ' * width for _ in range(height)]

        for i, val in enumerate(data):
            normalized = (val - min_val) / val_range
            filled_cells = int(normalized * height)

            for row in range(height):
                if height - 1 - row < filled_cells:
                    rows[row] = rows[row][:i] + '█' + rows[row][i+1:]

        return rows

    def _draw_header(self, y: int, x: int, width: int):
        """Draw the header"""
        title = f" {self.i18n.get('title')} "
        url_str = f"  URL: {self.server_url if self.server_url else 'N/A'} "
        
        # Center title
        center_x = x + (width - len(title)) // 2
        try:
            self.stdscr.addstr(y, center_x, title, curses.color_pair(self.COLOR_HEADER) | curses.A_BOLD)
            # Right align URL
            self.stdscr.addstr(y, x + width - len(url_str) - 1, url_str, curses.color_pair(self.COLOR_HEADER))
        except curses.error as e:
            self.logger.debug(f"Header draw error: {e}")
    
    def _draw_cpu_info(self, y: int, x: int, width: int, height: int):
        """Draw CPU information panel with proper graph and axis labels"""
        self._draw_panel_header(y, x, width, height, self.i18n.get('cpu_info'), self.COLOR_CPU)

        if not self.cpu_info:
            try:
                self.stdscr.addstr(y + 2, x + 2, self.i18n.get('not_available'), curses.color_pair(self.COLOR_WARNING))
            except curses.error as e:
                self.logger.debug(f"CPU panel not available draw error: {e}")
            return

        try:
            # Model name (header line)
            model = self.cpu_info.get('model', 'Unknown')
            # Truncate conservatively to fit the panel width
            available = width - 4
            if len(model) > available:
                model = model[:available-3] + '...'
            self.stdscr.addstr(y + 1, x + 2, model, curses.color_pair(self.COLOR_CPU) | curses.A_BOLD)

            usage = self.cpu_info.get('usage', 0)
            usage_color = self.COLOR_CPU if usage < 70 else (self.COLOR_WARNING if usage < 90 else self.COLOR_ERROR)

            # Chart area layout
            chart_top = y + 2
            chart_height = max(3, height - 5)  # Leave room for Y-axis labels
            chart_width = max(10, width - 10)   # Leave room for Y-axis

            if chart_height > 3 and chart_width > 10:
                # Draw Y-axis labels (percentages) on left side
                y_label_x = x + 2
                self.stdscr.addstr(chart_top, y_label_x, "100", curses.color_pair(self.COLOR_CPU))
                self.stdscr.addstr(chart_top + chart_height // 2, y_label_x, " 50", curses.color_pair(self.COLOR_CPU))
                self.stdscr.addstr(chart_top + chart_height - 1, y_label_x, "  0", curses.color_pair(self.COLOR_CPU))

                # Draw Y-axis vertical line
                chart_x = y_label_x + 4
                grid_color = curses.color_pair(self.COLOR_CPU) | curses.A_DIM

                # Draw horizontal grid lines
                for h in [0, chart_height // 2, chart_height - 1]:
                    if h < chart_height:
                        self.stdscr.addstr(chart_top + h, chart_x, "┼", grid_color)
                        self.stdscr.addstr(chart_top + h, chart_x + 1, "─" * min(chart_width - 2, width - chart_x - 2), grid_color)

                # Draw bar chart using gradient bars at each time point
                data = list(self.cpu_usage_history)
                bar_area_x = chart_x + 1
                bar_area_width = min(chart_width - 2, len(data), width - bar_area_x - 4)

                for i in range(min(bar_area_width, len(data))):
                    val = data[i] if i < len(data) else 0
                    bar_height = int((val / 100.0) * chart_height)
                    bar_height = max(1, min(bar_height, chart_height))  # Clamp to chart height

                    # Draw bar from bottom up
                    for h in range(bar_height):
                        row = chart_top + chart_height - 1 - h
                        if row >= chart_top and row < chart_top + chart_height:
                            self.stdscr.addstr(row, bar_area_x + i, "█", curses.color_pair(usage_color))

                # Draw current value on right side
                val_y = chart_top + chart_height // 2
                val_x = bar_area_x + bar_area_width + 2
                if val_x < x + width - 10:
                    val_str = f"{usage:5.1f}%"
                    self.stdscr.addstr(val_y, val_x, val_str, curses.color_pair(usage_color) | curses.A_BOLD)

                # Draw X-axis time labels at bottom
                time_y = chart_top + chart_height + 1
                if time_y < y + height - 1:
                    # Show time markers: "30s", "20s", "10s", "now"
                    time_x = chart_x
                    if bar_area_width >= 20:
                        self.stdscr.addstr(time_y, time_x + 2, "30s", curses.color_pair(self.COLOR_CPU))
                        self.stdscr.addstr(time_y, time_x + bar_area_width // 2, "15s", curses.color_pair(self.COLOR_CPU))
                        self.stdscr.addstr(time_y, time_x + bar_area_width - 3, "now", curses.color_pair(self.COLOR_CPU))

            # Bottom info row: Frequency and Cores
            info_y = y + height - 1
            freq = self.cpu_info.get('frequency', 0) / 1000  # Convert to GHz
            cores = self.cpu_info.get('cores', 0)
            threads = self.cpu_info.get('threads', 0)

            freq_str = f"{freq:.2f} GHz" if freq > 0 else ""
            cores_str = f"Cores: {cores}/{threads}"
            info_x = x + 2
            self.stdscr.addstr(info_y, info_x, freq_str, curses.color_pair(self.COLOR_CPU))
            if len(freq_str) > 0:
                info_x += len(freq_str) + 2
            self.stdscr.addstr(info_y, info_x, cores_str, curses.color_pair(self.COLOR_CPU))

        except curses.error as e:
            self.logger.debug(f"CPU info draw error: {e}")

    def _draw_memory_info(self, y: int, x: int, width: int, height: int):
        """Draw Memory information panel with bar chart"""
        self._draw_panel_header(y, x, width, height, self.i18n.get('memory'), self.COLOR_CPU)

        if not self.memory_info or self.memory_info.get('total', 0) <= 0:
            try:
                self.stdscr.addstr(y + 2, x + 2, self.i18n.get('not_available'), curses.color_pair(self.COLOR_WARNING))
            except curses.error as e:
                self.logger.debug(f"Memory panel not available draw error: {e}")
            return

        try:
            mem_percent = self.memory_info.get('percent', 0)
            mem_total = self.memory_info.get('total', 0)
            mem_used = self.memory_info.get('used', 0)
            mem_color = self.COLOR_CPU if mem_percent < 70 else (self.COLOR_WARNING if mem_percent < 90 else self.COLOR_ERROR)

            # Title/info row
            self.stdscr.addstr(y + 1, x + 2, f"Used: {mem_used:.1f} / {mem_total:.1f} GB", curses.color_pair(self.COLOR_CPU))

            # Chart area
            chart_top = y + 2
            chart_height = max(3, height - 4)
            chart_width = max(10, width - 10)

            if chart_height > 3 and chart_width > 10:
                # Y-axis labels
                y_label_x = x + 2
                self.stdscr.addstr(chart_top, y_label_x, "100", curses.color_pair(self.COLOR_CPU))
                self.stdscr.addstr(chart_top + chart_height // 2, y_label_x, " 50", curses.color_pair(self.COLOR_CPU))
                self.stdscr.addstr(chart_top + chart_height - 1, y_label_x, "  0", curses.color_pair(self.COLOR_CPU))

                # Chart area with grid
                chart_x = y_label_x + 4
                grid_color = curses.color_pair(self.COLOR_CPU) | curses.A_DIM

                for h in [0, chart_height // 2, chart_height - 1]:
                    if h < chart_height:
                        self.stdscr.addstr(chart_top + h, chart_x, "┼", grid_color)
                        self.stdscr.addstr(chart_top + h, chart_x + 1, "─" * min(chart_width - 2, width - chart_x - 2), grid_color)

                # Draw bar chart
                data = list(self.memory_usage_history)
                bar_area_x = chart_x + 1
                bar_area_width = min(chart_width - 2, len(data), width - bar_area_x - 4)

                for i in range(min(bar_area_width, len(data))):
                    val = data[i] if i < len(data) else 0
                    bar_height = int((val / 100.0) * chart_height)
                    bar_height = max(1, min(bar_height, chart_height))

                    for h in range(bar_height):
                        row = chart_top + chart_height - 1 - h
                        if row >= chart_top and row < chart_top + chart_height:
                            self.stdscr.addstr(row, bar_area_x + i, "█", curses.color_pair(mem_color))

                # Current value
                val_y = chart_top + chart_height // 2
                val_x = bar_area_x + bar_area_width + 2
                if val_x < x + width - 10:
                    val_str = f"{mem_percent:5.1f}%"
                    self.stdscr.addstr(val_y, val_x, val_str, curses.color_pair(mem_color) | curses.A_BOLD)

            # Bottom row: Memory type and freq
            info_y = y + height - 1
            mem_type = self.memory_info.get('type', 'Unknown')
            mem_freq = self.memory_info.get('frequency', 0)

            type_str = f"{mem_type}" if mem_type and mem_type != 'Unknown' else ""
            if mem_freq > 0:
                type_str += f" {mem_freq} MT/s" if type_str else f"{mem_freq} MT/s"
            if type_str:
                self.stdscr.addstr(info_y, x + 2, type_str, curses.color_pair(self.COLOR_CPU))

        except curses.error as e:
            self.logger.debug(f"Memory info draw error: {e}")

    def _draw_gpu_info(self, y: int, x: int, width: int, height: int):
        """Draw GPU information panel with bar charts and stats"""
        self._draw_panel_header(y, x, width, height, self.i18n.get('gpu_info'), self.COLOR_GPU)

        if not self.gpu_info:
            try:
                self.stdscr.addstr(y + 2, x + 2, self.i18n.get('gpu_not_detected'), curses.color_pair(self.COLOR_WARNING))
            except curses.error as e:
                self.logger.debug(f"GPU panel not detected draw error: {e}")
            return

        # Calculate rows needed per GPU
        rows_per_gpu = 7  # 1 header + 2 GPU usage + 2 VRAM + 2 stats
        max_gpus = min(len(self.gpu_info), max(1, (height - 3) // rows_per_gpu))

        for i in range(max_gpus):
            gpu = self.gpu_info[i]

            row = y + 2 + i * rows_per_gpu
            if row >= y + height - 2:
                break

            name = gpu.get('name', 'Unknown')
            # Truncate name to fit
            name_max_len = max(10, width - 25)
            if len(name) > name_max_len:
                name = name[:name_max_len-3] + '...'
            try:
                # GPU name header
                usage = gpu.get('utilization', 0)
                usage_color = self.COLOR_GPU if usage < 80 else (self.COLOR_WARNING if usage < 95 else self.COLOR_ERROR)
                self.stdscr.addstr(row, x + 2, f"GPU {i}: {name}", curses.color_pair(self.COLOR_GPU) | curses.A_BOLD)

                # GPU Usage bar chart
                bar_width = min(20, width - 15)
                bar_x = x + 2
                bar, bar_color = self._draw_gradient_bar(usage, 100, bar_width,
                                                        low_color=self.COLOR_GPU,
                                                        med_color=self.COLOR_WARNING,
                                                        high_color=self.COLOR_ERROR)
                self.stdscr.addstr(row + 1, bar_x, f"Use:", curses.color_pair(self.COLOR_GPU))
                self.stdscr.addstr(row + 1, bar_x + 5, bar, curses.color_pair(bar_color))
                self.stdscr.addstr(row + 1, bar_x + bar_width + 7, f"{usage:3.0f}%", curses.color_pair(usage_color) | curses.A_BOLD)

                # VRAM bar chart
                mem_used = gpu.get('memory_used', 0) / 1024  # GB
                mem_total = gpu.get('memory_total', 1) / 1024
                mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                mem_freq = gpu.get('mem_clock', 0)  # Memory clock in GHz

                vram_bar, vram_color = self._draw_gradient_bar(mem_percent, 100, bar_width,
                                                               low_color=self.COLOR_GPU,
                                                               med_color=self.COLOR_WARNING,
                                                               high_color=self.COLOR_ERROR)
                self.stdscr.addstr(row + 2, bar_x, f"VRAM:", curses.color_pair(self.COLOR_GPU))
                self.stdscr.addstr(row + 2, bar_x + 5, vram_bar, curses.color_pair(vram_color))
                mem_str = f"{mem_used:5.1f}/{mem_total:.0f}GB"
                if mem_freq > 0:
                    mem_str += f" ({mem_freq:.2f}GHz)"
                self.stdscr.addstr(row + 2, bar_x + bar_width + 7, mem_str, curses.color_pair(self.COLOR_GPU))

                # Stats row: temp, power, freq, fan
                temp = gpu.get('temperature', 0)
                temp_color = self.COLOR_GPU if temp < 70 else (self.COLOR_WARNING if temp < 85 else self.COLOR_ERROR)
                power = gpu.get('power', 0)
                gpu_freq = gpu.get('gpu_clock', 0)  # GPU clock in GHz
                fan_speed = gpu.get('fan_speed', 0)

                stats_y = row + 4
                stats = []
                if temp > 0:
                    stats.append(f"Temp: {temp}°C")
                if power > 0:
                    stats.append(f"Power: {power:.0f}W")
                if gpu_freq > 0:
                    stats.append(f"GPU: {gpu_freq:.2f}GHz")
                if fan_speed > 0:
                    stats.append(f"Fan: {fan_speed}%")

                if stats and stats_y < y + height - 1:
                    self.stdscr.addstr(stats_y, x + 2, " | ".join(stats), curses.color_pair(temp_color))


            except curses.error as e:
                self.logger.debug(f"GPU stats draw error: {e}")

    def _draw_model_status(self, y: int, x: int, width: int, height: int):
        """Draw model status panel - compact btop style"""
        self._draw_panel_header(y, x, width, height, self.i18n.get('model_status'), self.COLOR_MODEL)

        if not self.model_info or len(self.model_info) == 0:
            try:
                self.stdscr.addstr(y + 2, x + 2, self.i18n.get('not_available'), curses.color_pair(self.COLOR_WARNING))
            except curses.error as e:
                self.logger.debug(f"Model panel not available draw error: {e}")
            return

        try:
            # Model name - bold and prominent
            name = self.model_info.get('name', 'Unknown')
            name_short = name[:width - 8] if len(name) > width - 8 else name
            self.stdscr.addstr(y + 2, x + 2, name_short, curses.color_pair(self.COLOR_MODEL) | curses.A_BOLD)

            # Determine state and stage from running tasks
            running_tasks = [t for t in self.tasks if t.get('status') == 'running']
            stage_row = y + 3

            if running_tasks:
                # Show stage of first running task (with icon)
                first_task = running_tasks[0]
                stage = first_task.get('stage', 'unknown')
                stage_translated = self.i18n.get(stage) if stage in ['prefill', 'decode', 'waiting'] else stage
                stage_color = self.COLOR_PREFILL if stage == 'prefill' else (self.COLOR_DECODE if stage == 'decode' else self.COLOR_QUEUED)
                icon = self.STAGE_ICONS.get(stage, '○')
                self.stdscr.addstr(stage_row, x + 2, f"{icon} {stage_translated.upper()}", curses.color_pair(stage_color) | curses.A_BOLD)
            else:
                state = self.model_info.get('state', 'Unknown')
                stage_color = self.COLOR_SUCCESS if state == 'Running' else self.COLOR_WARNING
                self.stdscr.addstr(stage_row, x + 2, f"● {state.upper()}", curses.color_pair(stage_color) | curses.A_BOLD)

            # Context - compact display
            ctx = self.model_info.get('context', 0)
            if ctx > 0:
                ctx_str = f"Ctx: {ctx:,}" if ctx >= 1000 else f"Ctx: {ctx}"
                self.stdscr.addstr(stage_row, x + 15, ctx_str, curses.color_pair(self.COLOR_MODEL))

            # Batch
            batch = self.model_info.get('batch', 0)
            if batch > 0:
                self.stdscr.addstr(y + 4, x + 2, f"Batch: {batch}", curses.color_pair(self.COLOR_MODEL))

            # Slots info - use actual task count if available
            running = len([t for t in self.tasks if t.get('status') == 'running'])
            if running == 0 and self.stats:
                running = self.stats.get('running_requests', 0)
            if running > 0:
                self.stdscr.addstr(y + 4, x + 15, f"Active: {running}", curses.color_pair(self.COLOR_SUCCESS))

            # Total tokens processed - show input and output separately
            if self.stats:
                eval_count = self.stats.get('eval_count', 0)
                prompt_count = self.stats.get('prompt_eval_count', 0)
                if eval_count > 0 or prompt_count > 0:
                    self.stdscr.addstr(y + height - 2, x + 2, f"In: {prompt_count:,} | Out: {eval_count:,}", curses.color_pair(self.COLOR_METRICS))

        except curses.error as e:
            self.logger.debug(f"Model status draw error: {e}")

    def _draw_realtime_metrics(self, y: int, x: int, width: int, height: int):
        """Draw real-time metrics panel with bar chart and info at top"""
        self._draw_panel_header(y, x, width, height, self.i18n.get('realtime_metrics'), self.COLOR_METRICS)

        if not self.stats or len(self.stats) == 0:
            try:
                if self.api_consecutive_failures > 0:
                    msg = f"API Error ({self.api_consecutive_failures})"
                    self.stdscr.addstr(y + 2, x + 2, msg, curses.color_pair(self.COLOR_ERROR))
                else:
                    msg = self.i18n.get('metrics_disabled')
                    self.stdscr.addstr(y + 2, x + 2, msg, curses.color_pair(self.COLOR_WARNING))
            except curses.error as e:
                self.logger.debug(f"Metrics panel not available draw error: {e}")
            return

        try:
            tps = self.stats.get('tokens_per_second', 0)
            prompt_rate = self.stats.get('prompt_eval_per_second', 0)
            cache_hit = self.stats.get('cache_hit_rate', 0)
            running = self.stats.get('running_requests', 0)
            eval_count = self.stats.get('eval_count', 0)
            prompt_count = self.stats.get('prompt_eval_count', 0)

            # Info row at top (y+1)
            info_y = y + 1
            tps_color = self.COLOR_TPS_HIGH if tps > 40 else (self.COLOR_TPS_MED if tps > 20 else self.COLOR_TPS_LOW)
            cache_color = self.COLOR_SUCCESS if cache_hit > 80 else (self.COLOR_WARNING if cache_hit > 50 else self.COLOR_ERROR)

            info_parts = [
                f"TPS: {tps:.1f}",
                f"P: {prompt_rate:.1f}/s" if prompt_rate > 0 else "P: --",
                f"C: {cache_hit:.0f}%" if cache_hit > 0 else "C: --",
                f"R: {running}"
            ]
            info_str = " | ".join(info_parts)
            self.stdscr.addstr(info_y, x + 2, info_str[:width - 4], curses.color_pair(self.COLOR_METRICS))

            # Chart area (below info)
            chart_top = y + 2
            chart_height = max(3, height - 3)  # Leave room for bottom info
            chart_width = width - 4  # Full width minus borders

            if chart_height > 3 and chart_width > 10:
                # Y-axis labels (TPS values)
                tps_max = max(max(self.tps_history), 1) if self.tps_history else 1
                tps_max = max(tps_max * 1.1, 10)  # Ensure minimum scale

                y_label_x = x + 2
                # Y-axis labels on left side
                self.stdscr.addstr(chart_top, y_label_x, f"{tps_max:5.0f}", curses.color_pair(self.COLOR_METRICS))
                mid_y = chart_top + chart_height // 2
                self.stdscr.addstr(mid_y, y_label_x, f"{tps_max/2:5.0f}", curses.color_pair(self.COLOR_METRICS))
                bottom_y = chart_top + chart_height - 1
                self.stdscr.addstr(bottom_y, y_label_x, "    0", curses.color_pair(self.COLOR_METRICS))

                # Chart area starts after Y-axis labels
                chart_x = y_label_x + 6
                chart_right = x + width - 2
                bar_area_x = chart_x
                bar_area_width = chart_right - bar_area_x - 1

                grid_color = curses.color_pair(self.COLOR_METRICS) | curses.A_DIM

                # Draw horizontal grid lines across full chart width
                for h in [0, chart_height // 2, chart_height - 1]:
                    if h < chart_height:
                        grid_y = chart_top + h
                        self.stdscr.addstr(grid_y, chart_x, "├", grid_color)
                        line_width = min(bar_area_width, chart_right - chart_x - 1)
                        self.stdscr.addstr(grid_y, chart_x + 1, "─" * line_width, grid_color)
                        self.stdscr.addstr(grid_y, chart_right - 1, "┤", grid_color)

                # Draw bar chart for TPS history - bars fill the width
                data = list(self.tps_history)
                if len(data) > 0:
                    bar_count = min(bar_area_width, len(data))
                    for i in range(bar_count):
                        # Map data index to bar position
                        data_idx = len(data) - bar_count + i
                        val = data[data_idx] if data_idx >= 0 else 0
                        bar_height = int((val / tps_max) * chart_height)
                        bar_height = max(1, min(bar_height, chart_height))

                        for h in range(bar_height):
                            row = bottom_y - h
                            if row >= chart_top and row < chart_top + chart_height:
                                self.stdscr.addstr(row, bar_area_x + i, "█", curses.color_pair(tps_color))

                # Current value at right side
                val_str = f"{tps:5.1f}"
                self.stdscr.addstr(mid_y, chart_right - len(val_str) - 1, val_str, curses.color_pair(tps_color) | curses.A_BOLD)

                # X-axis time labels at bottom
                time_y = chart_top + chart_height
                if time_y < y + height - 1 and bar_area_width >= 15:
                    self.stdscr.addstr(time_y, bar_area_x + 1, "30s", curses.color_pair(self.COLOR_METRICS))
                    mid_pos = bar_area_width // 2
                    if mid_pos > 5:
                        self.stdscr.addstr(time_y, bar_area_x + mid_pos, "15s", curses.color_pair(self.COLOR_METRICS))
                    self.stdscr.addstr(time_y, bar_area_x + bar_area_width - 3, "now", curses.color_pair(self.COLOR_METRICS))

        except curses.error as e:
            self.logger.debug(f"Metrics time label draw error: {e}")

    def _draw_panel_header(self, y: int, x: int, width: int, height: int, title: str, color: int):
        """Draw a panel with header"""
        try:
            # Top border
            self.stdscr.addstr(y, x, '┌' + '─' * (width - 2) + '┐', curses.color_pair(color))
            # Title with underline
            title_x = x + 2
            self.stdscr.addstr(y, title_x, f" {title} ", curses.color_pair(color) | curses.A_BOLD | curses.A_UNDERLINE)
        except curses.error as e:
            self.logger.debug(f"Panel header draw error: {e}")

    def _draw_tasks(self, y: int, x: int, width: int, height: int):
        """Draw tasks list with tree structure grouped by task_id (job_id)"""
        task_count = len(self.tasks)
        self._draw_panel_header(y, x, width, height, f"{self.i18n.get('active_tasks')} ({task_count})", self.COLOR_TASK)

        if not self.tasks:
            try:
                self.stdscr.addstr(y + 2, x + 2, self.i18n.get('no_tasks'), curses.color_pair(self.COLOR_QUEUED))
            except curses.error as e:
                self.logger.debug(f"Tasks no_tasks draw error: {e}")
            return

        # Determine header based on available data
        has_task_id = any(t.get('task_id', 0) for t in self.tasks)

        try:
            if has_task_id:
                # Header for tree structure: Task tree with TPS (no In - /slots doesn't provide it)
                header = f"{'JobID / Slot':<25} | {'Stage':<8} | {'Out':<6} | {'TPS':<7} | {'%':<4}"
            else:
                # Header for synthetic data (has In from metrics)
                header = f"{'ID':<5} | {self.i18n.get('status'):<8} | {'In':<8} | {'Out':<8} | {'TPS':<8}"
            self.stdscr.addstr(y + 2, x + 2, header, curses.A_BOLD | curses.A_UNDERLINE)
        except curses.error as e:
            self.logger.debug(f"Tasks header draw error: {e}")

        # Group tasks by task_id (job_id)
        from collections import defaultdict
        jobs = defaultdict(list)
        for task in self.tasks:
            task_id = task.get('task_id', 0)
            if task_id > 0:
                jobs[task_id].append(task)

        # Draw tasks with tree structure
        row = y + 3
        max_row = y + height - 2

        if has_task_id:
            # Sort job IDs
            sorted_job_ids = sorted(jobs.keys())
            job_count = len(sorted_job_ids)

            for idx, job_id in enumerate(sorted_job_ids):
                if row >= max_row:
                    break

                slots = jobs[job_id]
                is_last_job = (idx == job_count - 1)

                # Draw job_id header
                tree_char = '└── ' if is_last_job else '├── '
                job_line = f"JobID {job_id}"
                full_line = f"{tree_char}{job_line:<21}"
                try:
                    self.stdscr.addstr(row, x + 2, full_line[:width - 4], curses.color_pair(self.COLOR_HEADER) | curses.A_BOLD)
                except curses.error as e:
                    self.logger.debug(f"Tasks job line draw error: {e}")
                row += 1

                # Draw slots under this job
                slot_count = len(slots)
                for s_idx, task in enumerate(slots):
                    if row >= max_row:
                        break

                    is_last_slot = (s_idx == slot_count - 1) or is_last_job
                    slot_prefix = '    ' if is_last_job else '│   '
                    slot_char = '└── ' if is_last_slot else '├── '

                    slot_id = task.get('id', 0)
                    stage = task.get('stage', 'unknown')
                    tps = task.get('tps', 0)
                    tokens_gen = task.get('tokens_generated', 0)
                    progress = task.get('progress', 0)

                    stage_color = {
                        'prefill': self.COLOR_PREFILL,
                        'decode': self.COLOR_DECODE,
                        'waiting': self.COLOR_QUEUED
                    }.get(stage, self.COLOR_QUEUED)

                    stage_str = self.i18n.get(stage)[:6] if stage in ['prefill', 'decode', 'waiting'] else stage[:6]
                    tps_str = f"{tps:>6.1f}" if tps > 0 else "   --"

                    slot_line = f"{slot_prefix}{slot_char}Slot {slot_id:<2} | {stage_str:<8} | {tokens_gen:<6} | {tps_str} | {progress:>3}%"
                    try:
                        self.stdscr.addstr(row, x + 2, slot_line[:width - 4], curses.color_pair(stage_color))
                    except curses.error as e:
                        self.logger.debug(f"Tasks slot line draw error: {e}")
                    row += 1
        else:
            # Synthetic data fallback (no tree structure)
            for i, task in enumerate(self.tasks[:height - 5]):
                if row >= max_row:
                    break

                status = task.get('status', 'unknown')
                stage = task.get('stage', 'unknown')
                tps = task.get('tps', 0)
                tokens_gen = task.get('tokens_generated', 0)
                prompt_tokens = task.get('prompt_tokens', 0)

                status_color = {
                    'running': self.COLOR_SUCCESS,
                    'queued': self.COLOR_QUEUED,
                    'completed': self.COLOR_SUCCESS,
                    'failed': self.COLOR_ERROR
                }.get(status, self.COLOR_WARNING)

                task_id = f"{task.get('id', i + 1):03d}"

                if stage == 'prefill':
                    prog_str = f"{prompt_tokens:<8} | {'-':<8} | {task.get('prompt_tps', 0):>6.1f}"
                elif stage == 'decode':
                    prog_str = f"{prompt_tokens:<8} | {tokens_gen:<8} | {tps:>6.1f}"
                elif status == 'completed':
                    prog_str = f"{prompt_tokens:<8} | {tokens_gen:<8} | {'-':>6}"
                else:
                    prog_str = f"{'-':<8} | {'-':<8} | {'-':>6}"

                stage_str = self.i18n.get(stage) if stage in ['prefill', 'decode', 'waiting'] else stage
                status_str = self.i18n.get(status) if status in ['running', 'completed', 'queued', 'failed'] else status
                line = f"{task_id:<5} | {status_str:<8} | {prog_str}"
                try:
                    self.stdscr.addstr(row, x + 2, line[:width - 4], curses.color_pair(status_color))
                except curses.error as e:
                    self.logger.debug(f"Tasks synthetic draw error: {e}")
                row += 1
    def _draw_footer(self, y: int, x: int, width: int):
        """Draw footer with 3-zone layout: Navigation | Status | Time"""
        # Phase 2: 3-zone footer layout
        # Zone 1 (Navigation): shortcuts
        # Zone 2 (Status): system status indicator
        # Zone 3 (Time): refresh rate and timestamp

        shortcuts = [
            "[+/-]Rate",
            "[R]Refresh",
            "[L]Log",
            "[M]Lang",
            "[Q]Quit"
        ]
        nav_str = " ".join(shortcuts)

        # Zone 2: System status with icon
        if self.api_consecutive_failures > 0:
            status_str = f"⚠ API ERR {self.api_consecutive_failures}"
            status_color = self.COLOR_ERROR
        elif self.system_errors > 0:
            status_str = f"⚠ SYS ERR {self.system_errors}"
            status_color = self.COLOR_ERROR
        else:
            status_str = "● All Systems OK"
            status_color = self.COLOR_SUCCESS

        # Zone 3: Time info
        if self.last_update:
            time_str = self.last_update.strftime('%H:%M:%S')
            right_str = f"Rate: {self.refresh_interval*1000:.0f}ms | {time_str}"
        else:
            right_str = f"Rate: {self.refresh_interval*1000:.0f}ms"

        # Draw footer border
        try:
            self.stdscr.addstr(y, x, '─' * width, curses.color_pair(self.COLOR_HEADER))

            # Zone 1: Navigation (left side)
            self.stdscr.addstr(y + 1, x + 2, nav_str, curses.color_pair(self.COLOR_HEADER))

            # Zone 2: Status (center)
            status_x = x + width // 2 - len(status_str) // 2
            self.stdscr.addstr(y + 1, status_x, status_str, curses.color_pair(status_color))

            # Zone 3: Time (right side)
            right_x = width - len(right_str) - 2
            if right_x > x + len(nav_str) + 5:
                self.stdscr.addstr(y + 1, right_x, right_str, curses.color_pair(self.COLOR_HEADER))
        except curses.error as e:
            self.logger.debug(f"Footer draw error: {e}")

    def refresh_system_data(self, cpu_collector: 'SystemCollector'):
        """Refresh system data (CPU, Memory, GPU) at fixed rate"""
        try:
            self.cpu_info = cpu_collector.get_cpu_info()
            self.memory_info = cpu_collector.get_memory_info()
            self.gpu_info = cpu_collector.get_gpu_info()

            # Update usage histories for line charts
            self.cpu_usage_history.append(self.cpu_info.get('usage', 0))
            self.memory_usage_history.append(self.memory_info.get('percent', 0))

            # Update per-GPU histories
            if self.gpu_info:
                # Initialize histories if GPU count changed
                while len(self.gpu_usage_history) < len(self.gpu_info):
                    self.gpu_usage_history.append(deque(maxlen=60))
                    self.gpu_mem_usage_history.append(deque(maxlen=60))
                # Trim histories if GPU count decreased
                while len(self.gpu_usage_history) > len(self.gpu_info):
                    self.gpu_usage_history.pop()
                    self.gpu_mem_usage_history.pop()

                # Update each GPU's history
                for i, gpu in enumerate(self.gpu_info):
                    self.gpu_usage_history[i].append(gpu.get('utilization', 0))
                    gpu_mem_used = gpu.get('memory_used', 0)
                    gpu_mem_total = gpu.get('memory_total', 1)
                    gpu_mem_percent = (gpu_mem_used / gpu_mem_total * 100) if gpu_mem_total > 0 else 0
                    self.gpu_mem_usage_history[i].append(gpu_mem_percent)

            self.last_successful_system = datetime.now()
            self.system_errors = 0
        except Exception as e:
            self.system_errors += 1
            self.logger.warning(f"System info error ({self.system_errors}): {e}")

    def refresh_api_data(self, server_client: 'LLAMAServerClient'):
        """Refresh API data (model info, stats, tasks) at user-defined rate"""
        # Periodically re-probe endpoints to discover new data
        self.endpoint_refresh_counter += 1
        if self.endpoint_refresh_counter >= self.endpoint_refresh_interval:
            self.endpoint_refresh_counter = 0
            try:
                server_client.update_data()
            except Exception as e:
                self.logger.debug(f"Endpoint refresh error: {e}")

        # Re-probe immediately on consecutive failures to recover from transient errors
        if self.api_consecutive_failures >= 3:
            try:
                server_client.update_data()
                self.logger.info("Re-probing endpoints after consecutive failures")
            except Exception as e:
                self.logger.debug(f"Endpoint re-probe error: {e}")

        # Get server data
        try:
            model_info = server_client.get_model_info()
            if model_info:
                self.model_info = model_info
                self.logger.debug(f"Updated model info: {model_info}")
        except Exception as e:
            self.api_errors += 1
            self.api_consecutive_failures += 1
            self.logger.warning(f"Model info API error ({self.api_consecutive_failures}): {e}")

        try:
            stats, curr_prompt, curr_eval, curr_time = server_client.get_fresh_stats(
                self._prev_prompt_count, self._prev_eval_count, self._prev_stats_time
            )
            if stats:
                self.stats = stats
                tps = stats.get('tokens_per_second', 0)
                self.tps_history.append(tps)
                self.logger.debug(f"Updated stats: tokens_per_second={tps:.1f}, running_requests={stats.get('running_requests', 0)}")
            else:
                # No stats available, record 0 TPS
                self.tps_history.append(0)
            # Update previous counters for next iteration
            if curr_prompt > 0:
                self._prev_prompt_count = curr_prompt
            if curr_eval > 0:
                self._prev_eval_count = curr_eval
            self._prev_stats_time = curr_time
        except Exception as e:
            self.api_errors += 1
            self.api_consecutive_failures += 1
            self.logger.warning(f"Stats API error ({self.api_consecutive_failures}): {e}")

        try:
            tasks, curr_prompt, curr_eval = server_client.get_fresh_tasks(
                self._prev_prompt_count, self._prev_eval_count
            )
            if tasks:
                # Calculate per-slot TPS based on n_decoded delta
                current_time = time.time()
                for task in tasks:
                    slot_id = task.get('id', 0)
                    n_decoded = task.get('tokens_generated', 0)
                    if slot_id in self._slot_tps_tracker:
                        prev_n_decoded, prev_time = self._slot_tps_tracker[slot_id]
                        time_delta = current_time - prev_time
                        if time_delta > 0:
                            delta = n_decoded - prev_n_decoded
                            if delta >= 0:
                                task['tps'] = delta / time_delta
                    self._slot_tps_tracker[slot_id] = (n_decoded, current_time)

                self.tasks = tasks
                self.logger.debug(f"Updated tasks: {len(tasks)} tasks")

                # Sum all slot TPS for real-time TPS (replace stats TPS)
                total_tps = sum(t.get('tps', 0) for t in tasks)
                if total_tps > 0 and self.stats:
                    self.stats['tokens_per_second'] = total_tps
                    self.tps_history.append(total_tps)
                    self.logger.debug(f"Updated TPS from slots: {total_tps:.1f}")
        except Exception as e:
            self.api_errors += 1
            self.api_consecutive_failures += 1
            self.logger.warning(f"Tasks API error ({self.api_consecutive_failures}): {e}")

        # If any API call succeeded, reset consecutive failure counter
        if self.model_info or self.stats or self.tasks:
            self.last_successful_api = datetime.now()
            self.api_consecutive_failures = 0

        # Phase 2: Trigger pulse animation on data refresh
        self._pulse_active = True
        threading.Timer(0.3, lambda: setattr(self, '_pulse_active', False)).start()

        self.last_update = datetime.now()
    
    def handle_input(self) -> bool:
        """Handle keyboard input. Returns False if should exit"""
        try:
            key = self.stdscr.getch()
            if key == -1:
                return True

            if key in (ord('q'), ord('Q')):
                return False
            elif key in (ord('r'), ord('R')):
                self.logger.debug("Manual refresh requested")
            elif key in (ord('l'), ord('L')):
                log_path = self.log_manager.get_log_path()
                self.logger.info(f"Log path: {log_path}")
            elif key in (ord('m'), ord('M')):
                new_lang = self.i18n.toggle()
                self.logger.info(f"Language switched to: {new_lang}")
            elif key == ord('+') or key == ord('='):
                # Increase refresh rate (decrease interval by 100ms, min 500ms)
                self.refresh_interval = max(0.5, self.refresh_interval - 0.1)
                self.logger.info(f"Refresh rate increased: {self.refresh_interval*1000:.0f}ms")
            elif key == ord('-') or key == ord('_'):
                # Decrease refresh rate (increase interval by 100ms, max 5s)
                self.refresh_interval = min(5.0, self.refresh_interval + 0.1)
                self.logger.info(f"Refresh rate decreased: {self.refresh_interval*1000:.0f}ms")
            elif key == ord(' '):
                self.detail_mode = not self.detail_mode
                self.logger.debug(f"Detail mode: {self.detail_mode}")
            elif key in (ord('h'), ord('H'), ord('?')):
                self.logger.info("Q=Quit, M=Lang, +/-=Rate, R=Refresh, L=Log")
        except curses.error as e:
            self.logger.debug(f"Input handling error: {e}")

        return True
    
    def draw(self):
        """Draw the entire interface - btop-inspired layout"""
        try:
            if self.ui_style == 'btop':
                self._draw_btop_ui()
                return

            height, width = self.stdscr.getmaxyx()

            # Use erase instead of clear to reduce flicker
            self.stdscr.erase()

            # Draw header
            self._draw_header(0, 0, width)

            # Layout:
            # Upper part (80%): Left (CPU/Mem/Model) | Right (GPU/Metrics)
            # Lower part (20%): Tasks (full width)

            # Calculate panel dimensions
            left_width = max(25, int(width * 0.40))
            right_width = width - left_width - 3
            right_x = left_width + 3

            # Content area (excluding header row 0, footer row height-2)
            content_top = 2
            content_bottom = height - 3
            total_height = content_bottom - content_top

            # Split: upper 80% for main info, lower 20% for tasks
            upper_height = max(12, int(total_height * 0.80))
            tasks_height = total_height - upper_height - 1

            # Left column in upper area: CPU | Memory | Model (equal height, 3 parts)
            # Phase 2: Enforce minimum heights for readability
            METRICS_MIN_HEIGHT = 8
            GPU_MIN_HEIGHT = 12
            raw_panel_height = upper_height // 3
            panel_height = max(raw_panel_height, METRICS_MIN_HEIGHT)
            cpu_height = panel_height
            mem_height = panel_height
            model_height = panel_height

            # Right column in upper area: GPU (80%) | Metrics (20%)
            # Phase 2: Enforce minimum GPU height
            gpu_height = max(int(upper_height * 0.80), GPU_MIN_HEIGHT)
            metrics_height = upper_height - gpu_height - 1

            # Draw upper left column
            self._draw_cpu_info(content_top, 1, left_width, cpu_height)
            mem_y = content_top + cpu_height + 1
            self._draw_memory_info(mem_y, 1, left_width, mem_height)
            model_y = mem_y + mem_height + 1
            self._draw_model_status(model_y, 1, left_width, model_height)

            # Draw upper right column: GPU (top) and Metrics (bottom)
            self._draw_gpu_info(content_top, right_x, right_width, gpu_height)
            metrics_y = content_top + gpu_height + 1
            self._draw_realtime_metrics(metrics_y, right_x, right_width, metrics_height)

            # Draw lower part: Tasks (full width)
            tasks_y = content_top + upper_height + 1
            self._draw_tasks(tasks_y, 1, width - 3, tasks_height)

            # Footer with refresh rate
            self._draw_footer(height - 2, 0, width)

            # Sync screen
            self.stdscr.refresh()
        except curses.error as e:
            self.logger.debug(f"Curses draw error: {e}")
    
    def run(self, cpu_collector: 'SystemCollector',
            server_client: 'LLAMAServerClient',
            refresh_interval: float = 1.0):
        """Main loop"""
        self.server_url = server_client.base_url
        self.refresh_interval = refresh_interval  # Initialize with passed value

        last_refresh = 0
        last_draw = 0
        min_draw_interval = 0.05  # Limit redraw rate to 20 FPS for smoother display

        while self.running:
            # Check for input
            if not self.handle_input():
                break

            current_time = time.time()
            data_changed = False

            # Refresh all data at user-defined rate
            if current_time - last_refresh >= self.refresh_interval:
                # Refresh system data (CPU, Memory, GPU)
                try:
                    self.refresh_system_data(cpu_collector)
                except Exception as e:
                    self.logger.warning(f"System refresh error: {e}")

                # Refresh API data (model, stats, tasks)
                try:
                    self.refresh_api_data(server_client)
                except Exception as e:
                    self.logger.warning(f"API refresh error: {e}")

                data_changed = True
                last_refresh = current_time

            # Draw interface only if data changed or enough time passed
            if data_changed or (current_time - last_draw >= min_draw_interval):
                try:
                    self.draw()
                    last_draw = current_time
                except curses.error as e:
                    self.logger.debug(f"Draw error: {e}")

            # Small sleep to prevent CPU spinning and ensure consistent timing
            time.sleep(0.01)


# ============================================================================
# Main Program
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='LLAMA.cpp Monitor - Real-time monitoring for llama-server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llama_monitor.py                           # Default settings
  python llama_monitor.py -u http://localhost:8080  # Custom URL
  python llama_monitor.py -l en -r 1                # English, 1s refresh
  python llama_monitor.py -d /var/log/llama-monitor # Custom log dir
        """
    )
    
    parser.add_argument(
        '-u', '--url',
        default='http://localhost:8000',
        help='llama-server URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '-r', '--rate',
        type=float,
        default=1.0,
        help='Refresh rate in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '-l', '--language',
        choices=['zh', 'en'],
        default='zh',
        help='Interface language: zh (Chinese) or en (English), default: zh'
    )
    
    parser.add_argument(
        '-d', '--log-dir',
        default=os.path.expanduser('~/llama-monitor/logs'),
        help='Log directory (default: ~/llama-monitor/logs)'
    )
    
    parser.add_argument(
        '-D', '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    return parser.parse_args()


def probe_server_url(url: str, log_manager: LogManager) -> str:
    """Probe and validate server URL"""
    logger = log_manager.logger
    
    client = LLAMAServerClient(url)
    
    # Test connection
    if client.test_connection():
        logger.info(f"Connection successful to {url}")
        client.close()
        return url
    
    logger.warning(f"Cannot connect to {url}, probing endpoints...")
    
    # Try to probe
    endpoints = client.probe_endpoints()
    if endpoints:
        logger.info(f"Found available endpoints: {list(endpoints.keys())}")
        client.close()
        return url
    
    client.close()
    
    # Ask user for input
    print(f"\n⚠️  Cannot connect to {url}")
    print("Please enter a valid llama-server URL (or press Enter to use default):")
    new_url = input("URL > ").strip()
    
    if not new_url:
        new_url = 'http://localhost:8000'
    
    # Validate new URL
    test_client = LLAMAServerClient(new_url)
    if test_client.test_connection():
        logger.info(f"Connected to {new_url}")
        test_client.close()
        return new_url
    
    test_client.close()
    logger.error(f"Failed to connect to {new_url}, using default")
    return 'http://localhost:8000'


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()
    
    # Initialize logging
    log_manager = LogManager(args.log_dir)
    logger = log_manager.logger
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    logger.info("=" * 60)
    logger.info("LLAMA.cpp Monitor starting")
    logger.info(f"URL: {args.url}")
    logger.info(f"Language: {args.language}")
    logger.info(f"Refresh rate: {args.rate}s")
    logger.info(f"Log directory: {args.log_dir}")
    
    # Initialize i18n
    i18n = I18n(args.language)
    
    # Probe server URL
    final_url = probe_server_url(args.url, log_manager)
    
    # Initialize components
    try:
        # System collector
        cpu_collector = SystemCollector()
        logger.info(f"System collector initialized (GPU: {cpu_collector.gpu_available})")
        
        # Server client
        server_client = LLAMAServerClient(final_url)
        
        # Initial probe
        endpoints = server_client.probe_endpoints()
        if endpoints:
            logger.info(f"Available endpoints: {list(endpoints.keys())}")
        else:
            logger.warning("No endpoints available, will retry during monitoring")
        
        # Run TUI
        def run_tui(stdscr):
            ui = TTUInterface(stdscr, i18n, log_manager)
            try:
                ui.run(cpu_collector, server_client, args.rate)
            except KeyboardInterrupt:
                pass
            finally:
                logger.info("TUI stopped")
        
        curses.wrapper(run_tui)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Cleanup
        try:
            cpu_collector.cleanup()
            server_client.close()
        except Exception as e:
            self.logger.debug(f"Cleanup error during shutdown: {e}")
        
        logger.info("LLAMA.cpp Monitor shutdown")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
