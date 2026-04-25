---
description: Verify all Reflex components build without errors
---

Run a full Python import + build check across every component and state module. Catches ObjectItemOperation arithmetic errors, invalid icon names, and missing imports before running the app.

```bash
python -c "
from app.components.dashboard import dashboard_view
from app.components.upload import upload_wizard
from app.components.report import report_view
from app.components.player import player_view
from app.components.settings import settings_view
from app.components.calibration import calibration_view
from app.components.shell import app_shell
dashboard_view(); upload_wizard(); report_view()
player_view(); settings_view(); calibration_view()
print('ALL COMPONENTS OK')
"
```
