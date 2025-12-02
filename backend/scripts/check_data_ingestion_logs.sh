#!/bin/bash
# Script to check Data Ingestion Agent logs
# 
# This script helps you monitor the Data Ingestion Agent to ensure it's correctly
# embedding data from MongoDB collections into ChromaDB.
#
# Usage:
#   ./check_data_ingestion_logs.sh [options]
#
# Options:
#   -f, --follow    Follow log output in real-time (like tail -f)
#   -n, --lines N    Show last N lines (default: 50)
#   -g, --grep TEXT Filter logs by text (e.g., "historical_rides", "embedding", "error")
#   -h, --help       Show this help message

# Default values
FOLLOW=false
LINES=50
GREP_FILTER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    -n|--lines)
      LINES="$2"
      shift 2
      ;;
    -g|--grep)
      GREP_FILTER="$2"
      shift 2
      ;;
    -h|--help)
      echo "Data Ingestion Agent Log Checker"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  -f, --follow    Follow log output in real-time"
      echo "  -n, --lines N   Show last N lines (default: 50)"
      echo "  -g, --grep TEXT Filter logs by text"
      echo "  -h, --help      Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Show last 50 lines"
      echo "  $0 -f                                 # Follow logs in real-time"
      echo "  $0 -n 100                             # Show last 100 lines"
      echo "  $0 -g 'historical_rides'              # Filter for historical_rides"
      echo "  $0 -g 'embedding' -f                 # Follow logs filtered by 'embedding'"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Check if Data Ingestion Agent is running
if ! pgrep -f "data_ingestion.py" > /dev/null; then
    echo "⚠️  Data Ingestion Agent is not running!"
    echo ""
    echo "To start it, run:"
    echo "  cd backend && python app/agents/data_ingestion.py"
    echo ""
    echo "Or run it in the background:"
    echo "  cd backend && nohup python app/agents/data_ingestion.py > /tmp/data_ingestion.log 2>&1 &"
    echo ""
    exit 1
fi

echo "✓ Data Ingestion Agent is running"
echo ""

# Determine log file location
# Check in order: backend/logs (from start.sh), /tmp, current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
LOG_FILE=""
if [ -f "$BACKEND_DIR/logs/data_ingestion.log" ]; then
    LOG_FILE="$BACKEND_DIR/logs/data_ingestion.log"
elif [ -f "/tmp/data_ingestion.log" ]; then
    LOG_FILE="/tmp/data_ingestion.log"
elif [ -f "backend/logs/data_ingestion.log" ]; then
    LOG_FILE="backend/logs/data_ingestion.log"
elif [ -f "backend/data_ingestion.log" ]; then
    LOG_FILE="backend/data_ingestion.log"
elif [ -f "data_ingestion.log" ]; then
    LOG_FILE="data_ingestion.log"
fi

if [ -n "$LOG_FILE" ]; then
    echo "📄 Reading from log file: $LOG_FILE"
    echo ""
    
    if [ -n "$GREP_FILTER" ]; then
        if [ "$FOLLOW" = true ]; then
            tail -f "$LOG_FILE" | grep --color=always "$GREP_FILTER"
        else
            tail -n "$LINES" "$LOG_FILE" | grep --color=always "$GREP_FILTER"
        fi
    else
        if [ "$FOLLOW" = true ]; then
            tail -f "$LOG_FILE"
        else
            tail -n "$LINES" "$LOG_FILE"
        fi
    fi
else
    echo "⚠️  No log file found. The agent might be running in foreground."
    echo ""
    echo "To capture logs, use the backend start script:"
    echo "  cd backend && ./start.sh"
    echo ""
    echo "Or manually run with:"
    echo "  cd backend && nohup python app/agents/data_ingestion.py > logs/data_ingestion.log 2>&1 &"
    echo ""
    echo "Or check the terminal where you started the agent."
    echo ""
    echo "Current agent process info:"
    ps aux | grep "data_ingestion.py" | grep -v grep
fi

