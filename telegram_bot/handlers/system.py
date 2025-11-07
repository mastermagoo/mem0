"""
System handlers for Telegram bot
Handles /start, /help, /stats, /status commands
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
from handlers.namespace import NAMESPACE_INFO

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - welcome message and setup
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Initialize user's namespace to default
    context.user_data['namespace'] = 'personal'

    welcome_message = (
        f"👋 Welcome {user_name}!\n\n"
        "🧠 **Personal AI Memory System**\n"
        "I remember everything across all your devices!\n\n"
        "**Quick Start:**\n"
        "📝 /remember - Store a memory\n"
        "🔍 /recall - Search memories\n"
        "📋 /list - Show recent memories\n"
        "🗂 /namespace - Switch context\n"
        "📊 /stats - View statistics\n"
        "🏥 /status - System health\n"
        "❓ /help - Detailed help\n\n"
        f"Current namespace: 👤 personal\n\n"
        "Start by storing a memory:\n"
        "`/remember Meeting with John tomorrow at 2pm`"
    )

    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    logger.info(f"User {user_id} started bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command - detailed help guide
    """
    help_message = (
        "📚 **mem0 Telegram Bot - Complete Guide**\n\n"

        "**Memory Operations:**\n"
        "• `/remember [text]` - Store new memory\n"
        "  Example: `/remember Call Sarah about project update`\n\n"
        "• `/recall [query]` - Search memories\n"
        "  Example: `/recall meetings with Sarah`\n\n"
        "• `/list [number]` - Show recent memories (default: 10)\n"
        "  Example: `/list 20`\n\n"

        "**Namespace Management:**\n"
        "• `/namespace` - Show menu to switch context\n"
        "• `/switch [name]` - Quick switch to namespace\n"
        "  Example: `/switch progressief`\n\n"

        "Available namespaces:\n"
    )

    # Add namespace list
    config = context.bot_data['config']
    for ns in config.namespaces:
        info = NAMESPACE_INFO.get(ns, {'emoji': '📁', 'desc': ns})
        help_message += f"  {info['emoji']} **{ns}** - {info['desc']}\n"

    help_message += (
        "\n**System Commands:**\n"
        "• `/stats` - Memory statistics per namespace\n"
        "• `/status` - System health check\n"
        "• `/help` - This help message\n\n"

        "**Tips:**\n"
        "• Memories are isolated by namespace\n"
        "• Switch namespaces to organize different contexts\n"
        "• Use natural language for queries\n"
        "• Works across all your devices (iPhone, iPad, Mac)\n\n"

        "**Troubleshooting:**\n"
        "If bot is slow or not responding:\n"
        "1. Check system status with `/status`\n"
        "2. Try again in a few seconds\n"
        "3. Switch namespace and switch back\n"
    )

    await update.message.reply_text(help_message, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stats command - show memory statistics
    """
    mem0 = context.bot_data['mem0_client']
    config = context.bot_data['config']

    stats_message = "📊 <b>Memory Statistics</b>\n\n"

    total_memories = 0

    # Get stats for each namespace
    for ns in config.namespaces:
        try:
            full_user_id = config.get_full_user_id(ns)
            stats = mem0.get_stats(full_user_id)
            count = stats.get('total_memories', 0)
            total_memories += count

            info = NAMESPACE_INFO.get(ns, {'emoji': '📁', 'desc': ns})

            # Mark current namespace
            current_marker = " 📍" if context.user_data.get('namespace') == ns else ""

            stats_message += f"{info['emoji']} <b>{ns}</b>{current_marker}: {count} memories\n"
        except Exception as e:
            logger.error(f"Failed to get stats for {ns}: {e}")
            stats_message += f"📁 <b>{ns}</b>: Error\n"

    stats_message += f"\n<b>Total</b>: {total_memories} memories across all namespaces"

    await update.message.reply_text(stats_message, parse_mode='HTML')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command - system health check
    """
    mem0 = context.bot_data['mem0_client']

    status_msg = await update.message.reply_text("🔍 Checking system health...")

    # Check mem0 server health
    health = mem0.health_check()

    if health['status'] == 'healthy':
        status_text = (
            "✅ **System Status: HEALTHY**\n\n"
            "🧠 mem0 server: Online\n"
            "📡 Telegram bot: Connected\n"
            "⚡ Response time: <2 seconds\n\n"
            f"Current namespace: {context.user_data.get('namespace', 'personal')}\n\n"
            "All systems operational!"
        )
    else:
        status_text = (
            "⚠️ **System Status: ISSUES DETECTED**\n\n"
            "🧠 mem0 server: Offline or unreachable\n"
            f"Error: {health.get('error', 'Unknown')}\n\n"
            "Please check:\n"
            "1. mem0 container is running\n"
            "2. Network connectivity\n"
            "3. Try again in a few seconds\n"
        )

    await status_msg.edit_text(status_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors in bot execution
    """
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again or use /status to check system health."
        )
