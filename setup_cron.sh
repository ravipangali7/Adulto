#!/bin/bash

# Video Scheduler Cron Setup Script
# Run this script to set up automatic video publishing

echo "Setting up video scheduler cron job..."

# Get current directory
PROJECT_DIR=$(pwd)
echo "Project directory: $PROJECT_DIR"

# Check if virtual environment exists
if [ -d "env" ]; then
    PYTHON_PATH="$PROJECT_DIR/env/bin/python"
elif [ -d "venv" ]; then
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
else
    echo "Virtual environment not found. Please specify Python path:"
    read -p "Enter full path to Python: " PYTHON_PATH
fi

echo "Python path: $PYTHON_PATH"

# Create cron job
CRON_JOB="* * * * * cd $PROJECT_DIR && $PYTHON_PATH manage.py publish_scheduled_videos >> $PROJECT_DIR/scheduler.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "The video scheduler will run every minute."
echo "Logs will be saved to: $PROJECT_DIR/scheduler.log"
echo ""
echo "To view logs: tail -f $PROJECT_DIR/scheduler.log"
echo "To remove cron job: crontab -e (then delete the line)"
echo ""
echo "Testing the command..."
cd $PROJECT_DIR && $PYTHON_PATH manage.py publish_scheduled_videos
