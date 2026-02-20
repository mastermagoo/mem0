# BTP Cockpit Access - What to Do

**Access Granted:** Nov 18 during meeting ✅  
**Your Access:** 6 subaccounts visible (CAS_ESX and CAS_ESY environments)

---

## ✅ WHAT YOU HAVE ACCESS TO (From Screenshot)

**CAS_ESX Subaccounts (Europe Netherlands - Azure):**
- CAS_ESX_DEV (Development)
- CAS_ESX_PRD (Production)
- CAS_ESX_QAS (Test/Quality Assurance)

**CAS_ESY Subaccounts (Europe Frankfurt - AWS):**
- CAS_ESY_DEV (Development)
- CAS_ESY_PRD (Production)
- CAS_ESY_QAS (Test/Quality Assurance)

**Note:** ESX = Azure region, ESY = AWS region (multi-cloud setup)

---

## 🎯 WHAT TO DO NOW (Before Thursday Deep-Dive)

### **TODAY/TOMORROW - Exploration (1-2 hours)**

**Goal:** Familiarize yourself with BTP structure, find AI Core services

**Steps:**

**1. Navigate to Each Subaccount (15 min):**
```
Click: CAS_ESX_DEV
Look for:
  - Services > AI Core (is it listed?)
  - Instances and Subscriptions > AI Core
  - Cloud Foundry > Spaces > Applications
```

Repeat for CAS_ESX_QAS and CAS_ESX_PRD

**2. Find AI Core Instances (15 min):**
```
In each subaccount:
  Services & Instances > Instances
  
Look for:
  - "AI Core" service instances
  - "AI Launchpad" (UI for AI Core)
  - Any SAP AI services
```

**3. Locate ESP AI Proxy (15 min):**
```
Cloud Foundry > Spaces
  
Look for:
  - Applications named "ESP AI Proxy" or similar
  - Running applications (green status)
  - Routes/URLs
```

**4. Check HANA Cloud (15 min):**
```
SAP HANA Cloud section (if visible)

Or use the links Oliver shared:
  - cas-dev.hana-tooling... (DEV)
  - cas-qas.hana-tooling... (QAS)
  - cas.hana-tooling... (PROD)
  
Credentials: request via approved channel (do not store in this repo)
```

**5. Look for Logs/Monitoring (15 min):**
```
Try to find:
  - Application Logs (for ESP AI Proxy)
  - AI Core Logs (for 502 errors)
  - Monitoring dashboards
  - Recent errors
```

---

## 📝 WHAT TO DOCUMENT (Take Screenshots/Notes)

**For Thursday Meeting:**
- [ ] Which subaccount has AI Core? (ESX or ESY or both?)
- [ ] How many AI Core instances? (1 per environment or shared?)
- [ ] Can you see application logs?
- [ ] Can you access AI Launchpad?
- [ ] What Cloud Foundry apps are running?

**Questions This Will Answer:**
- Where are the 502 errors logged?
- Which environment is hitting rate limits?
- How is AI Core deployed (dedicated vs on-demand)?
- Where is ESP AI Proxy running?

---

## 🎯 WHAT NOT TO CHANGE

**READ ONLY for now:**
- ❌ Don't modify any configurations
- ❌ Don't restart any applications
- ❌ Don't change any settings
- ✅ Just explore and learn

**Why:**
- 2000 consultants using production
- Thursday you'll understand with team
- Don't break anything before understanding it

---

## 🔍 SPECIFIC THINGS TO LOOK FOR

### **AI Core Service:**
```
Services > Service Marketplace > Search "AI Core"
or
Instances and Subscriptions > filter "AI"

Check:
- Is AI Core subscribed?
- Which plan/tier? (Extended vs Standard?)
- Usage metrics visible?
```

### **Rate Limiting Evidence:**
```
AI Core > Monitoring (if accessible)
or
Application Logs

Look for:
- 502 errors in logs
- Rate limit warnings
- Token usage metrics
```

### **Multi-Environment Setup:**
```
Compare DEV vs QAS vs PROD:
- Same AI Core setup in each?
- Separate AI Core instances?
- Shared or isolated?
```

---

## 💡 IF YOU GET STUCK

**Can't find AI Core?**
- It might be in ESY subaccounts (AWS Frankfurt)
- Or Cloud Foundry spaces within subaccounts
- Ask Steffen tomorrow in team meeting

**Can't access certain areas?**
- Normal - permissions may be limited
- Document what you CAN'T see
- Ask Oliver/Steffen for additional access Thursday

**Confused by structure?**
- Take screenshots
- Note questions for Thursday
- Team will explain during deep-dive

---

## 📋 DELIVERABLE FOR THURSDAY

**Come Prepared With:**
- "I explored BTP, I can see X, Y, Z"
- "I couldn't access A, B - do I need additional permissions?"
- "I have questions about how [component] works"

**This shows:**
- You're proactive (explored on your own)
- You're thorough (documented what you found)
- You're prepared (specific questions, not vague)

---

## ⚡ BOTTOM LINE

**What Oliver gave you:** BTP Cockpit access to 6 subaccounts  
**What to do now:** Explore (read-only), document findings  
**What to prepare:** Questions for Thursday based on exploration  
**What NOT to do:** Change anything, break anything

**Time needed:** 1-2 hours exploration (today or tomorrow)

**This is discovery, not action. Learn the landscape.**

---

**Created:** 2025-11-18 3:40 PM  
**Purpose:** Guide Mark through BTP Cockpit exploration  
**Status:** Use today/tomorrow before Thursday deep-dive














