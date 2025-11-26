"""
Memory operation handlers for Telegram bot
Handles /remember and /recall commands
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /remember command - store new memory
    Usage: /remember [text to remember]
    """
    user_id = update.effective_user.id

    # Get current namespace from context
    namespace = context.user_data.get('namespace', 'personal')

    # Get text to remember from command args
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /remember [text to remember]\n\n"
            "Example: /remember Meeting with John on Friday at 2pm"
        )
        return

    text = ' '.join(context.args)

    # Store in mem0
    try:
        mem0 = context.bot_data['mem0_client']
        config = context.bot_data['config']

        full_user_id = config.get_full_user_id(namespace)

        result = mem0.store_memory(
            user_id=full_user_id,
            content=text,
            metadata={'source': 'telegram', 'telegram_user_id': user_id}
        )

        await update.message.reply_text(
            f"✅ Remembered in '{namespace}':\n\n"
            f"{text}\n\n"
            f"Memory ID: {result.get('id', 'unknown')}"
        )
        logger.info(f"Stored memory for user {user_id} in namespace {namespace}")

    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        await update.message.reply_text(
            f"❌ Failed to store memory:\n{str(e)}\n\n"
            "Please check if mem0 server is running with /status"
        )

async def recall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /recall command - search memories
    Usage: /recall [search query]
    """
    user_id = update.effective_user.id

    # Get current namespace from context
    namespace = context.user_data.get('namespace', 'personal')

    # Get search query from command args
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /recall [search query]\n\n"
            "Example: /recall meetings with John"
        )
        return

    query = ' '.join(context.args)

    # Search mem0
    try:
        mem0 = context.bot_data['mem0_client']
        config = context.bot_data['config']

        full_user_id = config.get_full_user_id(namespace)

        # Send "searching..." message
        status_msg = await update.message.reply_text(f"🔍 Searching '{namespace}' for: {query}...")

        memories = mem0.search_memories(
            user_id=full_user_id,
            query=query,
            limit=config.max_recall_results
        )

        # Delete status message
        await status_msg.delete()

        if not memories:
            await update.message.reply_text(
                f"🔍 No memories found in '{namespace}' for:\n{query}\n\n"
                "Try:\n"
                "• Using different keywords\n"
                "• Checking if you're in the right namespace (/namespace)\n"
                "• Storing some memories first (/remember)"
            )
            return

        # Format response
        response = f"🔍 Found {len(memories)} memories in '{namespace}':\n\n"

        for i, mem in enumerate(memories, 1):
            # Extract memory content (handle different response formats)
            if isinstance(mem, dict):
                content = mem.get('memory', mem.get('content', str(mem)))
                score = mem.get('score', 'N/A')
                mem_id = mem.get('id', 'unknown')
            else:
                content = str(mem)
                score = 'N/A'
                mem_id = 'unknown'

            # Truncate long memories
            if len(content) > 200:
                content = content[:200] + "..."

            response += f"{i}. {content}\n"
            if score != 'N/A':
                response += f"   Score: {score}\n"
            response += f"   ID: {mem_id}\n\n"

        await update.message.reply_text(response)
        logger.info(f"Recalled {len(memories)} memories for user {user_id} in namespace {namespace}")

    except Exception as e:
        logger.error(f"Failed to recall memories: {e}")
        await update.message.reply_text(
            f"❌ Failed to search memories:\n{str(e)}\n\n"
            "Please check if mem0 server is running with /status"
        )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /list command - show recent memories
    Usage: /list [optional: number of memories]
    """
    user_id = update.effective_user.id
    namespace = context.user_data.get('namespace', 'personal')

    # Get limit from args or use default
    limit = 10
    if context.args:
        try:
            limit = int(context.args[0])
            limit = min(limit, 50)  # Cap at 50
        except ValueError:
            await update.message.reply_text("❌ Invalid number. Usage: /list [number]")
            return

    try:
        mem0 = context.bot_data['mem0_client']
        config = context.bot_data['config']

        full_user_id = config.get_full_user_id(namespace)

        # Get all memories for namespace
        memories = mem0.get_all_memories(full_user_id)

        if not memories:
            await update.message.reply_text(
                f"📭 No memories found in '{namespace}'\n\n"
                "Start storing memories with /remember"
            )
            return

        # Take most recent (up to limit)
        recent_memories = memories[:limit]

        response = f"📋 Recent {len(recent_memories)} memories in '{namespace}':\n\n"

        for i, mem in enumerate(recent_memories, 1):
            if isinstance(mem, dict):
                content = mem.get('memory', mem.get('content', str(mem)))
                mem_id = mem.get('id', 'unknown')
            else:
                content = str(mem)
                mem_id = 'unknown'

            # Truncate long memories
            if len(content) > 150:
                content = content[:150] + "..."

            response += f"{i}. {content}\n   ID: {mem_id}\n\n"

        if len(memories) > limit:
            response += f"\n... and {len(memories) - limit} more memories"

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Failed to list memories: {e}")
        await update.message.reply_text(f"❌ Failed to list memories:\n{str(e)}")
