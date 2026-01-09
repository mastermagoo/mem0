# Manual Telegram Configuration Required

**Status:** ⚠️ NEEDS MANUAL EDIT  
**File:** `/Volumes/Data/ai_projects/mem0-system/.env`

---

## 🚨 Issue

The `.env` file has file locking issues and cannot be edited programmatically.
The Telegram bot is restart-looping because it has placeholder credentials.

---

## ✅ Solution (2 minutes)

### Step 1: Edit .env File

```bash
cd /Volumes/Data/ai_projects/mem0-system
nano .env
```

### Step 2: Find and Replace These Lines

**FIND:**
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**REPLACE WITH:**
```bash
TELEGRAM_BOT_TOKEN=8272438703:AAHXnyrkdQ3s9r0QEGoentrTFxuaD5B5nSk
TELEGRAM_CHAT_ID=7007859146
```

### Step 3: Also Update These (if still placeholders)

```bash
NEO4J_PASSWORD=neo4jPrdPassword2026SecureV2
GRAFANA_PASSWORD=Grafana_Prd_2026!
MEM0_API_KEY=mem0-prd-api-b0539021-c9a6-4aaa-9193-665f63851a0d
```

### Step 4: Save and Restart Telegram Bot

```bash
# Save in nano: Ctrl+O, Enter, Ctrl+X

# Restart bot
docker restart mem0_telegram_bot_prd

# Verify it's running
sleep 10
docker logs mem0_telegram_bot_prd --tail 20
```

### Step 5: Test Telegram Alert

```bash
curl -X POST "https://api.telegram.org/bot8272438703:AAHXnyrkdQ3s9r0QEGoentrTFxuaD5B5nSk/sendMessage" \
  -d "chat_id=7007859146" \
  -d "text=✅ mem0 PRD - Telegram alerts now working!" \
  -d "parse_mode=Markdown"
```

You should receive a message in Telegram.

---

## ✅ Expected Result

After restart, bot logs should show:
```
✅ mem0 server is healthy
✅ Bot initialized successfully
🚀 Starting polling...
```

And Telegram bot container status should be:
```
Up X minutes
```

Not "Restarting (1)".

---

## 📝 Verification

```bash
# Check bot is running (not restarting)
docker ps --filter "name=mem0_telegram_bot_prd"

# Check bot logs for success
docker logs mem0_telegram_bot_prd | grep "✅"

# Test health monitor with Telegram
/Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh
```

---

**This is the only manual step needed - everything else is automated!**
