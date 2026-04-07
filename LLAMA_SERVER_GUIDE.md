# LLAMA.cpp Server 启动参数指南 / Server Startup Guide

本监控工具依赖 llama-server 的特定启动参数来获取完整数据。
This monitor tool depends on specific llama-server startup parameters for complete data.

---

## 必需参数 / Required Parameters

### 启用 Metrics 端点 / Enable Metrics Endpoint

```bash
llama-server --metrics
```

`--metrics` 参数会启用 `/metrics` 端点，提供 Prometheus 格式的实时指标：
- 实时 TPS (tokens per second)
- 正在处理的请求数
- Prompt tokens 和生成 tokens 计数
- 缓存命中率
- 任务阶段检测（prefill/decode）

The `--metrics` flag enables the `/metrics` endpoint providing Prometheus-format real-time metrics:
- Real-time TPS (tokens per second)
- Number of running requests
- Prompt and generation token counts
- Cache hit rate
- Task stage detection (prefill/decode)

---

## 推荐启动命令 / Recommended Commands

### 基本监控模式 / Basic Monitoring

```bash
llama-server \
  --model ./models/your-model.gguf \
  --ctx-size 4096 \
  --batch-size 512 \
  --metrics
```

### 生产环境推荐 / Production Environment

```bash
llama-server \
  --model ./models/your-model.gguf \
  --ctx-size 4096 \
  --batch-size 512 \
  --threads 8 \
  --threads-batch 8 \
  --parallel 4 \
  --host 0.0.0.0 \
  --port 8080 \
  --metrics
```

### GPU 加速 (CUDA) / GPU Acceleration

```bash
llama-server \
  --model ./models/your-model.gguf \
  --ctx-size 4096 \
  --batch-size 512 \
  --n-gpu-layers 35 \
  --metrics
```

---

## 参数说明 / Parameter Reference

| 参数 / Parameter | 说明 / Description | 监控依赖 / Monitor Dependency |
|------------------|-------------------|------------------------------|
| `--metrics` | 启用 `/metrics` 端点 / Enable `/metrics` endpoint | **必需 / Required** |
| `--port` | 服务器端口 / Server port (默认/default: 8080) | 可选 / Optional |
| `--host` | 监听地址 / Listen address (默认/default: 127.0.0.1) | 可选 / Optional |
| `--ctx-size` | 上下文大小 / Context size | 可选 / Optional |
| `--batch-size` | 批处理大小 / Batch size | 可选 / Optional |
| `--parallel` | 并行请求数 / Parallel requests | 可选 / Optional |
| `--n-gpu-layers` | GPU 加速层数 / GPU layers | 可选 / Optional |

---

## 监控工具连接 / Connect Monitor Tool

```bash
python llama_monitor.py -u http://localhost:8080
```

---

## 验证端点 / Verify Endpoint

```bash
curl http://localhost:8080/metrics
```

正常情况下应返回 Prometheus 格式的指标数据。
Should return Prometheus-format metrics data when working correctly.

---

## 故障排除 / Troubleshooting

### 问题：监控显示 "API Error"
### Issue: Monitor shows "API Error"

- 确认 llama-server 已启动并启用 `--metrics`
- 检查防火墙/端口是否开放
- Ensure llama-server is running with `--metrics` enabled
- Check firewall/port settings

### 问题：TPS 始终为 0
### Issue: TPS always shows 0

- 确认有正在运行的请求
- 检查 `/metrics` 端点是否正常返回数据
- Ensure there are running requests
- Check if `/metrics` endpoint returns data correctly

### 问题：任务列表为空
### Issue: Task list is empty

- 正常状态下没有请求时任务列表为空是预期行为
- 发送请求后应能看到活跃任务
- Empty task list is normal when no requests are running
- Active tasks should appear after sending requests
