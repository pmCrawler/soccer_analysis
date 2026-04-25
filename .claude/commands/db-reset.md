---
description: Drop and recreate the local database from scratch
---

Destroys all data. Use only in local dev when you need a clean slate after model changes.

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS soccercv_db;"
psql -U postgres -c "CREATE DATABASE soccercv_db OWNER soccercv_user;"
alembic upgrade head
python -m backend.db.seed
```
