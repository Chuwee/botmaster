# Usage Guide

## Quick Start

### 1. Set up your bot

First, create your Telegram bot:
1. Open Telegram and search for @BotFather
2. Send `/newbot` to create a new bot
3. Follow the prompts to choose a name and username
4. BotFather will give you a token - save this!

### 2. Configure the bot

Create a `.env` file in the botmaster directory:

```bash
cd /path/to/botmaster
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your configuration:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_PASSWORD=MySecurePassword123
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the bot

Simple method:
```bash
./run.sh
```

Or directly:
```bash
python3 bot.py
```

Or with environment variables:
```bash
TELEGRAM_BOT_TOKEN="your_token" BOT_PASSWORD="your_password" python3 bot.py
```

## Using the Bot in Telegram

1. **Start the bot**: Find your bot in Telegram and send `/start`
2. **Authenticate**: Enter the password you configured
3. **Select a service**: Click on a service button to start it
4. **View results**: The bot will show the output of the service

### Commands

- `/start` - Authenticate and show the service menu
- `/help` - Display help information
- `/logout` - Log out and require re-authentication

## Setting Up Services

Each service should be a directory in the parent folder with a `start.sh` script:

```
/home/user/projects/
├── botmaster/          # The bot
├── myapp/             # Your service
│   └── start.sh       # Service startup script
└── webserver/         # Another service
    └── start.sh
```

### Example start.sh scripts

**Simple service:**
```bash
#!/bin/bash
echo "Starting my application..."
cd /path/to/myapp
./myapp &
echo "Application started!"
```

**Docker service:**
```bash
#!/bin/bash
echo "Starting Docker containers..."
docker-compose up -d
echo "Containers started!"
```

**Node.js service:**
```bash
#!/bin/bash
echo "Starting Node.js application..."
cd /path/to/app
npm start &
echo "Node.js app started!"
```

**Python service:**
```bash
#!/bin/bash
echo "Starting Python service..."
cd /path/to/service
source venv/bin/activate
python main.py &
echo "Python service started!"
```

### Tips for start.sh scripts

1. **Make them executable:**
   ```bash
   chmod +x start.sh
   ```

2. **Add error handling:**
   ```bash
   #!/bin/bash
   set -e  # Exit on error
   echo "Starting service..."
   # Your commands here
   ```

3. **Use absolute paths** when possible to avoid issues

4. **Background processes**: Use `&` to run services in the background

5. **Check if already running:**
   ```bash
   #!/bin/bash
   if pgrep -f "myapp" > /dev/null; then
       echo "Service already running!"
       exit 0
   fi
   # Start service...
   ```

## Running as a System Service

To run the bot automatically on system startup, create a systemd service:

### Create service file

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Service Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/botmaster
Environment="TELEGRAM_BOT_TOKEN=your_token_here"
Environment="BOT_PASSWORD=your_password_here"
ExecStart=/usr/bin/python3 /home/yourusername/botmaster/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### Check status

```bash
sudo systemctl status telegram-bot
```

### View logs

```bash
sudo journalctl -u telegram-bot -f
```

## Security Best Practices

1. **Use a strong password**: Choose a complex password for bot authentication
2. **Keep token secret**: Never commit `.env` file or expose your bot token
3. **Limit service scripts**: Only put trusted scripts in service directories
4. **Use firewall**: Ensure your system firewall is properly configured
5. **Regular updates**: Keep python-telegram-bot and Python up to date
6. **User permissions**: Run the bot with limited user permissions
7. **Review scripts**: Regularly audit start.sh scripts for security issues

## Troubleshooting

### Bot doesn't respond

- Check if the bot is running: `ps aux | grep bot.py`
- Check logs for errors
- Verify your bot token is correct
- Ensure your internet connection works

### Services not showing up

- Ensure service directories are in the parent directory (`../`)
- Check that `start.sh` files exist and are executable
- Review bot logs for discovery errors

### Service fails to start

- Run the `start.sh` script manually to test
- Check script permissions: `ls -la /path/to/service/start.sh`
- Review the error message shown by the bot
- Check service logs if applicable

### Authentication issues

- Verify the password in `.env` or environment variable
- Check for typos in the password
- Use `/logout` and try again

## Advanced Configuration

### Custom service directory

Modify `bot.py` to change the service directory:

```python
SERVICES_DIR = Path('/custom/path/to/services')
```

### Change timeout

Modify the timeout value in `bot.py`:

```python
result = subprocess.run(
    ['bash', 'start.sh'],
    cwd=service_path.parent,
    capture_output=True,
    text=True,
    timeout=60  # Change from 30 to 60 seconds
)
```

### Persistent authentication

Currently, authentication is stored in memory and cleared on bot restart. For persistent authentication, you could implement a database or file-based storage.

## Examples

### Example interaction

```
User: /start
Bot: 🔐 Welcome to the Service Bot!
     Please enter the password to continue:

User: MySecurePassword123
Bot: ✅ Authentication successful!
     🚀 Choose a service to start:
     [▶️ myapp] [▶️ webserver] [🔄 Refresh]

User: [clicks "▶️ myapp"]
Bot: ⏳ Starting service 'myapp'...
     ✅ Service 'myapp' started!
     
     Output:
     ```
     Starting my application...
     Application started!
     ```
     
     🚀 Choose a service to start:
     [▶️ myapp] [▶️ webserver] [🔄 Refresh]
```

## Updating the Bot

To update the bot:

```bash
cd /path/to/botmaster
git pull
pip install -r requirements.txt --upgrade
# Restart the bot (if running as service)
sudo systemctl restart telegram-bot
```
