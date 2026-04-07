# LLAMA.cpp Monitor - Quick Reference

## 快速开始

```bash
# 1. 进入目录
cd ~/llama-monitor

# 2. 启动监控（默认设置）
./start.sh

# 3. 或者使用 Python 直接启动
python3 llama_monitor.py
```

## 常用命令

```bash
# 连接自定义服务器
python3 llama_monitor.py -u http://localhost:8080

# 英语界面，1 秒刷新
python3 llama_monitor.py -l en -r 1

# 调试模式
python3 llama_monitor.py -D

# 自定义日志目录
python3 llama_monitor.py -d /var/log/llama-monitor
```

## 快捷键

| 按键 | 功能 |
|------|------|
| **R** | 手动刷新 |
| **L** | 显示日志路径 |
| **M** | 切换语言（中/英） |
| **空格** | 切换详细/简洁模式 |
| **Q** | 快速退出 |
| **Ctrl+C** | 优雅退出 |

## 界面说明

```
┌─────────────────┬─────────────────┐
│   CPU 信息       │   GPU 信息       │
│   [████░░] 65%  │   [█████░] 80%  │
├─────────────────┼─────────────────┤
│   模型状态       │   实时指标       │
│   模型：llama-2 │   TPS: 45.2     │
├─────────────────┴─────────────────┤
│   任务列表                         │
│   001 | Running | Prefill | 62%   │
└───────────────────────────────────┘
```

## 任务状态

- **Prefill**: 提示词处理（显示进度%）
- **Decode**: 生成回复（显示 token 数）
- **Waiting**: 等待调度

## 日志管理

- 位置：`~/llama-monitor/logs/monitor.log`
- 最大大小：30MB
- 自动轮转：保留 5 个备份文件

## 故障排除

**无法连接服务器？**
- 检查 llama-server 是否运行
- 确认 URL 和端口正确
- 程序会自动探测可用端点

**GPU 信息不显示？**
- 确保安装 GPU 驱动 (NVIDIA 或 AMD ROCm)
- NVIDIA: `pip install nvidia-ml-py` + `nvidia-smi`
- AMD: `pip install amdsmi` + `rocm-smi`

**界面显示异常？**
- 确保终端支持 256 色
- 检查 `$TERM` 环境变量
- 尝试调整终端窗口大小

## 系统要求

- Python 3.8+
- Linux/macOS/Windows
- 终端支持 curses（标准 Linux/macOS 终端）

## 依赖

```bash
# 核心依赖（已包含）
psutil>=5.9.0
requests>=2.28.0

# 可选依赖（GPU 监控）
nvidia-ml-py>=11.0  # NVIDIA GPU
amdsmi              # AMD GPU (experimental)
```

## 版本

v1.0.0 - 2026-03-27
