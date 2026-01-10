#!/bin/bash
# Test Telegram bot functionality
# Tests both PRD and TEST bots

set -e

MEM0_REPO_DIR="${MEM0_REPO_DIR:-/Volumes/Data/ai_projects/mem0-system}"

# Load config
if [[ -f "${MEM0_REPO_DIR}/.env" ]]; then
  source "${MEM0_REPO_DIR}/.env"
fi

if [[ -f "${MEM0_REPO_DIR}/.env.test" ]]; then
  source "${MEM0_REPO_DIR}/.env.test"
fi

PRD_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
PRD_CHAT_ID="${TELEGRAM_CHAT_ID:-7007859146}"

# Load TEST config
TEST_TOKEN=""
TEST_CHAT_ID=""
if [[ -f "${MEM0_REPO_DIR}/.env.test" ]]; then
  TEST_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "${MEM0_REPO_DIR}/.env.test" | cut -d'=' -f2)
  TEST_CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" "${MEM0_REPO_DIR}/.env.test" | cut -d'=' -f2)
fi

echo "=== Telegram Bot Functionality Test ==="
echo ""

# Test PRD Bot
echo "1. Testing PRD Bot Token..."
if [[ -n "$PRD_TOKEN" ]]; then
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${PRD_TOKEN}/getMe")
  if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ PRD Bot authenticated: @${BOT_NAME}"
  else
    echo "   ❌ PRD Bot token invalid"
    echo "   Response: $RESPONSE"
  fi
else
  echo "   ⚠️  PRD token not found in .env"
fi

echo ""

# Test TEST Bot
echo "2. Testing TEST Bot Token..."
if [[ -n "$TEST_TOKEN" ]]; then
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TEST_TOKEN}/getMe")
  if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ TEST Bot authenticated: @${BOT_NAME}"
  else
    echo "   ❌ TEST Bot token invalid"
    echo "   Response: $RESPONSE"
  fi
else
  echo "   ⚠️  TEST token not found in .env.test"
fi

echo ""

# Test sending messages
echo "3. Testing Message Sending..."

if [[ -n "$PRD_TOKEN" ]] && [[ -n "$PRD_CHAT_ID" ]]; then
  echo "   Sending test message via PRD bot..."
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${PRD_TOKEN}/sendMessage" \
    -d "chat_id=${PRD_CHAT_ID}" \
    -d "text=🧪 PRD Bot Test: This message confirms PRD bot can send messages to you." \
    -d "parse_mode=Markdown")
  
  if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "   ✅ PRD Bot message sent successfully"
  else
    echo "   ❌ PRD Bot failed to send message"
    echo "   Response: $RESPONSE"
  fi
fi

if [[ -n "$TEST_TOKEN" ]] && [[ -n "$TEST_CHAT_ID" ]]; then
  echo "   Sending test message via TEST bot..."
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TEST_TOKEN}/sendMessage" \
    -d "chat_id=${TEST_CHAT_ID}" \
    -d "text=🧪 TEST Bot Test: This message confirms TEST bot can send messages to you." \
    -d "parse_mode=Markdown")
  
  if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "   ✅ TEST Bot message sent successfully"
  else
    echo "   ❌ TEST Bot failed to send message"
    echo "   Response: $RESPONSE"
  fi
fi

echo ""

# Test bot containers
echo "4. Testing Bot Containers..."
if docker ps --format '{{.Names}}' | grep -q "^mem0_telegram_bot_prd$"; then
  echo "   ✅ PRD bot container running"
  docker logs mem0_telegram_bot_prd --tail 5 2>&1 | grep -q "polling\|Application started" && echo "      ✅ Bot is polling"
else
  echo "   ❌ PRD bot container not running"
fi

if docker ps --format '{{.Names}}' | grep -q "^mem0_telegram_bot_test$"; then
  echo "   ✅ TEST bot container running"
  docker logs mem0_telegram_bot_test --tail 5 2>&1 | grep -q "polling\|Application started" && echo "      ✅ Bot is polling"
else
  echo "   ❌ TEST bot container not running"
fi

echo ""

# Test health monitor alert
echo "5. Testing Health Monitor Alert Function..."
if [[ -n "$PRD_TOKEN" ]] && [[ -n "$PRD_CHAT_ID" ]]; then
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${PRD_TOKEN}/sendMessage" \
    -d "chat_id=${PRD_CHAT_ID}" \
    -d "text=🧪 Health Monitor Test: This confirms health monitor can send alerts." \
    -d "parse_mode=Markdown")
  
  if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "   ✅ Health monitor alert function working"
  else
    echo "   ❌ Health monitor alert function failed"
    echo "   Response: $RESPONSE"
  fi
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "If you received messages in Telegram, bots are working correctly!"
echo "If not, check:"
echo "  1. Bot tokens are correct in .env files"
echo "  2. Chat ID matches your Telegram user ID"
echo "  3. You've started the bot with /start command"
echo "  4. Bot containers are running"
