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
        -h|--help)
            echo "LLAMA.cpp Monitor - Quick Start"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -u, --url URL       llama-server URL (default: http://localhost:8000)"
            echo "  -r, --rate RATE     Refresh rate in seconds (default: 2)"
            echo "  -l, --language LANG Interface language: zh|en (default: zh)"
            echo "  -d, --log-dir DIR   Log directory (default: ~/llama-monitor/logs)"
            echo "  -D, --debug         Enable debug mode"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                          # Default settings"
            echo "  $0 -u http://localhost:8080 # Custom URL"
            echo "  $0 -l en -r 1               # English, 1s refresh"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the monitor
python3 llama_monitor.py \
    -u "$URL" \
    -r "$RATE" \
    -l "$LANG" \
    -d "$LOG_DIR" \
    $DEBUG
