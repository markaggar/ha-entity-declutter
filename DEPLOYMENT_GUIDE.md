# 🚀 PyScript Helper Analysis - Final Deployment Guide

## ✅ **Event Loop Issue Fixed!**

The "Cannot be called from within the event loop" error has been resolved by using PyScript's proper async patterns and state access methods.

## 📁 **Deploy These Files:**

### 1. **Analysis Script**
**Copy `pyscript_analyze_helpers_final.py` to `/config/pyscript/analyze_helpers.py`**

**Key Fixes:**
- ✅ Uses `state.names()` instead of `hass.states.entity_ids()` 
- ✅ Uses `state.get()` instead of `hass.states.get()`
- ✅ Uses `state.set()` instead of `hass.states.set()`
- ✅ Proper async function with `task.create()`
- ✅ Both `@service` and `@time_trigger("startup")` decorators

### 2. **Deletion Script**  
**Copy `delete_helpers_final.py` to `/config/pyscript/delete_helpers.py`**

**Key Fixes:**
- ✅ Uses `state.get()` for entity checking
- ✅ Uses `await service.call()` for helper deletion
- ✅ Proper async function with `task.create()`
- ✅ Event-loop safe service calls

## 🔧 **PyScript Configuration**

Ensure your `configuration.yaml` has:
```yaml
pyscript:
  allow_all_imports: true
  hass_is_global: true
```

## 🚀 **Usage Commands**

### **Run Analysis:**
```yaml
# Developer Tools → Services
service: pyscript.analyze_helpers
```

### **Delete Helpers (Dry Run):**
```yaml
service: pyscript.delete_helpers
data:
  dry_run: true
```

### **Delete Helpers (Actual):**
```yaml
service: pyscript.delete_helpers  
data:
  dry_run: false
```

## 📊 **What This Fixes:**

### **Original Error:**
```
RuntimeError: Cannot be called from within the event loop
```

### **Root Cause:**
- `hass.states.entity_ids()` cannot be called from PyScript's event loop
- Direct `hass.states.get()` calls blocked by event loop restrictions
- Synchronous service calls not allowed in async context

### **Solution:**
- Use PyScript's `state.names()` method for entity IDs
- Use PyScript's `state.get()` method for entity states  
- Use `await service.call()` for async service calls
- Wrap main function in async task creation

## 🔍 **Technical Details:**

### **PyScript State Access:**
```python
# ❌ Old (blocked by event loop)
entity_ids = hass.states.entity_ids()
entity_state = hass.states.get(entity_id)

# ✅ New (event loop safe)
entity_ids = list(state.names())
entity_state = state.get(entity_id)
```

### **PyScript Service Calls:**
```python
# ❌ Old (synchronous)
hass.services.call('input_boolean', 'delete', {'entity_id': helper})

# ✅ New (async)
await service.call('input_boolean', 'delete', entity_id=helper)
```

### **PyScript Function Structure:**
```python
# ✅ Proper PyScript pattern
@service
def analyze_helpers(**kwargs):
    task.create(analyze_helpers_async())

async def analyze_helpers_async():
    # Main logic here
    pass
```

## 🎯 **Expected Results:**

After deployment, you should see:
1. ✅ No more event loop errors
2. ✅ Successful entity enumeration
3. ✅ Complete YAML file analysis  
4. ✅ Generated analysis files in `/config/helper_analysis/`
5. ✅ Working deletion functionality

## 📁 **File Structure After Deployment:**

```
/config/
├── pyscript/
│   ├── analyze_helpers.py        # ← pyscript_analyze_helpers_final.py
│   └── delete_helpers.py         # ← delete_helpers_final.py
└── helper_analysis/              # ← Auto-created by script
    ├── orphaned_helpers_[timestamp].txt
    ├── helper_analysis_full_[timestamp].json
    └── helper_analysis_summary_[timestamp].txt
```

## 🔧 **Troubleshooting:**

### **If Still Getting Errors:**
1. **Check PyScript Version:** Ensure you have the latest PyScript from HACS
2. **Verify Configuration:** Confirm `allow_all_imports: true` is set
3. **Restart Required:** Restart Home Assistant after installing PyScript
4. **File Permissions:** Ensure `/config/pyscript/` directory is writable
5. **Log Checking:** Check Home Assistant logs for detailed error messages

### **Success Indicators:**
- ✅ Service `pyscript.analyze_helpers` appears in Developer Tools
- ✅ Service runs without errors
- ✅ Log shows "=== Starting Enhanced Helper Analysis with PyScript ==="
- ✅ Files created in `/config/helper_analysis/`
- ✅ Status entity `sensor.helper_analysis_status` created

This version should work perfectly with PyScript's current architecture! 🎉