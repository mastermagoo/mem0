# Telegram Bot Setup Guide

## Prerequisites

1. Telegram account
2. mem0 server running (Worker 1 complete)
3. Docker and docker-compose installed
4. Access to BotFather on Telegram

## Step 1: Create Telegram Bot

### 1.1 Open BotFather

1. Open Telegram on any device
2. Search for `@BotFather`
3. Start conversation with BotFather

### 1.2 Create New Bot

Send this command to BotFather:
```
/newbot
```

BotFather will ask for:

1. **Bot name** (display name, can be anything)
   - Suggested: `Mark's Personal Memory`
   - Or: `mem0 Personal AI`

2. **Bot username** (must be unique, must end in 'bot')
   - Suggested: `markcarey_mem0_bot`
   - Or: `mc_personal_memory_bot`

### 1.3 Save Bot Token

BotFather will reply with:
```
Done! Congratulations on your new bot...

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567

Keep your token secure and store it safely...
```

**IMPORTANT:** Copy this token immediately. You'll need it for the next step.

### 1.4 Configure Bot Settings (Optional but Recommended)

**Set description:**
```
/setdescription
@your_bot_username
```
Then send:
```
Personal AI memory system. Store and search memories across all devices.
```

**Set about text:**
```
/setabouttext
@your_bot_username
```
Then send:
```
Universal access to mem0 AI memory system
```

**Set command list:**
```
/setcommands
@your_bot_username
```
Then send:
```
start - Welcome message and setup
remember - Store a new memory
recall - Search memories
list - Show recent memories
namespace - Switch memory context
switch - Quick namespace switch
stats - View statistics
status - System health check
help - Detailed help guide
```

## Step 2: Add Token to Environment

### 2.1 Edit .env file

```bash
cd /Volumes/intel-system/deployment/docker/mem0_tailscale/
nano .env
```

### 2.2 Add TELEGRAM_BOT_TOKEN

Add this line (replace with your actual token):
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

### 2.3 Verify .env file

Check that all required variables are present:
```bash
grep -E "^(TELEGRAM_BOT_TOKEN|MEM0_API_KEY|OPENAI_API_KEY)" .env
```

Should show:
```
TELEGRAM_BOT_TOKEN=1234567890:...
MEM0_API_KEY=mem0-...
OPENAI_API_KEY=sk-...
```

## Step 3: Build and Deploy Bot

### 3.1 Build Docker Image

```bash
cd /Volumes/intel-system/deployment/docker/mem0_tailscale/
docker-compose build telegram_bot
```

Expected output:
```
Building telegram_bot
Step 1/6 : FROM python:3.12-slim
...
Successfully built abc123def456
Successfully tagged mem0_tailscale_telegram_bot:latest
```

### 3.2 Start Bot Container

```bash
docker-compose up -d telegram_bot
```

Expected output:
```
Creating mem0_telegram_bot ... done
```

### 3.3 Verify Container is Running

```bash
docker ps | grep mem0_telegram_bot
```

Should show:
```
CONTAINER ID   IMAGE                              STATUS          PORTS
abc123def456   mem0_tailscale_telegram_bot       Up 2 seconds
```

### 3.4 Check Logs

```bash
docker logs mem0_telegram_bot --tail 50 --follow
```

Expected output:
```
2025-10-16 12:00:00 - __main__ - INFO - Starting mem0 Telegram bot...
2025-10-16 12:00:01 - __main__ - INFO - ✅ mem0 server is healthy
2025-10-16 12:00:01 - __main__ - INFO - ✅ Bot initialized successfully
2025-10-16 12:00:01 - __main__ - INFO - 🚀 Starting polling...
```

If you see these messages, the bot is running successfully!

Press `Ctrl+C` to exit log view (container keeps running).

## Step 4: Test Bot on Telegram

### 4.1 Find Your Bot

1. Open Telegram on any device
2. Search for your bot username (e.g., `@markcarey_mem0_bot`)
3. Click on the bot to open conversation

### 4.2 Start Conversation

Send:
```
/start
```

Expected response:
```
👋 Welcome Mark!

🧠 Personal AI Memory System
I remember everything across all your devices!

Quick Start:
📝 /remember - Store a memory
🔍 /recall - Search memories
...
```

### 4.3 Test Basic Commands

**Test 1: Store a memory**
```
/remember This is a test memory from Telegram bot setup
```

Expected response:
```
✅ Remembered in 'personal':

This is a test memory from Telegram bot setup

Memory ID: ...
```

**Test 2: Recall the memory**
```
/recall test memory
```

Expected response:
```
🔍 Found 1 memories in 'personal':

1. This is a test memory from Telegram bot setup
   Score: 0.95
   ID: ...
```

**Test 3: Check status**
```
/status
```

Expected response:
```
✅ System Status: HEALTHY

🧠 mem0 server: Online
📡 Telegram bot: Connected
...
```

### 4.4 Test Namespace Switching

**Test 4: Switch namespace**
```
/namespace
```

Expected response: Interactive menu with buttons for all namespaces

Click any namespace button.

Expected response:
```
✅ Switched to namespace: 🏢 progressief
...
```

**Test 5: Verify isolation**
```
/remember Test memory in progressief namespace
/recall test memory
```

Should show 1 result (only progressief memory, not personal memory).

Switch back to personal:
```
/switch personal
/recall test memory
```

Should show 1 result (only personal memory, not progressief memory).

## Step 5: Cross-Device Testing

### 5.1 Test on iPhone

1. Open Telegram app on iPhone
2. Find bot conversation
3. Send `/remember Test from iPhone`
4. Send `/recall iPhone`
5. Verify response shows the memory

### 5.2 Test on iPad

1. Open Telegram app on iPad
2. Find same bot conversation
3. Send `/recall iPhone`
4. Verify it shows the memory you just stored from iPhone
5. Send `/remember Test from iPad`

### 5.3 Verify Sync on MacBook

1. Open Telegram on MacBook Pro
2. Find bot conversation
3. Send `/list 10`
4. Verify you see memories from both iPhone and iPad

**Expected result:** All memories visible on all devices, real-time sync.

## Step 6: Response Time Benchmarking

### 6.1 Test /remember Speed

Send 5 consecutive `/remember` commands and time responses:
```
/remember Speed test 1
/remember Speed test 2
/remember Speed test 3
/remember Speed test 4
/remember Speed test 5
```

**Target:** Each response in <2 seconds

### 6.2 Test /recall Speed

Send search queries and time responses:
```
/recall speed test
```

**Target:** Response in <2 seconds

### 6.3 Test /stats Speed

```
/stats
```

**Target:** Response in <3 seconds (queries multiple namespaces)

### 6.4 Test /namespace Speed

```
/namespace
```

**Target:** Menu appears in <1 second

## Troubleshooting

### Bot doesn't respond to /start

**Check container logs:**
```bash
docker logs mem0_telegram_bot --tail 100
```

Look for errors like:
- `ValueError: TELEGRAM_BOT_TOKEN environment variable is required`
  - Fix: Add token to .env file, restart container
- `Failed to start bot: Unauthorized`
  - Fix: Verify bot token is correct
- `Connection refused`
  - Fix: Check mem0 server is running

**Restart container:**
```bash
docker restart mem0_telegram_bot
```

### Bot is slow (>5 seconds)

**Check mem0 server health:**
```bash
docker logs mem0_server --tail 50
```

**Check network connectivity:**
```bash
docker exec mem0_telegram_bot ping -c 3 mem0_server
```

**Restart both services:**
```bash
docker restart mem0_server mem0_telegram_bot
```

### "Failed to store memory" error

**Check mem0 server status:**
```bash
docker ps | grep mem0_server
```

Should show `Up` status. If not:
```bash
docker-compose up -d mem0
```

**Test mem0 API directly:**
```bash
curl http://localhost:8888/health
```

Should return: `{"status":"ok"}`

### Namespace switching doesn't work

**Check config.py has correct namespaces:**
```bash
docker exec mem0_telegram_bot cat /app/config.py | grep namespaces
```

**Restart bot to reload config:**
```bash
docker restart mem0_telegram_bot
```

### Bot stops responding after some time

**Check container is running:**
```bash
docker ps | grep mem0_telegram_bot
```

**Check logs for crashes:**
```bash
docker logs mem0_telegram_bot --tail 200
```

**Check resource usage:**
```bash
docker stats mem0_telegram_bot --no-stream
```

**Restart container:**
```bash
docker restart mem0_telegram_bot
```

## Verification Checklist

After setup, verify all functionality:

- [ ] Bot responds to /start
- [ ] /remember stores memories successfully
- [ ] /recall finds stored memories
- [ ] /list shows recent memories
- [ ] /namespace shows interactive menu
- [ ] Namespace switching works (memories isolated)
- [ ] /switch command works
- [ ] /stats shows memory counts
- [ ] /status shows system health
- [ ] /help displays guide
- [ ] Works on iPhone
- [ ] Works on iPad
- [ ] Works on MacBook Pro
- [ ] Memories sync across devices
- [ ] Response time <2 seconds for most commands
- [ ] Container auto-restarts if crashed
- [ ] Logs are readable and informative

## Next Steps

1. **Read USER_GUIDE.md** - Complete command reference
2. **Set up daily workflow** - Start using bot for real memories
3. **Test namespace organization** - Store memories in relevant contexts
4. **Bookmark bot on all devices** - Pin to top of Telegram conversations
5. **Enable notifications** - Get alerts for bot responses

## Bot Information

After successful setup, document:

**Bot Username:** @your_bot_username
**Bot Display Name:** Your Bot Name
**Bot Token:** (stored in .env, never share)
**Container Name:** mem0_telegram_bot
**Docker Network:** mem0_internal
**mem0 Server URL:** http://mem0_server:8888

**Invite Link (for reference):**
```
https://t.me/your_bot_username
```

---

*Setup guide created: 2025-10-16*
*Worker 4 - Full-Stack Developer*
