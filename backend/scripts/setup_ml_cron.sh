#!/bin/bash

# Setup ML Retraining Cron Job
# Configures a cron job to retrain Prophet ML models every Sunday at 3 AM

set -e

echo "🤖 Setting up ML Retraining Cron Job..."
echo "========================================"
echo ""

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Python executable in venv
PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
RETRAIN_SCRIPT="$PROJECT_ROOT/scripts/retrain_models.py"

# Check if Python executable exists
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "❌ Python executable not found at: $PYTHON_EXEC"
    echo "   Please ensure the virtual environment is set up."
    exit 1
fi

# Check if retrain script exists
if [ ! -f "$RETRAIN_SCRIPT" ]; then
    echo "❌ Retrain script not found at: $RETRAIN_SCRIPT"
    exit 1
fi

# Cron job schedule: Sunday 3 AM
CRON_SCHEDULE="0 3 * * 0"
CRON_JOB="$CRON_SCHEDULE $PYTHON_EXEC $RETRAIN_SCRIPT >> $PROJECT_ROOT/logs/ml_retrain.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "retrain_models.py"; then
    echo "⚠️  ML retraining cron job already exists"
    echo ""
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "retrain_models.py" || true
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Keeping existing cron job"
        exit 0
    fi
    
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "retrain_models.py" | crontab - || true
    echo "   ✓ Removed existing cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✅ ML retraining cron job added"
echo ""
echo "📋 Cron job details:"
echo "   Schedule:  Sunday 3 AM (0 3 * * 0)"
echo "   Command:   $PYTHON_EXEC $RETRAIN_SCRIPT"
echo "   Logs:      $PROJECT_ROOT/logs/ml_retrain.log"
echo ""
echo "📝 To view cron jobs:"
echo "   crontab -l"
echo ""
echo "📝 To remove cron job:"
echo "   crontab -l | grep -v 'retrain_models.py' | crontab -"
echo ""

