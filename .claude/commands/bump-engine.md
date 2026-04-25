---
description: Pull latest soccercv engine commits and bump the submodule pointer
---

```bash
git -C soccercv_engine pull origin main
uv pip install -e soccercv_engine/ --extra-index-url https://download.pytorch.org/whl/cpu
git add soccercv_engine
git commit -m "bump engine to latest"
```
