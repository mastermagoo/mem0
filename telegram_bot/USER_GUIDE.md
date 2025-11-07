# mem0 Telegram Bot - User Guide

## Overview

The mem0 Telegram bot provides universal access to your personal AI memory system from any device - iPhone, iPad, MacBook Pro, or any device with Telegram installed.

## Getting Started

### 1. Find the Bot on Telegram

1. Open Telegram on any device
2. Search for your bot by its username (provided after setup)
3. Click "Start" or send `/start` command

### 2. Initial Setup

When you first start the bot, you'll see a welcome message with available commands. The bot defaults to the `personal` namespace.

## Core Commands

### Memory Operations

#### /remember [text]
Store a new memory in your current namespace.

**Examples:**
```
/remember Meeting with John tomorrow at 2pm
/remember Sarah's birthday is June 15th
/remember Docker credentials are in /opt/credentials/docker.env
/remember Important: Review quarterly report by Friday
```

**Tips:**
- Be specific and descriptive
- Include dates, times, and context
- Natural language works best
- No length limit, but keep it focused

#### /recall [query]
Search your memories using natural language queries.

**Examples:**
```
/recall meetings with John
/recall Sarah's birthday
/recall Docker credentials
/recall quarterly report
```

**Tips:**
- Use keywords from your memories
- Try different phrasings if first search doesn't work
- Returns top 5 most relevant results
- Shows relevance score for each result

#### /list [number]
Show recent memories from current namespace.

**Examples:**
```
/list           # Shows last 10 memories
/list 20        # Shows last 20 memories
/list 5         # Shows last 5 memories
```

**Tips:**
- Default: 10 memories
- Maximum: 50 memories
- Useful for browsing recent additions
- Sorted by most recent first

### Namespace Management

#### /namespace
Show interactive menu to switch between contexts.

**Available namespaces:**
- 👤 **personal** - Personal notes & reminders
- 🏢 **progressief** - Progressief B.V. work
- 💼 **cv_automation** - CV automation project
- 💰 **investments** - Investment research & tracking
- 🖥 **intel_system** - Intel system infrastructure
- 🤖 **ai_projects** - AI project development
- 🎯 **vectal** - Vectal.ai development

**How it works:**
1. Send `/namespace`
2. Bot shows current namespace and buttons for all available namespaces
3. Click a button to switch
4. Confirmation message shows memory count in new namespace

#### /switch [namespace_name]
Quick namespace switch without menu.

**Examples:**
```
/switch progressief
/switch personal
/switch cv_automation
```

**Tips:**
- Faster than using /namespace menu
- Useful if you know exact namespace name
- Names are case-insensitive
- Use underscores (e.g., `cv_automation` not `cv automation`)

### System Commands

#### /stats
View memory statistics across all namespaces.

**Shows:**
- Memory count for each namespace
- Total memories across all namespaces
- Current active namespace (marked with 📍)

**Example output:**
```
📊 Memory Statistics

👤 personal 📍: 42 memories
🏢 progressief: 15 memories
💼 cv_automation: 8 memories
💰 investments: 23 memories
🖥 intel_system: 12 memories
🤖 ai_projects: 5 memories
🎯 vectal: 3 memories

Total: 108 memories across all namespaces
```

#### /status
Check system health and connectivity.

**Shows:**
- mem0 server status (online/offline)
- Telegram bot connection status
- Current namespace
- Response time estimate

**Use when:**
- Bot seems slow or unresponsive
- Getting error messages
- Troubleshooting connection issues

#### /help
Display complete command reference (same information as this guide).

## Understanding Namespaces

### What are namespaces?

Namespaces are isolated memory contexts. Memories stored in one namespace are completely separate from other namespaces.

**Think of namespaces as different notebooks:**
- Each namespace = separate notebook
- Switching namespace = opening different notebook
- Memories don't cross between notebooks

### When to use different namespaces?

**personal**: Day-to-day life, reminders, personal notes
- "Dentist appointment next Tuesday at 3pm"
- "Mom's favorite restaurant is La Bella"

**progressief**: Work-related for Progressief B.V.
- "Client meeting notes from vendor X"
- "B2B contract renewal deadline is March 31st"

**cv_automation**: CV automation project specifics
- "Job matcher threshold is 85%"
- "LinkedIn scraper runs every 30 minutes"

**investments**: Investment research and portfolio tracking
- "Research NVDA stock before Friday"
- "Portfolio rebalancing due in Q2"

**intel_system**: Infrastructure and system management
- "PostgreSQL port is 5432 on mac-studio"
- "Redis password rotation every 90 days"

**ai_projects**: AI development work
- "Claude Code workflow documented in .claude/"
- "mem0 API endpoint: /v1/memories"

**vectal**: Vectal.ai specific development
- "Next.js app in frontend/vectal.ai/"
- "Stripe integration pending for May launch"

### Best Practices

1. **Use the right namespace** - Store memories in the most relevant context
2. **Don't duplicate** - Same memory doesn't need to be in multiple namespaces
3. **Switch freely** - No cost to switching namespaces
4. **Check stats** - Use `/stats` to see what's where
5. **Be consistent** - Develop habits for which namespace to use when

## Cross-Device Usage

### How it works

All your memories are synced in real-time across all devices:

1. Store memory on iPhone → Available instantly on iPad and MacBook
2. Search on iPad → Same results as on iPhone
3. Switch namespace on MacBook → Reflected on all devices

### Device-Specific Tips

**iPhone:**
- Use Telegram notifications for quick memory capture
- Voice messages can be copied and sent with /remember
- Siri shortcuts can trigger Telegram commands

**iPad:**
- Split view: Telegram bot + notes/browser
- Great for reviewing /list output while working
- Landscape keyboard makes commands easier

**MacBook Pro:**
- Copy-paste from other apps into /remember
- Multiple Telegram windows for different namespaces
- Can use SSH access for direct mem0 API calls if needed

## Common Use Cases

### 1. Quick Capture
```
/remember Check email from John about project deadline
```
*Later, from different device:*
```
/recall John project deadline
```

### 2. Meeting Notes
```
# During meeting on iPhone:
/switch progressief
/remember Client X wants feature Y by end of month
/remember Follow up with Sarah about budget approval

# After meeting on MacBook:
/recall Client X
/recall Sarah budget
```

### 3. Project Context
```
# Switch to project namespace:
/switch cv_automation

# Store technical details:
/remember Database name is cv_automation_prod on mac-studio
/remember Port 8050 for cv-api service

# Later retrieval:
/recall database name
/recall cv-api port
```

### 4. Personal Reminders
```
/switch personal
/remember Water plants every Monday
/remember Gym membership renews April 1st
/remember Car insurance expires 2025-08-15

# Set recurring searches:
/recall water plants  # Check weekly
/recall renews  # Check monthly
```

## Troubleshooting

### Bot not responding

1. Check system status: `/status`
2. Wait 10 seconds and try again
3. Try switching namespace and switching back
4. Check Telegram app is updated

### "Failed to store memory" error

1. Run `/status` to check mem0 server
2. Verify bot container is running:
   ```bash
   docker ps | grep mem0_telegram_bot
   ```
3. Check logs:
   ```bash
   docker logs mem0_telegram_bot --tail 50
   ```

### Empty search results

1. Verify you're in correct namespace: `/namespace`
2. Check if memories exist: `/list`
3. Try broader search terms
4. Check memory count: `/stats`

### Slow response times

- Normal: <2 seconds
- Slow: 2-5 seconds (usually OK, server busy)
- Very slow: >5 seconds (check `/status`)

**If consistently slow:**
1. Check mem0 server health
2. Restart bot container: `docker restart mem0_telegram_bot`
3. Check network connectivity

### Wrong namespace

If you stored memory in wrong namespace:

1. `/switch [correct_namespace]`
2. `/remember [text]` (store again in correct place)
3. `/switch [wrong_namespace]`
4. *(Currently no delete command, but coming soon)*

## Advanced Tips

### Effective Memory Storage

**Good examples:**
```
/remember Meeting with Sarah Johnson at Starbucks on Main St, June 15th 2pm, discuss Q2 budget
/remember Docker Compose file location: /Volumes/intel-system/deployment/docker/mem0_tailscale/docker-compose.yml
/remember John's preferred communication: Telegram for urgent, email for non-urgent
```

**Less effective:**
```
/remember meeting tomorrow
/remember check that thing
/remember important
```

**Why?** More context = better recall. Include who, what, when, where, why.

### Search Strategies

**Broad to narrow:**
```
/recall meetings          # Too many results
/recall meetings Sarah    # Better
/recall Sarah June 15th   # Most specific
```

**Keyword mixing:**
```
/recall docker compose location
/recall database credentials mac-studio
/recall quarterly budget meeting notes
```

**Date-based searches:**
```
/recall June 15th
/recall 2025-08-15
/recall April 1st
```

### Namespace Organization

**Project-based:**
- Create mental map: "Work = progressief, Side project = ai_projects"
- When starting work session, switch namespace first
- End of day: `/stats` to review what was captured

**Context-based:**
- Quick personal note while working? Stay in work namespace or quick `/switch personal`
- Reference needed from other namespace? `/switch`, `/recall`, switch back

**Review routine:**
- Daily: `/list` in active namespaces
- Weekly: `/stats` to see distribution
- Monthly: Search old memories to verify recall still works

## FAQ

**Q: Can I access this from my work computer?**
A: Yes! Telegram works on any device. Just log into Telegram and find the bot.

**Q: Are my memories private?**
A: Yes. Single-user bot, self-hosted on your infrastructure, encrypted in transit.

**Q: Can I delete memories?**
A: Not yet via bot. Coming in future update. Currently requires direct API access.

**Q: What if I'm offline?**
A: Bot requires internet. Memories are not cached locally on your device.

**Q: Can I export memories?**
A: Not directly from bot. Can export via mem0 API or database backup.

**Q: Is there a limit to memory storage?**
A: No hard limit. Practical limit is database storage capacity on mac-studio.

**Q: Can I use voice messages?**
A: Not directly. Voice must be transcribed first, then use `/remember [transcribed text]`.

**Q: Can I add images or files?**
A: Not currently. Text-only for now. Can store file paths or descriptions.

**Q: What happens if bot crashes?**
A: Auto-restarts (docker restart policy). All memories are safe in database.

**Q: Can I have multiple users?**
A: Current setup is single-user (Mark Carey). Multi-user requires authentication update.

## Getting Help

1. Try `/help` command in bot
2. Check `/status` for system health
3. Review this guide for command examples
4. Check Docker logs: `docker logs mem0_telegram_bot`
5. Verify mem0 server is running: `docker ps | grep mem0_server`

## Summary

**Most-used commands:**
```
/remember [text]          # Store memory
/recall [query]           # Search memories
/namespace                # Switch context
/stats                    # View overview
```

**Quick workflow:**
1. Switch to relevant namespace (`/namespace` or `/switch`)
2. Store memories as you go (`/remember`)
3. Search when needed (`/recall`)
4. Review periodically (`/list`, `/stats`)

**Key principle:** Capture everything, search when needed, organize by namespace.

---

*Last updated: 2025-10-16*
*Version: 1.0*
