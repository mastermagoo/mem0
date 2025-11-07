# Namespace Integration Notes

**Date:** 2025-10-16
**Worker:** Worker 3 (Data Architect)

---

## Namespace Count Discrepancy

### Worker 3 Design (This Implementation)
**5 Core Namespaces:**
1. `progressief` - Business consulting
2. `cv_automation` - Job search
3. `investments` - Financial tracking
4. `personal` - Personal life
5. `intel_system` - Infrastructure

### Existing Telegram Bot Implementation
**7 Namespaces:**
1. `personal`
2. `progressief`
3. `cv_automation`
4. `investments`
5. `intel_system`
6. `ai_projects` (EXTRA)
7. `vectal` (EXTRA)

---

## Resolution Options

### Option 1: Use 5 Core Namespaces (Recommended)
**Rationale:**
- Simpler, cleaner architecture
- Focused on Mark's primary life contexts
- ai_projects and vectal can use `intel_system` namespace
- Easier to maintain and understand

**Changes Required:**
- Update `telegram_bot/handlers/namespace.py` to remove `ai_projects` and `vectal`
- Update Telegram bot config to use 5 namespaces
- Update `NAMESPACE_INFO` emoji mappings

### Option 2: Expand to 7 Namespaces
**Rationale:**
- Telegram bot already supports it
- Separates AI projects from infrastructure
- More granular organization

**Changes Required:**
- Add `ai_projects` and `vectal` to `namespace_manager.py` NamespaceRegistry
- Add retention policies for new namespaces
- Update PostgreSQL constraint to allow 7 namespaces
- Update Neo4j validation
- Update documentation

---

## Recommended Action

**Use 5 Core Namespaces** for simplicity and clarity.

### Implementation Steps:

1. Update `telegram_bot/handlers/namespace.py`:
```python
NAMESPACE_INFO = {
    'personal': {'emoji': '👤', 'desc': 'Personal notes & reminders'},
    'progressief': {'emoji': '🏢', 'desc': 'Progressief B.V. consulting business'},
    'cv_automation': {'emoji': '💼', 'desc': 'Job search and CV generation'},
    'investments': {'emoji': '💰', 'desc': 'Investment tracking and analysis'},
    'intel_system': {'emoji': '🖥', 'desc': 'Infrastructure and technical projects'}
}
```

2. Update Telegram bot config namespaces list to 5

3. Map existing usage:
   - `ai_projects` → `intel_system` (both are technical)
   - `vectal` → `intel_system` (development project)

---

## Namespace Manager vs Telegram Bot

### Worker 3 Implementation (namespace_manager.py)
- ✅ Thread-safe context management
- ✅ Composite user_id format (`user/namespace`)
- ✅ Validation and access control
- ✅ Retention policies defined
- ✅ 5 core namespaces

### Telegram Bot Implementation
- ✅ User-friendly emoji interface
- ✅ Inline keyboard for switching
- ✅ Stats display
- ✅ Quick `/switch` command
- ⚠️  7 namespaces (needs alignment)

---

## Integration Checklist

When integrating Worker 3's namespace system with Telegram bot:

- [ ] Decide on 5 or 7 namespaces (recommend 5)
- [ ] Update `NAMESPACE_INFO` in `telegram_bot/handlers/namespace.py`
- [ ] Update Telegram bot config to match namespace list
- [ ] Import `namespace_manager` into Telegram bot
- [ ] Use `NamespaceContext.format_user_id()` for user IDs
- [ ] Test namespace switching via Telegram
- [ ] Verify isolation via `/stats` command in different namespaces

---

## Example Integration

```python
# In telegram_bot main file
from namespace_manager import NamespaceContext, NamespaceRegistry

# When user switches namespace
async def namespace_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_namespace = query.data.replace('ns_', '')

    # Validate using NamespaceRegistry
    if not NamespaceRegistry.is_valid_namespace(new_namespace):
        await query.answer("Invalid namespace!")
        return

    # Set in context manager
    NamespaceContext.set_namespace(new_namespace)

    # Store in user_data for persistence
    context.user_data['namespace'] = new_namespace

    # Format user_id for mem0
    user_id = NamespaceContext.format_user_id('mark_carey', new_namespace)
    # user_id is now 'mark_carey/progressief' (for example)

    # Use for mem0 operations
    mem0.add(message, user_id=user_id)
```

---

## Files to Review

1. `/Volumes/intel-system/deployment/docker/mem0_tailscale/telegram_bot/handlers/namespace.py`
   - Update `NAMESPACE_INFO` to 5 namespaces
   - Import `namespace_manager`

2. `/Volumes/intel-system/deployment/docker/mem0_tailscale/telegram_bot/config.py`
   - Update `namespaces` list to 5 core namespaces

3. `/Volumes/intel-system/deployment/docker/mem0_tailscale/telegram_bot/main.py`
   - Import `NamespaceContext`
   - Use for user_id formatting

---

## Next Steps

1. **Coordinator Decision:** 5 or 7 namespaces?
2. **If 5:** Update Telegram bot to remove extras
3. **If 7:** Extend Worker 3 implementation to include ai_projects and vectal
4. **Then:** Integrate namespace_manager with Telegram bot
5. **Finally:** Test end-to-end namespace isolation

---

**Recommendation:** Stick with 5 core namespaces for simplicity. Map ai_projects and vectal to intel_system.
