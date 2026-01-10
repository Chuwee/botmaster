# Quick Start Guide

## 1. Get Your Bot Token
1. Open Telegram, search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the token provided

## 2. Configure
```bash
cd botmaster
cp .env.example .env
# Edit .env and add your token and password
```

## 3. Install & Run
```bash
pip install -r requirements.txt
./run.sh
```

## 4. Use the Bot
1. Find your bot in Telegram
2. Send `/start`
3. Enter your password
4. Click a service button to start it

## File Structure
```
/your/projects/
├── botmaster/          # This bot
│   ├── bot.py
│   └── requirements.txt
├── myapp/             # Your service
│   └── start.sh       # Make it executable
└── another-service/   # Another service
    └── start.sh
```

## Commands
- `/start` - Authenticate & show services
- `/help` - Show help
- `/logout` - Log out

## Troubleshooting
- **No services found?** Ensure `start.sh` files exist in parent directories
- **Service won't start?** Test `bash start.sh` manually first
- **Bot not responding?** Check your token and internet connection

For detailed documentation, see README.md and USAGE.md
