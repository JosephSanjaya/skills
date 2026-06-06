# Zero-Downtime Database Migrations

## Expand-and-Contract Pattern

Decouple schema changes from code deployment. Never apply destructive updates in same release.

### Phase 1: Expand (Additive Only)
Add new table/columns. Old app versions ignore them. Nullable or default values mandatory.
```sql
-- V2__add_display_name.sql (Additive)
ALTER TABLE users ADD COLUMN display_name VARCHAR(255);
```

### Phase 2: Dual-Write
Deploy app update. Writes data to both `user_name` (old) and `display_name` (new). Reads from `user_name` with fallback to `display_name`.

### Phase 3: Backfill
Sync existing records from old columns to new columns. Run via background worker in small chunks to avoid locking table.
```sql
-- Batch backfill (do not run inside migration script)
UPDATE users SET display_name = user_name WHERE display_name IS NULL LIMIT 10000;
```

### Phase 4: Contract (Destructive)
Deploy app update reading only `display_name`. Verify telemetry. Deploy final migration to drop old columns.
```sql
-- V4__drop_user_name.sql (Destructive)
ALTER TABLE users DROP COLUMN user_name;
```

---

## Guardrails & CI/CD Checks

- Parse SQL files in lint step. Fail PR if contains `DROP`, `RENAME`, `ALTER TABLE ... DROP COLUMN`, or `ALTER TABLE ... ALTER COLUMN ... SET NOT NULL` without override flag.
- Limit lock wait times on heavy tables. Set `lock_timeout` in PostgreSQL.
- Prevent concurrent migrations. Ensure tool uses database advisory locks.
- K8s migration runner config: `backoffLimit: 3`, `activeDeadlineSeconds: 300` in Job manifest.

---

## Tooling Matrix

| Tool | Format | Key Strengths |
|------|--------|---------------|
| **Flyway** | Pure SQL, Java | Fast setup, SQL-native, predictable migrations |
| **Liquibase** | XML, YAML, JSON, SQL | Automatic rollback generation, database-agnostic |

---

## Rollback & Sync Strategies

- **Fix Forward**: Standard choice. Build correction migration, roll forward. Minimize data-loss risk.
- **Reverse Scripts**: Liquibase/manual rollbacks. Warning: drops columns, deletes data permanently.
- **ArgoCD PreSync Hook**: Execute migrations before pod rollover. If job fails, deployment stops automatically.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrator
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/sync-wave: "-5"
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: flyway/flyway:latest
        args: ["migrate"]
      restartPolicy: Never
```
