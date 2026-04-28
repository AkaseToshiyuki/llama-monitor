# LLAMA.cpp Monitor

[English](#english) | [中文](#中文)

---

## 中文

### 简介

基于 Python 的 LLAMA.cpp (llama-server) 实时状态监测工具，提供美观的 256 色彩色 TUI 界面。

### 特性

- **系统监控**: CPU/GPU 占用率、频率、显存、温度、风扇、功率
- **模型状态**: 模型名称、上下文大小、批处理、运行状态
- **实时指标**: Token 生成速率、缓存命中率
- **任务列表**: 活跃任务、输入/输出 tokens
- **多语言**: 中文/英语切换 (按 `M`)
- **可调刷新率**: `+`/`-` 键调整刷新速度
- **日志记录**: 自动轮转，最大 30MB
- **状态图标**: ▶ ● ○ ✓ ✗ 等图标直观区分任务阶段
- **脉冲动画**: 数据更新时当前值闪烁提示变化
- **3区布局**: 面板标题带下划线，底部3区状态栏（Navigation | Status | Time）

### 安装

```bash
pip install -r requirements.txt
# GPU 监控 (NVIDIA 或 AMD ROCm)
pip install nvidia-ml-py  # NVIDIA GPU
# pip install amdsmi      # AMD GPU (experimental)
```

> **注意**: 支持 NVIDIA GPU (通过 pynvml) 和 AMD GPU (通过 amdsmi，实验性支持)。Apple Metal 暂不支持。

### 快速开始

```bash
# 启动监控
python llama_monitor.py

# 连接自定义地址
python llama_monitor.py -u http://localhost:8080

# 英语界面，1 秒刷新
python llama_monitor.py -l en -r 1
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-u, --url` | llama-server 地址 | http://localhost:8000 |
| `-r, --rate` | 刷新频率（秒） | 1.0 |
| `-l, --language` | 界面语言: `zh` 或 `en` | zh |
| `-d, --log-dir` | 日志目录 | ~/llama-monitor/logs |
| `-D, --debug` | 启用调试模式 | - |

### 快捷键

| 键位 | 功能 |
|------|------|
| `+` / `-` | 增加/减少刷新频率 |
| `R` | 手动刷新 |
| `L` | 显示日志路径 |
| `M` | 切换语言（中/英） |
| `空格` | 切换详细/简洁模式 |
| `Q` | 退出 |

### 故障排除

**无法连接服务器**
- 确认 llama-server 已启动并使用 `--metrics` 参数
- 检查 URL 和端口是否正确

**GPU 监控不可用**
- 确保安装了 `nvidia-ml-py`
- 运行 `nvidia-smi` 验证 GPU

---

## English

### Overview

A Python-based real-time monitoring tool for LLAMA.cpp (llama-server) with beautiful 256-color TUI interface.

### Features

- **System Monitoring**: CPU/GPU usage, frequency, VRAM, temperature, fan, power
- **Model Status**: Model name, context size, batch size, running state
- **Real-time Metrics**: Token generation rate, cache hit rate
- **Task List**: Active tasks, input/output tokens
- **Multi-language**: Chinese/English toggle (press `M`)
- **Adjustable Refresh**: `+`/`-` keys to change refresh speed
- **Log Management**: Auto rotation, 30MB max
- **Status Icons**: ▶ ● ○ ✓ ✗ for intuitive task stage recognition
- **Pulse Animation**: Current values blink on data update
- **3-Zone Layout**: Underlined panel titles, 3-zone footer (Navigation | Status | Time)

### Installation

```bash
pip install -r requirements.txt
# GPU monitoring (NVIDIA or AMD ROCm)
pip install nvidia-ml-py  # NVIDIA GPU
# pip install amdsmi      # AMD GPU (experimental)
```

> **Note**: Supports NVIDIA GPU (via pynvml) and AMD GPU (via amdsmi, experimental). Apple Metal is not yet supported.

### Quick Start

```bash
# Start monitor
python llama_monitor.py

# Connect to custom address
python llama_monitor.py -u http://localhost:8080

# English interface, 1 second refresh
python llama_monitor.py -l en -r 1
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-u, --url` | llama-server URL | http://localhost:8000 |
| `-r, --rate` | Refresh rate (seconds) | 1.0 |
| `-l, --language` | Interface language: `zh` or `en` | zh |
| `-d, --log-dir` | Log directory | ~/llama-monitor/logs |
| `-D, --debug` | Enable debug mode | - |

### Keyboard Shortcuts

| Key | Function |
|-----|----------|
| `+` / `-` | Increase/decrease refresh rate |
| `R` | Manual refresh |
| `L` | Show log path |
| `M` | Toggle language (zh/en) |
| `Space` | Toggle detail/simple mode |
| `Q` | Quit |

### Troubleshooting

**Cannot connect to server**
- Ensure llama-server is running with `--metrics` flag
- Check URL and port are correct

**GPU monitoring not available**
- Ensure `nvidia-ml-py` is installed
- Run `nvidia-smi` to verify GPU

### Server Requirements

The llama-server must be started with the `--metrics` flag:

```bash
llama-server --model ./models/your-model.gguf --metrics
```

See [LLAMA_SERVER_GUIDE.md](LLAMA_SERVER_GUIDE.md) for detailed server parameters.

---

## License / 许可证

MIT License