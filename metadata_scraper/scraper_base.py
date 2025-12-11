"""
Base scraper class with rate limiting and progress tracking.
"""
import time
import random
import requests
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from database import get_db

class BaseScraper(ABC):
    """Base class for all scrapers with rate limiting."""

    SOURCE_NAME = 'unknown'
    REQUESTS_PER_HOUR = 100  # Override in subclass
    MIN_DELAY = 2  # Minimum seconds between requests
    MAX_DELAY = 5  # Maximum seconds between requests

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        self._init_rate_limit()

    def _init_rate_limit(self):
        """Initialize or load rate limit tracking."""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO rate_limits (source, max_per_hour)
            VALUES (?, ?)
        ''', (self.SOURCE_NAME, self.REQUESTS_PER_HOUR))
        conn.commit()
        conn.close()

    def _check_rate_limit(self):
        """Check if we can make a request, wait if needed."""
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM rate_limits WHERE source = ?', (self.SOURCE_NAME,))
        rate = dict(c.fetchone())

        now = datetime.now()
        window_start = datetime.fromisoformat(rate['window_start']) if rate['window_start'] else now

        # Reset window if more than an hour has passed
        if now - window_start > timedelta(hours=1):
            c.execute('''
                UPDATE rate_limits
                SET requests_made = 0, window_start = ?
                WHERE source = ?
            ''', (now.isoformat(), self.SOURCE_NAME))
            conn.commit()
            rate['requests_made'] = 0

        # If at limit, wait until window resets
        if rate['requests_made'] >= rate['max_per_hour']:
            wait_time = (window_start + timedelta(hours=1) - now).total_seconds()
            if wait_time > 0:
                print(f"Rate limit reached for {self.SOURCE_NAME}. Waiting {wait_time:.0f}s...")
                conn.close()
                time.sleep(wait_time + 1)
                return self._check_rate_limit()  # Recursive check after waiting

        conn.close()
        return True

    def _record_request(self):
        """Record that we made a request."""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            UPDATE rate_limits
            SET requests_made = requests_made + 1,
                last_request = ?,
                window_start = COALESCE(window_start, ?)
            WHERE source = ?
        ''', (datetime.now().isoformat(), datetime.now().isoformat(), self.SOURCE_NAME))
        conn.commit()
        conn.close()

    def _random_delay(self):
        """Wait a random time between requests."""
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        time.sleep(delay)

    def fetch(self, url, **kwargs):
        """Fetch a URL with rate limiting."""
        self._check_rate_limit()
        self._random_delay()

        try:
            response = self.session.get(url, timeout=30, **kwargs)
            self._record_request()

            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Got 429 - waiting {retry_after}s...")
                time.sleep(retry_after)
                return self.fetch(url, **kwargs)

            if response.status_code == 403:
                print(f"Got 403 Forbidden on {url} - may need to rotate user agent or use proxy")
                return None

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_progress(self):
        """Get scraping progress for this source."""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM scrape_progress WHERE source = ?', (self.SOURCE_NAME,))
        result = c.fetchone()
        conn.close()
        return dict(result) if result else None

    def save_progress(self, last_page=None, last_item=None, total_items=None, status='in_progress'):
        """Save scraping progress."""
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO scrape_progress (source, last_page, last_item, total_items, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                last_page = COALESCE(?, scrape_progress.last_page),
                last_item = COALESCE(?, scrape_progress.last_item),
                total_items = COALESCE(?, scrape_progress.total_items),
                status = ?,
                completed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
        ''', (self.SOURCE_NAME, last_page, last_item, total_items, status, datetime.now().isoformat(),
              last_page, last_item, total_items, status, status))
        conn.commit()
        conn.close()

    @abstractmethod
    def scrape_all(self):
        """Scrape all data from this source. Override in subclass."""
        pass

    @abstractmethod
    def scrape_series(self, series_name):
        """Scrape a specific series. Override in subclass."""
        pass
