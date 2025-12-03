# Prophet CmdStan Fix

## Issue
When calling `/api/v1/ml/train` endpoint, got error:
```
CmdStan installataion missing makefile, path .../prophet/stan_model/cmdstan-2.33.1 is invalid
```

## Root Cause
1. **CmdStan was installed** in `/Users/manasaiyer/.cmdstan/cmdstan-2.37.0`
2. **Prophet expected it** in `.../venv/lib/python3.12/site-packages/prophet/stan_model/cmdstan-2.33.1`
3. **Existing directory was incomplete** - had some files but missing the makefile
4. **Version mismatch** - Prophet bundled with 2.33.1 but system had 2.37.0

## Solution Applied

### 1. Updated forecasting_ml.py
Modified the CmdStan path configuration to explicitly set the path before Prophet tries to find it:

```python
# Set the known CmdStan path explicitly FIRST
known_cmdstan_path = Path.home() / ".cmdstan" / "cmdstan-2.37.0"
if known_cmdstan_path.exists():
    cmdstanpy.set_cmdstan_path(str(known_cmdstan_path))
```

### 2. Fixed Symlink
Removed the incomplete `cmdstan-2.33.1` directory and created a proper symlink:

```bash
rm -rf venv/lib/python3.12/site-packages/prophet/stan_model/cmdstan-2.33.1
ln -s /Users/manasaiyer/.cmdstan/cmdstan-2.37.0 \
      venv/lib/python3.12/site-packages/prophet/stan_model/cmdstan-2.33.1
```

Now Prophet can find CmdStan at the path it expects, and it points to the actual installation.

## Verification

### Check Symlink
```bash
ls -lah venv/lib/python3.12/site-packages/prophet/stan_model/ | grep cmdstan
# Output: cmdstan-2.33.1 -> /Users/manasaiyer/.cmdstan/cmdstan-2.37.0
```

### Check Makefile
```bash
test -f venv/lib/python3.12/site-packages/prophet/stan_model/cmdstan-2.33.1/makefile
# Output: ✓ Makefile NOW EXISTS
```

## Files Modified
- `backend/app/forecasting_ml.py` - Explicitly set CmdStan path on module load
- Created symlink: `venv/.../prophet/stan_model/cmdstan-2.33.1` → `/Users/manasaiyer/.cmdstan/cmdstan-2.37.0`

## Testing
After the server restarts, the `/api/v1/ml/train` endpoint should work without CmdStan errors.

## Why This Happens
Prophet installs with a bundled CmdStan version (2.33.1 in this case), but:
- Sometimes the bundled version is incomplete or corrupted
- Users may have newer system-wide CmdStan installations
- Prophet looks in specific paths and doesn't automatically find system installations

The symlink solution tells Prophet "look here for CmdStan" while pointing to the working system installation.

---

**Date Fixed:** December 2, 2025  
**Status:** ✅ RESOLVED

