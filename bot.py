#!/usr/bin/env python3
"""
Telegram Bot for starting services remotely.
This bot authenticates users with a password and allows them to start services
located in the parent directory that have a start.sh script.
"""

import os
import subprocess
import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_PASSWORD = 1

# Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
PASSWORD = os.environ.get('BOT_PASSWORD', 'changeme')
SERVICES_DIR = Path(__file__).parent.parent  # Parent directory

# Store authenticated users
# Note: Using in-memory storage means authentication state is lost on bot restart.
# For production use, consider implementing persistent storage with session management.
authenticated_users = set()


def escape_html(text: str) -> str:
    """Escape special characters for HTML formatting."""
    # Escape HTML entities for safe display in parse_mode='HTML'
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def is_safe_service_name(service_name: str) -> bool:
    """
    Validate that service_name doesn't contain path traversal sequences.
    Only allows alphanumeric characters, hyphens, underscores, and dots.
    Prevents directory traversal attacks.
    """
    if not service_name:
        return False
    # Reject path traversal sequences
    if '..' in service_name or '/' in service_name or '\\' in service_name:
        return False
    # Only allow safe characters: alphanumeric, hyphen, underscore, dot
    import re
    if not re.match(r'^[a-zA-Z0-9._-]+$', service_name):
        return False
    return True


def discover_services():
    """
    Discover services in the parent directory.
    A service is a directory that contains a start.sh script.
    """
    services = []
    if not SERVICES_DIR.exists():
        logger.warning(f"Services directory {SERVICES_DIR} does not exist")
        return services
    
    for item in SERVICES_DIR.iterdir():
        if item.is_dir():
            start_script = item / 'start.sh'
            if start_script.exists() and start_script.is_file():
                services.append(item.name)
                logger.info(f"Found service: {item.name}")
    
    return sorted(services)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /start command."""
    user_id = update.effective_user.id
    
    # Check if user is already authenticated
    if user_id in authenticated_users:
        await show_services(update, context)
        return ConversationHandler.END
    
    # Ask for password
    await update.message.reply_text(
        "🔐 Welcome to the Service Bot!\n\n"
        "Please enter the password to continue:"
    )
    return WAITING_PASSWORD


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Check if the provided password is correct."""
    user_id = update.effective_user.id
    provided_password = update.message.text
    
    if provided_password == PASSWORD:
        authenticated_users.add(user_id)
        await update.message.reply_text("✅ Authentication successful!")
        await show_services(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Incorrect password. Please try again with /start"
        )
        return ConversationHandler.END


async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display available services as buttons."""
    services = discover_services()
    
    if not services:
        message = "❌ No services found in the parent directory.\n\n" \
                  "Services must have a start.sh script."
        if update.callback_query:
            if update.callback_query.message and hasattr(update.callback_query.message, 'reply_text'):
                await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Create inline keyboard with service buttons
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(f"▶️ {service}", callback_data=f"start_{service}")])
    
    # Add refresh button
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "🚀 Choose a service to start:"
    
    if update.callback_query:
        if update.callback_query.message and hasattr(update.callback_query.message, 'reply_text'):
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    # Check if message is available
    if not query.message or not hasattr(query.message, 'reply_text'):
        logger.warning("Callback query message is unavailable or inaccessible")
        return
    
    user_id = update.effective_user.id
    
    # Check authentication
    if user_id not in authenticated_users:
        await query.message.reply_text(
            "❌ You need to authenticate first. Please use /start"
        )
        return
    
    if query.data == "refresh":
        await show_services(update, context)
        return
    
    # Handle service start
    if query.data.startswith("start_"):
        service_name = query.data[6:]  # Remove "start_" prefix
        
        # Validate service name to prevent path traversal
        if not is_safe_service_name(service_name):
            await query.message.reply_text(
                "❌ Invalid service name. Service names must only contain "
                "alphanumeric characters, hyphens, underscores, and dots."
            )
            logger.warning(f"Rejected unsafe service name: {service_name}")
            return
        
        await start_service(update, context, service_name)


async def start_service(update: Update, context: ContextTypes.DEFAULT_TYPE, service_name: str):
    """Start the specified service."""
    query = update.callback_query
    
    # Check if message is available
    if not query.message or not hasattr(query.message, 'reply_text'):
        logger.warning("Callback query message is unavailable")
        return
    
    service_path = SERVICES_DIR / service_name / 'start.sh'
    
    # Verify the resolved path is still within SERVICES_DIR (prevent path traversal)
    try:
        resolved_service_path = service_path.resolve()
        resolved_services_dir = SERVICES_DIR.resolve()
        if not str(resolved_service_path).startswith(str(resolved_services_dir)):
            logger.error(f"Path traversal attempt detected: {service_name}")
            await query.message.reply_text(
                "❌ Invalid service path."
            )
            return
    except (ValueError, OSError) as e:
        logger.error(f"Error resolving path for service {service_name}: {e}")
        await query.message.reply_text(
            f"❌ Error accessing service '{service_name}'."
        )
        return
    
    if not service_path.exists():
        await query.message.reply_text(
            f"❌ Service '{service_name}' not found or start.sh is missing."
        )
        return
    
    await query.message.reply_text(
        f"⏳ Starting service '{service_name}'..."
    )
    
    try:
        # Use async subprocess to avoid blocking the event loop
        process = await asyncio.create_subprocess_exec(
            'bash', 'start.sh',
            cwd=service_path.parent,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for process with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30.0
            )
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            await process.wait()
            await query.message.reply_text(
                f"⚠️ Service '{service_name}' is taking longer than expected.\n"
                "It may still be starting in the background."
            )
            await show_services(update, context)
            return
        
        if process.returncode == 0:
            output = stdout_text if stdout_text else "Service started successfully"
            # Truncate and escape output for safe display
            output_truncated = output[:500]
            await query.message.reply_text(
                f"✅ Service '{service_name}' started!\n\n"
                f"Output:\n<pre>{escape_html(output_truncated)}</pre>",
                parse_mode='HTML'
            )
        else:
            error = stderr_text if stderr_text else "Unknown error"
            # Truncate and escape error for safe display
            error_truncated = error[:500]
            await query.message.reply_text(
                f"❌ Failed to start service '{service_name}'.\n\n"
                f"Error:\n<pre>{escape_html(error_truncated)}</pre>",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {e}")
        await query.message.reply_text(
            f"❌ Error starting service '{service_name}': {escape_html(str(e))}"
        )
    
    # Show services again
    await show_services(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Operation cancelled. Use /start to begin again."
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display help information."""
    help_text = (
        "🤖 *Service Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Authenticate and show available services\n"
        "/help - Show this help message\n"
        "/logout - Log out from the bot\n\n"
        "*How it works:*\n"
        "1. Use /start to begin\n"
        "2. Enter the password\n"
        "3. Choose a service to start from the list\n"
        "4. The bot will execute the start.sh script for that service"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log out the user."""
    user_id = update.effective_user.id
    if user_id in authenticated_users:
        authenticated_users.remove(user_id)
        await update.message.reply_text("👋 You have been logged out. Use /start to log in again.")
    else:
        await update.message.reply_text("You are not logged in.")


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for password authentication
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('logout', logout))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Bot starting...")
    logger.info(f"Services directory: {SERVICES_DIR}")
    logger.info(f"Available services: {discover_services()}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
