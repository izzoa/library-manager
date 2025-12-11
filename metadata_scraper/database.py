"""
Book Metadata Database Schema and Operations
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'metadata.db'

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    """Initialize the metadata database schema."""
    conn = get_db()
    c = conn.cursor()

    # Authors table
    c.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            name_normalized TEXT NOT NULL,  -- lowercase, no punctuation for matching
            aliases TEXT,  -- JSON array of alternate names
            bio TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name_normalized)
        )
    ''')

    # Series table
    c.execute('''
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            name_normalized TEXT NOT NULL,
            author_id INTEGER,
            total_books INTEGER,
            description TEXT,
            genre TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            UNIQUE(name_normalized, author_id)
        )
    ''')

    # Books table
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            title_normalized TEXT NOT NULL,
            author_id INTEGER,
            series_id INTEGER,
            series_position REAL,  -- supports 1.5, 2.5 for novellas
            year_published INTEGER,
            isbn TEXT,
            isbn13 TEXT,
            asin TEXT,  -- Amazon ID for audiobooks
            description TEXT,
            page_count INTEGER,
            genres TEXT,  -- JSON array
            narrators TEXT,  -- JSON array for audiobooks
            duration_minutes INTEGER,  -- audiobook length
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            FOREIGN KEY (series_id) REFERENCES series(id)
        )
    ''')

    # Sources table - track where data came from
    c.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            entity_type TEXT NOT NULL,  -- 'author', 'series', 'book'
            entity_id INTEGER NOT NULL,
            source_name TEXT NOT NULL,  -- 'bookseriesinorder', 'fictiondb', 'openlibrary', 'goodreads'
            source_url TEXT,
            source_id TEXT,  -- ID in the source system
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Scrape progress table - track what we've scraped
    c.execute('''
        CREATE TABLE IF NOT EXISTS scrape_progress (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            last_page INTEGER DEFAULT 0,
            last_item TEXT,
            total_items INTEGER,
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, paused
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            UNIQUE(source)
        )
    ''')

    # Rate limit tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            requests_made INTEGER DEFAULT 0,
            window_start TIMESTAMP,
            max_per_hour INTEGER DEFAULT 100,
            last_request TIMESTAMP,
            UNIQUE(source)
        )
    ''')

    # Create indexes for fast lookups
    c.execute('CREATE INDEX IF NOT EXISTS idx_authors_normalized ON authors(name_normalized)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_series_normalized ON series(name_normalized)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_books_normalized ON books(title_normalized)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_books_series ON books(series_id, series_position)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_books_author ON books(author_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_books_isbn13 ON books(isbn13)')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def normalize_text(text):
    """Normalize text for matching - lowercase, remove punctuation."""
    if not text:
        return ''
    import re
    # Lowercase
    text = text.lower()
    # Remove common articles at start
    text = re.sub(r'^(the|a|an)\s+', '', text)
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def add_author(name, aliases=None, bio=None, birth_year=None, death_year=None, source=None, source_url=None):
    """Add or update an author."""
    import json
    conn = get_db()
    c = conn.cursor()

    normalized = normalize_text(name)
    aliases_json = json.dumps(aliases) if aliases else None

    try:
        c.execute('''
            INSERT INTO authors (name, name_normalized, aliases, bio, birth_year, death_year)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name_normalized) DO UPDATE SET
                aliases = COALESCE(excluded.aliases, authors.aliases),
                bio = COALESCE(excluded.bio, authors.bio),
                updated_at = CURRENT_TIMESTAMP
        ''', (name, normalized, aliases_json, bio, birth_year, death_year))

        author_id = c.lastrowid or c.execute(
            'SELECT id FROM authors WHERE name_normalized = ?', (normalized,)
        ).fetchone()['id']

        if source:
            c.execute('''
                INSERT OR REPLACE INTO sources (entity_type, entity_id, source_name, source_url, scraped_at)
                VALUES ('author', ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (author_id, source, source_url))

        conn.commit()
        return author_id
    finally:
        conn.close()

def add_series(name, author_id=None, total_books=None, description=None, genre=None, source=None, source_url=None):
    """Add or update a series."""
    conn = get_db()
    c = conn.cursor()

    normalized = normalize_text(name)

    try:
        c.execute('''
            INSERT INTO series (name, name_normalized, author_id, total_books, description, genre)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name_normalized, author_id) DO UPDATE SET
                total_books = COALESCE(excluded.total_books, series.total_books),
                description = COALESCE(excluded.description, series.description),
                updated_at = CURRENT_TIMESTAMP
        ''', (name, normalized, author_id, total_books, description, genre))

        series_id = c.lastrowid or c.execute(
            'SELECT id FROM series WHERE name_normalized = ? AND (author_id = ? OR (author_id IS NULL AND ? IS NULL))',
            (normalized, author_id, author_id)
        ).fetchone()['id']

        if source:
            c.execute('''
                INSERT OR REPLACE INTO sources (entity_type, entity_id, source_name, source_url, scraped_at)
                VALUES ('series', ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (series_id, source, source_url))

        conn.commit()
        return series_id
    finally:
        conn.close()

def add_book(title, author_id=None, series_id=None, series_position=None, year_published=None,
             isbn=None, isbn13=None, asin=None, description=None, narrators=None, source=None, source_url=None):
    """Add or update a book."""
    import json
    conn = get_db()
    c = conn.cursor()

    normalized = normalize_text(title)
    narrators_json = json.dumps(narrators) if narrators else None

    try:
        c.execute('''
            INSERT INTO books (title, title_normalized, author_id, series_id, series_position,
                              year_published, isbn, isbn13, asin, description, narrators)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, normalized, author_id, series_id, series_position,
              year_published, isbn, isbn13, asin, description, narrators_json))

        book_id = c.lastrowid

        if source:
            c.execute('''
                INSERT INTO sources (entity_type, entity_id, source_name, source_url, scraped_at)
                VALUES ('book', ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (book_id, source, source_url))

        conn.commit()
        return book_id
    finally:
        conn.close()

def find_series(name, author_name=None):
    """Find a series by name and optionally author."""
    conn = get_db()
    c = conn.cursor()

    normalized = normalize_text(name)

    if author_name:
        author_norm = normalize_text(author_name)
        c.execute('''
            SELECT s.*, a.name as author_name
            FROM series s
            LEFT JOIN authors a ON s.author_id = a.id
            WHERE s.name_normalized LIKE ? AND a.name_normalized LIKE ?
        ''', (f'%{normalized}%', f'%{author_norm}%'))
    else:
        c.execute('''
            SELECT s.*, a.name as author_name
            FROM series s
            LEFT JOIN authors a ON s.author_id = a.id
            WHERE s.name_normalized LIKE ?
        ''', (f'%{normalized}%',))

    results = c.fetchall()
    conn.close()
    return [dict(r) for r in results]

def get_series_books(series_id):
    """Get all books in a series, ordered by position."""
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT b.*, a.name as author_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        WHERE b.series_id = ?
        ORDER BY b.series_position
    ''', (series_id,))

    results = c.fetchall()
    conn.close()
    return [dict(r) for r in results]

def get_stats():
    """Get database statistics."""
    conn = get_db()
    c = conn.cursor()

    stats = {}
    for table in ['authors', 'series', 'books', 'sources']:
        c.execute(f'SELECT COUNT(*) FROM {table}')
        stats[table] = c.fetchone()[0]

    conn.close()
    return stats

if __name__ == '__main__':
    init_db()
    print("Stats:", get_stats())
