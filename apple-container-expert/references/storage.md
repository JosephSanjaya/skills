# Storage

## Named volumes

```bash
container volume create mydata                  # creates EXT4 image
container volume create mydata -s 20g           # explicit size
container volume ls
container volume inspect mydata
container volume rm mydata
```

## The lost+found problem (critical for databases)

EXT4 volume formatting **always injects a `lost+found` directory** at the filesystem root. Database engines that require an empty data directory before running initialization scripts will fail.

**Affected engines:** PostgreSQL (`initdb`), MySQL, MariaDB, ClickHouse, and any engine that checks `readdir()` returns empty before init.

**Error symptom:** `initdb: error: directory "..." exists but is not empty`

**Fix: always use a sub-directory inside the mount point**

```bash
# Wrong — PGDATA points at the volume root, which contains lost+found
container run \
  -e PGDATA=/var/lib/postgresql/data \
  -v pgdata:/var/lib/postgresql/data \
  postgres

# Correct — PGDATA points at a subdirectory inside the mount
container run \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgdata:/var/lib/postgresql/data \
  postgres

# MySQL equivalent
container run \
  -e MYSQL_DATA_DIR=/var/lib/mysql/data \
  -v mysqldata:/var/lib/mysql \
  mysql
```

The volume mount (`/var/lib/postgresql/data`) receives `lost+found`. The actual database files go into the subdirectory (`/pgdata`), which is empty on first boot.

## Bind mounts

```bash
container run -v /host/path:/container/path image
container run -v /host/path:/container/path:ro image                        # read-only
container run --mount type=bind,source=/host/path,target=/container/path image
container run --mount type=bind,source=/host/path,target=/container/path,readonly image
```

**UID/GID gotcha:** No `--userns keep-id` equivalent yet (open feature #165). Bind-mounted files may appear owned by `root` inside the container, breaking non-root workloads. Workaround: `chmod`/`chown` inside container startup, or use named volumes.

**Performance:** Bind-mount write is ~32.6 MB/s vs OrbStack's ~548 MB/s (~17× slower). Avoid hot-reload patterns, `node_modules`, or write-heavy workflows with bind mounts. Prefer:

- **Named volumes** for persistent data (full EXT4 speed)
- **`COPY` in Dockerfile** for static read-only content
- **`container machine`** for dev-in-VM workflows where Linux filesystem speed matters

## File copying

```bash
container cp ./local-file mycontainer:/remote/path      # host → container
container cp mycontainer:/remote/path ./local-dir/      # container → host
```

Relative host paths resolve from current working directory (fixed in v1.x line).

## Storage inspection

```bash
container system df              # disk usage: images, layers, volumes
container inspect web | jq '.Mounts'   # inspect volume/bind mounts on a running container
```

> Key: NEVER point PGDATA/MySQL data dir at volume root — EXT4 lost+found breaks DB init. Mount one level up and use a sub-directory. Named volume I/O (~1,280 MB/s) is fast; bind-mount writes (~32.6 MB/s) are 17× slower than OrbStack.
