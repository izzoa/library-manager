# Troubleshooting

## Common Issues

### "Path doesn't exist" (Docker)

**Cause:** You entered your host path in Settings instead of the container path.

**Fix:**
1. Check your docker-compose.yml volume mount: `- /host/path:/audiobooks`
2. In Settings, use `/audiobooks` (the right side of the `:`)

### Wrong author detected

**Fix:**
1. Go to **Pending** or **History**
2. Find the incorrect suggestion
3. Click **✗ Reject** to delete it
4. Book will be marked as "verified OK"

### Want to undo a fix

**Fix:**
1. Go to **History**
2. Find the change
3. Click **↩ Undo**
4. Folder renames back to original

### Error entry for file that doesn't exist

**Fix:**
1. Go to **History**
2. Find the error entry
3. Click **🗑 Dismiss**

### Series not detected

1. Make sure **Series Grouping** is enabled in Settings
2. The title pattern must be recognizable
3. Try a deep rescan - Dashboard → Deep Re-scan

### Rate limit reached

The app has a self-imposed rate limit to avoid hitting API limits. Wait an hour or adjust the limit in Settings → Advanced.

### Database locked errors

Usually happens when multiple operations run simultaneously. The app handles this automatically with timeouts. If persistent, restart the app.

### Books being skipped

Some folders are intentionally skipped:
- **System folders** (`metadata/`, `tmp/`, `cache/`)
- **Series folders** (folders containing multiple book subfolders)
- **Complete collections** (`Complete Series`, `Box Set`, etc.)

### Permission denied

**Docker:** Make sure the container can read/write your audiobook folder.

**Linux:** Check folder permissions:
```bash
chmod -R 755 /path/to/audiobooks
```

## Getting More Help

### Check Logs

**Direct install:**
```bash
tail -f app.log
```

**Docker:**
```bash
docker logs library-manager
```

### Bug Reports

Go to **Settings** → **Advanced** → **Generate Bug Report**

This creates a report with:
- App version
- Configuration (no secrets)
- Recent errors
- System info

### Still Stuck?

- [GitHub Issues](https://github.com/deucebucket/library-manager/issues)
- [GitHub Discussions](https://github.com/deucebucket/library-manager/discussions)
