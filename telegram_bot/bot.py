#!/usr/bin/env python3
"""
mem0 Telegram Bot - Universal AI Memory Access
Provides Telegram interface for mem0 memory system across all devices
"""
import logging
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Import configuration and handlers
from config import config
from mem0_client import Mem0Client
from handlers.memory import remember_command, recall_command, list_command
from handlers.namespace import namespace_command, namespace_callback, switch_command
from handlers.system import start_command, help_command, stats_command, status_command, error_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Initialize and run the Telegram bot
    """
    logger.info("Starting mem0 Telegram bot...")

    try:
        # Initialize mem0 client
        mem0_client = Mem0Client(config.mem0_url, config.mem0_api_key)

        # Check mem0 server health
        health = mem0_client.health_check()
        if health['status'] == 'healthy':
            logger.info("✅ mem0 server is healthy")
        else:
            logger.warning(f"⚠️ mem0 server health check failed: {health.get('error')}")

        # Namespaces are loaded from NAMESPACES environment variable in config.py
        # If NAMESPACES is not set, defaults are used
        logger.info(f"Loaded {len(config.namespaces)} namespaces from configuration")

        # Build application
        application = Application.builder().token(config.telegram_token).build()

        # Store shared objects in bot_data
        application.bot_data['mem0_client'] = mem0_client
        application.bot_data['config'] = config

        # Register command handlers

        # System commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("status", status_command))

        # Memory commands
        application.add_handler(CommandHandler("remember", remember_command))
        application.add_handler(CommandHandler("recall", recall_command))
        application.add_handler(CommandHandler("list", list_command))

        # Namespace commands
        application.add_handler(CommandHandler("namespace", namespace_command))
        application.add_handler(CommandHandler("switch", switch_command))

        # Callback query handler for inline keyboards (namespace selection)
        application.add_handler(CallbackQueryHandler(namespace_callback, pattern="^ns_"))

        # Error handler
        application.add_error_handler(error_handler)

        logger.info("✅ Bot initialized successfully")
        logger.info(f"Available commands: start, help, remember, recall, list, namespace, switch, stats, status")
        logger.info(f"Default namespace: {config.default_namespace}")
        logger.info(f"Available namespaces: {', '.join(config.namespaces)}")

        # Start the bot
        logger.info("🚀 Starting polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
