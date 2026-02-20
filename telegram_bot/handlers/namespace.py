"""
Namespace management handlers for Telegram bot
Handles namespace switching and display
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

# Namespace display info (emoji + description)
# This is metadata only - actual namespaces come from config.namespaces (environment-driven)
# Format: NAMESPACE_INFO[namespace] = {'emoji': '📊', 'desc': 'Description'}
# If a namespace is not in this dict, defaults will be used
NAMESPACE_INFO = {
    'sap': {'emoji': '📊', 'desc': 'SAP client work & intelligence'},
    'personal': {'emoji': '👤', 'desc': 'Personal notes & reminders'},
    'progressief': {'emoji': '🏢', 'desc': 'Progressief B.V. work'},
    'cv_automation': {'emoji': '💼', 'desc': 'CV automation project'},
    'investments': {'emoji': '💰', 'desc': 'Investment research & tracking'},
    'intel_system': {'emoji': '🖥', 'desc': 'Intel system infrastructure'},
    'wingman': {'emoji': '🛡️', 'desc': 'Wingman system & assistant'},
    'mem0': {'emoji': '🧠', 'desc': 'mem0 system & Telegram bot'}
}

async def namespace_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /namespace command - show current namespace and switch options
    """
    config = context.bot_data['config']
    current_namespace = context.user_data.get('namespace', config.default_namespace)
    config = context.bot_data['config']

    # Build inline keyboard with namespace buttons
    keyboard = []
    for ns in config.namespaces:
        info = NAMESPACE_INFO.get(ns, {'emoji': '📁', 'desc': ns})
        button_text = f"{info['emoji']} {ns.replace('_', ' ').title()}"

        # Mark current namespace with checkmark
        if ns == current_namespace:
            button_text += " ✓"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"ns_{ns}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    current_info = NAMESPACE_INFO.get(current_namespace, {'emoji': '📁', 'desc': current_namespace})

    await update.message.reply_text(
        f"🗂 <b>Current namespace</b>: {current_info['emoji']} {current_namespace}\n"
        f"{current_info['desc']}\n\n"
        "Select a namespace to switch:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def namespace_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle namespace selection from inline keyboard
    """
    query = update.callback_query
    await query.answer()

    # Extract namespace from callback data (format: "ns_namespace_name")
    new_namespace = query.data.replace('ns_', '')

    # Update user's current namespace
    context.user_data['namespace'] = new_namespace

    # Get namespace info
    info = NAMESPACE_INFO.get(new_namespace, {'emoji': '📁', 'desc': new_namespace})

    # Get stats for new namespace
    try:
        mem0 = context.bot_data['mem0_client']
        config = context.bot_data['config']
        full_user_id = config.get_full_user_id(new_namespace)
        stats = mem0.get_stats(full_user_id)

        memory_count = stats.get('total_memories', 0)
        stats_text = f"\n📊 {memory_count} memories stored"
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        stats_text = ""

    await query.edit_message_text(
        f"✅ Switched to namespace: {info['emoji']} <b>{new_namespace}</b>\n"
        f"{info['desc']}{stats_text}\n\n"
        "All memory operations will now use this namespace.\n"
        "Use /namespace to switch again.",
        parse_mode='HTML'
    )

    logger.info(f"User {query.from_user.id} switched to namespace: {new_namespace}")

async def switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /switch command - quick namespace switch without menu
    Usage: /switch [namespace_name]
    """
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /switch [namespace_name]\n\n"
            "Available namespaces:\n" +
            "\n".join(f"• {ns}" for ns in context.bot_data['config'].namespaces) +
            "\n\nOr use /namespace to see a menu."
        )
        return

    new_namespace = context.args[0].lower()
    config = context.bot_data['config']

    # Validate namespace
    if new_namespace not in config.namespaces:
        await update.message.reply_text(
            f"❌ Unknown namespace: {new_namespace}\n\n"
            "Available namespaces:\n" +
            "\n".join(f"• {ns}" for ns in config.namespaces)
        )
        return

    # Update namespace
    context.user_data['namespace'] = new_namespace

    info = NAMESPACE_INFO.get(new_namespace, {'emoji': '📁', 'desc': new_namespace})

    # Get stats
    try:
        mem0 = context.bot_data['mem0_client']
        full_user_id = config.get_full_user_id(new_namespace)
        stats = mem0.get_stats(full_user_id)

        memory_count = stats.get('total_memories', 0)
        stats_text = f"\n📊 {memory_count} memories stored"
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        stats_text = ""

    await update.message.reply_text(
        f"✅ Switched to: {info['emoji']} <b>{new_namespace}</b>\n"
        f"{info['desc']}{stats_text}",
        parse_mode='HTML'
    )

    logger.info(f"User {update.effective_user.id} switched to namespace: {new_namespace}")
