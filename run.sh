#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is not set"
    echo "Please create a .env file or set the environment variable"
    exit 1
fi

# Run the bot
python3 bot.py
