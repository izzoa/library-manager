# Docker Setup

Complete guide for running Library Manager in Docker.

## Quick Start

```bash
git clone https://github.com/deucebucket/library-manager.git
cd library-manager

# Edit docker-compose.yml - change the audiobook path
docker-compose up -d
```

## Understanding Volume Mounts

**This is the most important concept.**

Docker containers are isolated. They can't see your files unless you mount them:

```yaml
volumes:
  # HOST_PATH:CONTAINER_PATH
  - /your/audiobooks:/audiobooks
```

| Path Type | Example | Where to Use |
|-----------|---------|--------------|
| Host path | `/mnt/user/media/audiobooks` | docker-compose.yml (left of `:`) |
| Container path | `/audiobooks` | Settings page in web UI |

**The Settings page cannot access paths that aren't mounted!**

## Platform Examples

### UnRaid

```yaml
volumes:
  - /mnt/user/media/audiobooks:/audiobooks
  - /mnt/user/appdata/library-manager:/data
```

### Synology

```yaml
volumes:
  - /volume1/media/audiobooks:/audiobooks
  - /volume1/docker/library-manager:/data
```

### Standard Linux

```yaml
volumes:
  - /home/user/audiobooks:/audiobooks
  - ./data:/data
```

## Full docker-compose.yml

```yaml
version: "3.8"

services:
  library-manager:
    build: .
    container_name: library-manager
    restart: unless-stopped
    ports:
      - "5060:5060"
    volumes:
      # ⚠️ CHANGE THIS to your audiobook path
      - /path/to/audiobooks:/audiobooks
      - ./data:/data
    environment:
      - TZ=America/Chicago
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5060/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Multiple Libraries

```yaml
volumes:
  - /disk1/audiobooks:/audiobooks
  - /disk2/more-books:/library2
  - ./data:/data
```

Then in Settings, add both paths:
```
/audiobooks
/library2
```

## Dockge Setup

1. Click **+ Compose**
2. Name: `library-manager`
3. Paste the compose content above
4. Edit the volume path
5. Click **Deploy**

## Portainer Setup

1. Go to **Stacks** → **Add Stack**
2. Name: `library-manager`
3. Paste compose content or use Repository URL
4. Deploy

## Troubleshooting

### "Path doesn't exist"
You entered a host path in Settings instead of the container path. Use `/audiobooks` (or whatever you mapped it to).

### Permission denied
Container can't read/write your files. Check folder permissions on the host.

### Container won't start
```bash
docker logs library-manager
```
