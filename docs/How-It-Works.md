# How It Works

## The Pipeline

```
Your Messy Folder → Scan → Search APIs → AI Verify → Rename
```

### Step 1: Scan

The scanner looks for issues like:
- Year in author name (`The Expanse 2019`)
- Author/title swapped (`Mistborn/Brandon Sanderson`)
- Missing first name (`Boyett/The Hollow Man`)
- Junk in filename (`[site.to] Author - Book`)
- Placeholder author (`Unknown/Book Title`)

### Step 2: Search APIs

Books are searched across multiple databases:

1. **Audnexus** - Audible's audiobook database (best for audiobooks)
2. **OpenLibrary** - Internet Archive's massive book DB
3. **Google Books** - Wide coverage, good series info
4. **Hardcover** - Modern and indie titles

### Step 3: AI Verification

When metadata is found, AI verifies it makes sense:

| Scenario | Action |
|----------|--------|
| Minor change (e.g., "Boyett" → "Steven Boyett") | Auto-applied |
| Drastic change (e.g., "Golden" → "Sussman") | Requires approval |
| Garbage match (< 30% word overlap) | Rejected |
| Uncertain | Held for review |

### Step 4: Rename

If approved (automatically or manually), the folder is renamed.

## Garbage Match Filtering

APIs sometimes return completely wrong books. The app uses **Jaccard similarity** to detect these:

```
✗ "Chapter 19" → "College Accounting" (only "chapter" matches)
✗ "Death Genesis" → "The Darkborn Genesis" (only "genesis" matches)
```

Matches with less than 30% word overlap are automatically rejected.

## Series Detection

Series info is extracted from:

1. **API metadata** - Google Books, Audnexus provide series info
2. **Folder names** - Parses patterns like:
   - `Series Name, Book 8: Title`
   - `Mistborn Book 1: The Final Empire`
   - `The Expanse #3 - Abaddon's Gate`
3. **Author folder** - If folder contains "Series", "Saga", etc.

## Narrator Preservation

Different audiobook versions are kept separate:

```
The Hellbound Heart (Kafer)/   ← Narrator 1
The Hellbound Heart (Barker)/  ← Narrator 2
```

The app detects narrator names in parentheses and preserves them.

## Safety Features

- **Drastic changes always require approval**
- **Every fix can be undone**
- **History tracks all changes**
- **Garbage matches are filtered out**
