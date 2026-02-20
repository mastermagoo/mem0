# JIRA Workflow for Vital Tickets

**Purpose:** Fast, efficient Jira monitoring for SAP AI work  
**Date:** Nov 24, 2025

---

## ⚡ FAST WORKFLOW

### **Daily (5 minutes):**

**1. Check Your Vital Tickets:**
```
JQL: project = CASPBM AND labels = "ESP@CAS Platform_Tools" AND status != Done
```

Watch for:
- CR143 (CASPBM-861) - AI Enhancements ⚠️ CRITICAL
- CR144 (CASPBM-1002) - Joule enhancements (Medium priority)
- Any new tickets assigned to you

**2. Quick Scan (2 min):**
- Latest comment (who, when, what)
- Status change (any movement?)
- Your name mentioned?

**3. Action Decision:**
- **New comment mentioning you?** → Read + respond
- **Status changed?** → Note in daily log
- **No changes?** → Move on

---

## 📋 WEEKLY (Wednesday 8AM - Tom's Update Day)

**Tom updates CR143 every Wednesday 8AM** - Check that day!

**Workflow:**
1. **8:30 AM CET:** Check CR143 for Tom's update
2. **Read his comment** (he'll mention your progress)
3. **Update Oliver if needed** ("Tom noted progress on CR143")
4. **Document in your weekly summary**

---

## 🎯 VITAL TICKETS YOU'RE WATCHING

### **Priority 1: CR143 (CASPBM-861)**
- **Why:** 2 months overdue, blocking 51K tickets
- **Check:** Daily (or after any major progress)
- **Your role:** Unblock performance issues
- **Update when:** You make progress on 502/performance

### **Priority 2: CR144 (CASPBM-1002)**
- **Why:** 1 month overdue, but not blocking
- **Check:** Weekly (Wednesday with Tom's update)
- **Your role:** Monitor only (not your area yet)
- **Update when:** Oliver asks or you're pulled in

---

## 🔄 PASTE TO TELEGRAM BOT (Future Automation)

**When you check Jira, paste this to your Telegram bot:**

```
CR143 Update [DATE]:
- Status: [Status]
- Latest: [Brief summary of latest comment]
- Action: [What you did or need to do]
```

**Bot will:**
- Store in mem0
- Log in PostgreSQL
- Make queryable via RAG

---

## 📊 SIMPLE TRACKING TEMPLATE

**Create:** `/03-deliverables/JIRA_DAILY_LOG.md`

```markdown
# JIRA Daily Log

## [DATE]

### CR143 (CASPBM-861) - AI Enhancements
- **Status:** In Development
- **Latest Comment:** [Who] - [Date] - [Summary]
- **My Progress:** [What you did today]
- **Next:** [What's next]

### CR144 (CASPBM-1002) - Joule enhancements
- **Status:** In Development
- **Latest Comment:** [Who] - [Date] - [Summary]
- **Relevance:** [Medium/Low - monitoring only]
```

---

## 🚨 ALERT CONDITIONS

**Immediately check Jira if:**
1. Tom tags you in a comment
2. CR143 status changes
3. New ticket assigned to you
4. Email notification from Jira

**Don't check Jira if:**
- No notifications
- Nothing urgent pending
- Focus time needed for technical work

---

## ⏰ TIME INVESTMENT

**Daily:** 5 minutes (quick scan)  
**Wednesday:** 10 minutes (Tom's update + your summary)  
**As needed:** When tagged or progress made

**Total:** ~30 min/week average

---

## 🎯 SUCCESS CRITERIA

✅ Never miss Tom's Wednesday CR143 update  
✅ Respond to tags within 4 hours  
✅ Update CR143 when you make progress  
✅ Weekly summary includes Jira status  
✅ No manual checking beyond vital tickets

---

## 📝 WHAT TO IGNORE (Save Time)

❌ Don't check every ticket in CASPBM  
❌ Don't read old comments (just latest)  
❌ Don't track tickets not relevant to AI  
❌ Don't spend >10 min/day on Jira

**Your time is valuable - focus on CR143 + your work, let Tom track everything else.**

---

**Created:** Nov 24, 2025  
**Status:** Ready to use  
**Review:** Weekly (adjust as needed)

