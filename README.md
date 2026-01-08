# botmaster

A Telegram bot for remotely starting services on your machine. This bot provides a secure, password-protected interface to execute `start.sh` scripts in service directories.

## Features

- 🔐 Password authentication
- 🚀 Start services remotely via Telegram
- 📋 Automatic service discovery
- 🔄 Refresh service list
- 💬 Interactive button-based interface

## Setup

### Prerequisites

- Python 3.7 or higher
- A Telegram account
- Services with `start.sh` scripts in the parent directory

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Chuwee/botmaster.git
   cd botmaster
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a Telegram bot:
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the instructions
   - Copy the bot token provided by BotFather

4. Configure the bot:
   ```bash
   cp .env.example .env
   # Edit .env and add your bot token and password
   ```

   Or set environment variables directly:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export BOT_PASSWORD="your_secure_password_here"
   ```

### Running the Bot

```bash
python3 bot.py
```

Or make it executable and run:
```bash
chmod +x bot.py
./bot.py
```

## Usage

1. Start a conversation with your bot in Telegram
2. Send `/start` command
3. Enter the password you configured
4. Select a service from the list of buttons
5. The bot will execute the `start.sh` script for that service

### Available Commands

- `/start` - Authenticate and show available services
- `/help` - Show help message
- `/logout` - Log out from the bot

## Service Structure

The bot looks for services in the parent directory (`../`). Each service should be a directory containing a `start.sh` script.

Example structure:
```
/home/user/projects/
├── botmaster/          # This bot
│   ├── bot.py
│   └── requirements.txt
├── service1/           # Service 1
│   └── start.sh
├── service2/           # Service 2
│   └── start.sh
└── my-app/             # Service 3
    └── start.sh
```

The bot will discover and display: `service1`, `service2`, and `my-app`.

## Security Notes

- Keep your bot token secure and never commit it to version control
- Use a strong password for authentication
- The bot stores authenticated user IDs in memory (cleared on restart)
- Only authorized users can execute services after authentication
- Service execution has a 30-second timeout to prevent hanging

## Troubleshooting

**Bot doesn't start:**
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Verify your internet connection

**No services found:**
- Ensure service directories are in the parent directory (`../`)
- Verify each service has a `start.sh` file
- Check that `start.sh` files have execute permissions

**Service fails to start:**
- Check the error message in Telegram
- Verify the `start.sh` script works when run manually
- Check permissions on the service directory and script

## License

MIT