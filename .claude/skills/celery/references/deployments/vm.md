---
name: Celery VM Deployment
description: Systemd and supervisor patterns for celery beat and workers on bare-metal/VMs
---

# VM / Bare-Metal Deployment

## Systemd Service — Worker

```ini
# /etc/systemd/system/celery-worker.service
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/opt/app
Environment=DJANGO_SETTINGS_MODULE=config.settings_celery_light
Environment=CELERY_BROKER_URL=redis://localhost:6379/1
ExecStart=/opt/app/venv/bin/celery -A proj multi start w1 w2 \
    -Q default \
    --pidfile=/run/celery/%%n.pid \
    --logfile=/var/log/celery/%%n%%I.log \
    --loglevel=INFO
ExecStop=/opt/app/venv/bin/celery multi stopwait w1 w2 \
    --pidfile=/run/celery/%%n.pid
ExecReload=/opt/app/venv/bin/celery multi restart w1 w2 \
    --pidfile=/run/celery/%%n.pid
Restart=always
RuntimeDirectory=celery

[Install]
WantedBy=multi-user.target
```

## Systemd Service — Beat

```ini
# /etc/systemd/system/celery-beat.service
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=celery
Group=celery
WorkingDirectory=/opt/app
Environment=DJANGO_SETTINGS_MODULE=backend.settings
ExecStart=/opt/app/venv/bin/celery -A proj beat \
    --loglevel=INFO \
    --schedule=/var/lib/celery/beat-schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

## Off-Host Workers (Remote VMs)

Workers on remote hosts need only broker connectivity. No DB, no app server:

```ini
# /etc/systemd/system/celery-worker.service (remote host)
[Service]
Environment=DJANGO_SETTINGS_MODULE=config.settings_celery_light
Environment=CELERY_BROKER_URL=redis://broker-host.internal:6379/1
Environment=INTERNAL_API_URL=https://api.example.com/api/internal
Environment=INTERNAL_SERVICE_TOKEN=<token>
```

Deploy the worker code (without DB) via:
```bash
rsync -az --exclude='*.sqlite3' --exclude='.env' ./backend/ worker-host:/opt/app/
```

## Multiple Worker Types

```ini
# celery-worker-cpu.service — CPU-bound tasks
ExecStart=/opt/app/venv/bin/celery -A proj multi start cpu1 cpu2 \
    -Q db_tasks -c 4 --pool=prefork

# celery-worker-io.service — I/O-bound tasks
ExecStart=/opt/app/venv/bin/celery -A proj worker \
    -Q api_tasks -P gevent -c 100 -n io@%%h
```

## Log Rotation

```
# /etc/logrotate.d/celery
/var/log/celery/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    postrotate
        systemctl reload celery-worker 2>/dev/null || true
    endscript
}
```

## Management Commands

```bash
systemctl start celery-worker
systemctl stop celery-worker
systemctl restart celery-worker
systemctl status celery-worker

# Scale by enabling multiple unit instances
systemctl enable celery-worker@1
systemctl enable celery-worker@2
systemctl start celery-worker@{1,2}
```
