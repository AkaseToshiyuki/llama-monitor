# vLLM Monitoring Guide

vLLM's OpenAI-compatible server exposes Prometheus telemetry at `/metrics` by
default. llama-monitor auto-detects the `vllm:` metric namespace and reads:

- running and waiting requests;
- prompt and generation token counters;
- KV cache usage and prefix-cache hit rate;
- preemptions and an instantaneous generation rate derived from counter deltas.

## Start vLLM

```bash
export VLLM_API_KEY='replace-with-a-secret'
vllm serve your/model --api-key "$VLLM_API_KEY"
```

## Monitor a local server

```bash
llama-monitor -u http://localhost:8000
```

## Monitor a remote server

```bash
export VLLM_API_KEY='replace-with-a-secret'
llama-monitor \
  -u https://inference.example.com \
  --ca-cert ./internal-ca.pem
```

The token is read from `VLLM_API_KEY` by default and is never logged. Use
`--api-key-env NAME` to select a different variable. Avoid `--insecure` outside
short-lived diagnostics.

For remote URLs, local CPU/GPU collection is disabled in `--system auto` mode.
vLLM's KV cache metrics still remain visible. Use `--system local` only when the
monitor runs on the same host or local host telemetry is intentionally desired.
