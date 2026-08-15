#!/bin/bash
# LLAMA.cpp Monitor - Quick Start Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
URL="http://localhost:8000"
RATE="1"
LANG="zh"
LOG_DIR="$HOME/llama-monitor/logs"
DEBUG=""
UI_STYLE="${LLAMA_MONITOR_UI:-${UI_STYLE:-btop}}"
BACKEND="auto"
SYSTEM_SCOPE="auto"
API_KEY_ENV="VLLM_API_KEY"
TLS_ARGS=()
export UI_STYLE

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -r|--rate)
            RATE="$2"
            shift 2
            ;;
        -l|--language)
            LANG="$2"
            shift 2
            ;;
        -d|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -D|--debug)
            DEBUG="-D"
            shift
            ;;
        --ui)
            UI_STYLE="$2"
            shift 2
            ;;
        --backend)
            BACKEND="$2"
            shift 2
            ;;
        --system)
            SYSTEM_SCOPE="$2"
            shift 2
            ;;
        --api-key-env)
            API_KEY_ENV="$2"
            shift 2
            ;;
        --ca-cert)
            TLS_ARGS=(--ca-cert "$2")
            shift 2
            ;;
        --insecure)
            TLS_ARGS=(--insecure)
            shift
            ;;
        -h|--help)
            echo "LLAMA.cpp Monitor - Quick Start"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -u, --url URL       llama-server URL (default: http://localhost:8000)"
            echo "  -r, --rate RATE     Refresh rate in seconds (default: 1)"
            echo "  -l, --language LANG Interface language: zh|en (default: zh)"
            echo "  -d, --log-dir DIR   Log directory (default: ~/llama-monitor/logs)"
            echo "  -D, --debug         Enable debug mode"
            echo "  --ui STYLE          Interface style: btop (default) or default"
            echo "  --backend TYPE      Backend: auto, llama.cpp, or vllm"
            echo "  --system SCOPE      Host metrics: auto, local, or off"
            echo "  --api-key-env NAME  Bearer-token environment variable"
            echo "  --ca-cert PATH      Custom HTTPS CA bundle"
            echo "  --insecure          Disable TLS verification (unsafe)"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                          # Default settings"
            echo "  $0 -u http://localhost:8080 # Custom URL"
            echo "  $0 -l en -r 1               # English, 1s refresh"
            echo "  $0 --ui default             # Use the legacy layout"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the monitor
export UI_STYLE
python3 llama_monitor.py \
    -u "$URL" \
    -r "$RATE" \
    -l "$LANG" \
    -d "$LOG_DIR" \
    --ui "$UI_STYLE" \
    --backend "$BACKEND" \
    --system "$SYSTEM_SCOPE" \
    --api-key-env "$API_KEY_ENV" \
    "${TLS_ARGS[@]}" \
    $DEBUG
