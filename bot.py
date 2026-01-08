#!/usr/bin/env python3
"""
Telegram Bot for starting services remotely.
This bot authenticates users with a password and allows them to start services
located in the parent directory that have a start.sh script.
"""

import os
import subprocess
import logging
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


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown formatting."""
    # Escape special markdown characters
    special_chars = ['`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '\\']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


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
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
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
        await start_service(update, context, service_name)


async def start_service(update: Update, context: ContextTypes.DEFAULT_TYPE, service_name: str):
    """Start the specified service."""
    query = update.callback_query
    service_path = SERVICES_DIR / service_name / 'start.sh'
    
    if not service_path.exists():
        await query.message.reply_text(
            f"❌ Service '{service_name}' not found or start.sh is missing."
        )
        return
    
    await query.message.reply_text(
        f"⏳ Starting service '{service_name}'..."
    )
    
    try:
        # Change to service directory and execute start.sh
        result = subprocess.run(
            ['bash', 'start.sh'],
            cwd=service_path.parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout if result.stdout else "Service started successfully"
            # Truncate and escape output for safe display
            output_truncated = output[:500]
            await query.message.reply_text(
                f"✅ Service '{service_name}' started!\n\n"
                f"Output:\n<pre>{escape_markdown(output_truncated)}</pre>",
                parse_mode='HTML'
            )
        else:
            error = result.stderr if result.stderr else "Unknown error"
            # Truncate and escape error for safe display
            error_truncated = error[:500]
            await query.message.reply_text(
                f"❌ Failed to start service '{service_name}'.\n\n"
                f"Error:\n<pre>{escape_markdown(error_truncated)}</pre>",
                parse_mode='HTML'
            )
    except subprocess.TimeoutExpired:
        await query.message.reply_text(
            f"⚠️ Service '{service_name}' is taking longer than expected.\n"
            "It may still be starting in the background."
        )
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {e}")
        await query.message.reply_text(
            f"❌ Error starting service '{service_name}': {str(e)}"
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
