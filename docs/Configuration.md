# Configuration

All settings are configured through the web UI at **Settings**.

## Settings Tabs

### General Tab

| Setting | Default | Description |
|---------|---------|-------------|
| Library Paths | `[]` | Folders to scan (one per line) |
| Naming Format | `author/title` | Folder structure for renames |
| Series Grouping | `false` | Enable `Author/Series/# - Title` format |
| Auto-Fix | `false` | Automatically apply safe fixes |
| Protect Author Changes | `true` | Require approval for drastic author changes |
| Scan Interval | `6 hours` | How often to auto-scan |

### AI Setup Tab

| Setting | Description |
|---------|-------------|
| AI Provider | Gemini (recommended) or OpenRouter |
| API Key | Your API key from the provider |
| Model | Which AI model to use |

### Advanced Tab

- Danger Zone (reset database, clear history)
- Bug report generator
- Live logs

## Naming Formats

| Format | Example |
|--------|---------|
| `author/title` | `Brandon Sanderson/Mistborn/` |
| `author - title` | `Brandon Sanderson - Mistborn/` |

## Series Grouping

When enabled, books in a series get organized as:

```
Author/Series Name/1 - Book Title/
Author/Series Name/2 - Book Title/
```

Standalone books stay as `Author/Title/`.

## Rate Limits

| Provider | Free Tier |
|----------|-----------|
| Gemini | 14,400 calls/day |
| OpenRouter | Varies by model |

The app defaults to 2000 calls/hour to stay well under limits.

## Config Files

Settings are stored in:
- `config.json` - General settings
- `secrets.json` - API keys (gitignored)
- `library.db` - Database

For Docker, these are stored in the `/data` volume.
