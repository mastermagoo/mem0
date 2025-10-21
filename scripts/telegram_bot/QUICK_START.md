# Telegram Bot - Quick Start

## 5-Minute Setup

### 1. Create Bot (2 minutes)

Open Telegram → Search `@BotFather` → Send:
```
/newbot
```

**Name:** Mark's Personal Memory
**Username:** markcarey_mem0_bot

**Copy the token** BotFather gives you.

### 2. Add Token (1 minute)

```bash
cd /Volumes/intel-system/deployment/docker/mem0_tailscale/
echo 'TELEGRAM_BOT_TOKEN=paste_your_token_here' >> .env
```

### 3. Deploy (2 minutes)

```bash
docker-compose build telegram_bot
docker-compose up -d telegram_bot
docker logs mem0_telegram_bot --tail 20
```

Look for:
```
✅ mem0 server is healthy
✅ Bot initialized successfully
🚀 Starting polling...
```

### 4. Test

Open Telegram → Search your bot → Send:
```
/start
```

You should see welcome message!

Try:
```
/remember This is my first memory
/recall first memory
```

## Essential Commands

```
/remember [text]    Store memory
/recall [query]     Search memories
/namespace          Switch context
/stats              View all namespaces
```

## Common Tasks

**Store memory:**
```
/remember Meeting tomorrow at 2pm
```

**Search memory:**
```
/recall meeting
```

**Switch project:**
```
/namespace
[click "progressief" button]
```

**Check what's stored:**
```
/list
```

## Troubleshooting

**Bot doesn't respond?**
```bash
docker restart mem0_telegram_bot
docker logs mem0_telegram_bot --tail 50
```

**Can't find bot?**
Search: @your_bot_username_here

**"Failed to store memory"?**
Check mem0 is running:
```bash
docker ps | grep mem0_server
```

## Full Guides

- **SETUP.md** - Complete setup instructions
- **USER_GUIDE.md** - All commands and features
- **README.md** - Technical documentation

---

**That's it!** You now have universal AI memory access from any device.
