---
description: HEMN System - Git Sync & Safety Recovery
---

This workflow ensures that every significant change is backed up and provides a fast "emergency exit" if something breaks.

### 1. Synchronous Backup (Sync)
Whenever a task is completed:
1.  **Add Changes**: `git add .`
2.  **Commit with Context**: `git commit -m "Round [X]: [Brief description of what was fixed/added]"`
3.  **Push to Cloud**: `git push origin main`

### 2. Emergency Recovery (Rollback)
If the system stops working after a change:
1.  **Find the Last Stable Version**: `git log --oneline -n 5`
2.  **Return to Safety**: `git reset --hard HEAD~1` (reverts to the immediately preceding state)
3.  **Deploy Immediately**: Run `python deploy_vps.py` to restore the VPS to the last known working code.

### 3. Stability Check
After any rollback or major sync:
- Check `server_error.log` for new entries.
- Run `python test_vps_api.py` to confirm the API is still alive.
