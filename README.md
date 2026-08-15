# llama-monitor

[English](#english) | [中文](#中文)

---

## 中文

### 简介

基于 Python 的 LLAMA.cpp (llama-server) 与 vLLM 实时状态监测工具，提供受 **btop** 启发的自适应 256 色彩色 TUI 界面。

### 特性

- **系统监控**: CPU/GPU 占用率、频率、显存、温度、风扇、功率
- **模型状态**: 模型名称、上下文大小、批处理、运行状态
- **实时指标**: Token 生成速率、缓存命中率
- **vLLM 支持**: 自动识别 vLLM `/metrics`，显示并发请求、队列、KV Cache 使用率、Prefix Cache 命中率与即时 TPS
- **任务列表**: 活跃任务、输入/输出 tokens
- **多语言**: 中文/英语切换 (按 `M`)
- **可调刷新率**: `+`/`-` 键调整刷新速度
- **日志记录**: 自动轮转，最大 30MB
- **状态图标**: ▶ ● ○ ✓ ✗ 等图标直观区分任务阶段
- **低开销刷新**: 仅在数据或交互变化时重绘，减少空闲 CPU 占用
- **安全采集边界**: 限制远程响应体与展示队列行数，避免异常遥测耗尽本机资源
- **Btop 风格仪表盘**: 默认彩色双栏卡片、资源条、迷你历史曲线与活动槽位栏
- **自适应布局**: 按终端尺寸收缩；尺寸不足时给出明确提示而非错位绘制

### GPU 支持说明

| GPU 类型 | 支持状态 | 依赖 |
|---------|---------|------|
| **NVIDIA** | ✅ 稳定 | `nvidia-ml-py` (pip install) |
| **AMD** | ⚠️ 实验性 | `amdsmi` (pip install, experimental) |
| **Apple Metal** | ⚠️ 实验性 | macOS + ctypes（无需额外依赖） |
| **Intel** | ⚠️ 实验性 | Linux sysfs（无需额外依赖） |

> **注意**: NVIDIA GPU 为稳定支持。AMD / Apple Metal / Intel GPU 为实验性支持，可能在不同环境下表现不一致。

### 安装

```bash
pip install -e .             # 核心功能
pip install -e '.[nvidia]'   # NVIDIA GPU（可选）
# pip install -e '.[amd]'    # AMD GPU（实验性）
```

### 快速开始

```bash
# 启动监控
python llama_monitor.py

# 连接自定义地址
python llama_monitor.py -u http://localhost:8080

# 英语界面，1 秒刷新
python llama_monitor.py -l en -r 1

# 使用传统布局（默认是 btop 风格）
python llama_monitor.py --ui default

# 监控 vLLM（vLLM 默认暴露 /metrics）
python llama_monitor.py -u http://localhost:8000

# 带 API Key 的远程 vLLM
export VLLM_API_KEY='your-token'
llama-monitor -u https://inference.example.com --ca-cert ./ca.pem
```

远程 URL 在 `--system auto` 下不会显示本机 CPU/GPU，以免把监控器所在机器误认为推理服务器。只有需要同时查看本机资源时才使用 `--system local`。

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-u, --url` | llama-server 地址 | http://localhost:8000 |
| `-r, --rate` | 刷新频率（秒） | 1.0 |
| `-l, --language` | 界面语言: `zh` 或 `en` | zh |
| `-d, --log-dir` | 日志目录 | ~/llama-monitor/logs |
| `-D, --debug` | 启用调试模式 | - |
| `--ui` | 界面风格：`btop`（默认）或 `default` | `btop` |
| `--backend` | 后端：`auto`、`llama.cpp` 或 `vllm` | `auto` |
| `--system` | 主机指标：`auto`、`local` 或 `off` | `auto` |
| `--api-key-env` | 保存 Bearer Token 的环境变量名称 | `VLLM_API_KEY` |
| `--ca-cert` | HTTPS 自定义 CA 文件 | - |
| `--insecure` | 关闭 TLS 证书校验（不推荐） | - |

### 快捷键

| 键位 | 功能 |
|------|------|
| `+` / `-` | 增加/减少刷新频率 |
| `R` | 手动刷新 |
| `L` | 显示日志路径 |
| `M` | 切换语言（中/英） |
| `空格` | 切换详细/简洁模式 |
| `U` | 切换 btop / 传统布局 |
| `Q` | 退出 |

### 故障排除

**无法连接服务器**
- 确认 llama-server 已启动并使用 `--metrics` 参数；vLLM 默认暴露此端点
- 检查 URL 和端口是否正确

**GPU 监控不可用**
- 确保已安装对应 GPU 的依赖包
- NVIDIA: `pip install nvidia-ml-py` + `nvidia-smi`
- AMD: `pip install amdsmi` (实验性)
- Intel / Apple Metal: 无需额外依赖（自动检测）

---

## English

### Overview

A real-time monitor for LLAMA.cpp (llama-server) and vLLM with an adaptive, **btop-inspired** 256-color TUI.

### Features

- **System Monitoring**: CPU/GPU usage, frequency, VRAM, temperature, fan, power
- **Model Status**: Model name, context size, batch size, running state
- **Real-time Metrics**: Token generation rate, cache hit rate
- **vLLM support**: Auto-detects vLLM `/metrics` and shows running/queued requests, KV Cache use, Prefix Cache hit rate, and instantaneous TPS
- **Task List**: Active tasks, input/output tokens
- **Multi-language**: Chinese/English toggle (press `M`)
- **Adjustable Refresh**: `+`/`-` keys to change refresh speed
- **Log Management**: Auto rotation, 30MB max
- **Status Icons**: ▶ ● ○ ✓ ✗ for intuitive task stage recognition
- **Low-overhead refresh**: Redraws only for new data or interaction, avoiding idle CPU use
- **Bounded collection**: Caps remote response bodies and displayed queue rows to contain malformed telemetry
- **Btop dashboard**: Colour-coded dual-column panels, resource bars, mini history graphs, and an active-slot strip by default
- **Responsive layout**: Fits to terminal dimensions and gives a clear resize message when the terminal is too small

### GPU Support

| GPU Type | Status | Dependencies |
|----------|--------|--------------|
| **NVIDIA** | ✅ Stable | `nvidia-ml-py` (pip install) |
| **AMD** | ⚠️ Experimental | `amdsmi` (pip install, experimental) |
| **Apple Metal** | ⚠️ Experimental | macOS + ctypes (no extra deps) |
| **Intel** | ⚠️ Experimental | Linux sysfs (no extra deps) |

> **Note**: NVIDIA GPU is stable. AMD / Apple Metal / Intel GPU are experimental and may behave inconsistently across environments.

### Installation

```bash
pip install -e .             # Core monitor
pip install -e '.[nvidia]'   # NVIDIA GPU (optional)
# pip install -e '.[amd]'    # AMD GPU (experimental)
```

### Quick Start

```bash
# Start monitor
python llama_monitor.py

# Connect to custom address
python llama_monitor.py -u http://localhost:8080

# English interface, 1 second refresh
python llama_monitor.py -l en -r 1

# Use the legacy layout (btop is the default)
python llama_monitor.py --ui default

# Monitor vLLM (it exposes /metrics by default)
python llama_monitor.py -u http://localhost:8000

# Remote vLLM protected by an API key
export VLLM_API_KEY='your-token'
llama-monitor -u https://inference.example.com --ca-cert ./ca.pem
```

With `--system auto`, remote URLs do not show local CPU/GPU metrics. This prevents the monitor host from being mistaken for the inference server. Use `--system local` only when that is intentional.

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-u, --url` | llama-server URL | http://localhost:8000 |
| `-r, --rate` | Refresh rate (seconds) | 1.0 |
| `-l, --language` | Interface language: `zh` or `en` | zh |
| `-d, --log-dir` | Log directory | ~/llama-monitor/logs |
| `-D, --debug` | Enable debug mode | - |
| `--ui` | Interface style: `btop` (default) or `default` | `btop` |
| `--backend` | Backend: `auto`, `llama.cpp`, or `vllm` | `auto` |
| `--system` | Host metrics: `auto`, `local`, or `off` | `auto` |
| `--api-key-env` | Environment variable containing the Bearer token | `VLLM_API_KEY` |
| `--ca-cert` | Custom CA bundle for HTTPS | - |
| `--insecure` | Disable TLS verification (not recommended) | - |

### Keyboard Shortcuts

| Key | Function |
|-----|----------|
| `+` / `-` | Increase/decrease refresh rate |
| `R` | Manual refresh |
| `L` | Show log path |
| `M` | Toggle language (zh/en) |
| `Space` | Toggle detail/simple mode |
| `U` | Toggle btop / legacy layout |
| `Q` | Quit |

### Troubleshooting

**Cannot connect to server**
- Ensure llama-server is running with `--metrics`; vLLM exposes this endpoint by default
- Check URL and port are correct

**GPU monitoring not available**
- Ensure the appropriate GPU package is installed
- NVIDIA: `pip install nvidia-ml-py` + `nvidia-smi`
- AMD: `pip install amdsmi` (experimental)
- Intel / Apple Metal: No extra deps needed (auto-detected)

### Server Requirements

The llama-server must be started with the `--metrics` flag:

```bash
llama-server --model ./models/your-model.gguf --metrics
```

vLLM exposes `/metrics` by default:

```bash
vllm serve your/model --api-key "$VLLM_API_KEY"
```

See [LLAMA_SERVER_GUIDE.md](LLAMA_SERVER_GUIDE.md) for llama.cpp and
[VLLM_GUIDE.md](VLLM_GUIDE.md) for vLLM setup details.

---

## License / 许可证

[MIT](LICENSE)
