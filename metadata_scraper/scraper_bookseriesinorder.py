"""
BookSeriesInOrder.com Scraper
Scrapes 18,000+ series with book ordering information.
"""
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from scraper_base import BaseScraper
from database import init_db, add_author, add_series, add_book, get_db, normalize_text

class BookSeriesInOrderScraper(BaseScraper):
    """Scraper for bookseriesinorder.com"""

    SOURCE_NAME = 'bookseriesinorder'
    BASE_URL = 'https://www.bookseriesinorder.com'
    REQUESTS_PER_HOUR = 200  # Be respectful
    MIN_DELAY = 3
    MAX_DELAY = 6

    def __init__(self):
        super().__init__()
        init_db()

    def get_all_urls_from_sitemaps(self):
        """Fetch all author/series URLs from sitemaps."""
        sitemap_index_url = f'{self.BASE_URL}/sitemap_index.xml'
        print(f"Fetching sitemap index: {sitemap_index_url}")

        response = self.fetch(sitemap_index_url)
        if not response:
            return []

        # Parse sitemap index
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap_urls = [loc.text for loc in root.findall('.//sm:loc', ns)]

        # Filter to post sitemaps (where author/series pages are)
        post_sitemaps = [url for url in sitemap_urls if 'post-sitemap' in url]
        print(f"Found {len(post_sitemaps)} post sitemaps")

        all_urls = []
        for sitemap_url in post_sitemaps:
            print(f"Fetching {sitemap_url}...")
            response = self.fetch(sitemap_url)
            if not response:
                continue

            try:
                root = ET.fromstring(response.content)
                urls = [loc.text for loc in root.findall('.//sm:loc', ns)]
                all_urls.extend(urls)
                print(f"  Got {len(urls)} URLs")
            except ET.ParseError as e:
                print(f"  Error parsing {sitemap_url}: {e}")

        # Filter out non-content pages
        content_urls = [url for url in all_urls
                       if not any(skip in url for skip in ['/about', '/privacy', '/contact', '/recommendations', '/book-release'])]

        print(f"Total content URLs: {len(content_urls)}")
        return content_urls

    def parse_author_page(self, url, html):
        """Parse an author/series page and extract data."""
        soup = BeautifulSoup(html, 'html.parser')

        # Get author name from title or heading
        title = soup.find('title')
        if not title:
            return None

        title_text = title.get_text()
        # Title format: "Author Name - Book Series In Order"
        author_match = re.match(r'^(.+?)\s*[-–—]\s*Book Series', title_text)
        if not author_match:
            return None

        author_name = author_match.group(1).strip()

        # Find all series on the page
        # Series are typically in h2 or h3 tags with "Publication Order of X Books"
        series_data = []

        # Look for series headings
        headings = soup.find_all(['h2', 'h3', 'h4'])
        current_series = None

        for heading in headings:
            heading_text = heading.get_text().strip()

            # Match series heading patterns
            series_match = re.match(
                r'(?:Publication Order of|Chronological Order of)\s+(.+?)\s+(?:Books?|Series|Novels?)',
                heading_text,
                re.IGNORECASE
            )

            if series_match:
                series_name = series_match.group(1).strip()

                # Get books - look for the content after this heading
                # Books are often in paragraph tags or lists following the heading
                books = []
                sibling = heading.find_next_sibling()

                while sibling and sibling.name not in ['h2', 'h3', 'h4']:
                    # Look for book entries - usually links with years
                    text = sibling.get_text()

                    # Pattern: "Book Title (Year)"
                    book_matches = re.findall(
                        r'([^()\n]+?)\s*\((\d{4})\)',
                        text
                    )

                    for book_title, year in book_matches:
                        book_title = book_title.strip()
                        # Clean up title
                        book_title = re.sub(r'^[\d.]+\s*[-–—.]?\s*', '', book_title)  # Remove leading numbers
                        book_title = re.sub(r'^Description\s*/?\s*Buy at Amazon\s*', '', book_title)  # Remove Amazon cruft
                        book_title = re.sub(r'Description\s*/?\s*Buy at Amazon.*$', '', book_title)  # Remove trailing Amazon
                        book_title = book_title.strip()
                        if book_title and len(book_title) > 2:
                            books.append({
                                'title': book_title,
                                'year': int(year),
                                'position': len(books) + 1
                            })

                    sibling = sibling.find_next_sibling()

                if books:
                    series_data.append({
                        'name': series_name,
                        'books': books
                    })

        return {
            'author': author_name,
            'series': series_data,
            'url': url
        }

    def save_author_data(self, data):
        """Save scraped author data to database."""
        if not data:
            return

        author_name = data['author']
        url = data['url']

        # Add author
        author_id = add_author(
            name=author_name,
            source=self.SOURCE_NAME,
            source_url=url
        )

        # Add each series and its books
        for series_info in data['series']:
            series_name = series_info['name']

            series_id = add_series(
                name=series_name,
                author_id=author_id,
                total_books=len(series_info['books']),
                source=self.SOURCE_NAME,
                source_url=url
            )

            # Add books
            for book in series_info['books']:
                add_book(
                    title=book['title'],
                    author_id=author_id,
                    series_id=series_id,
                    series_position=book['position'],
                    year_published=book['year'],
                    source=self.SOURCE_NAME,
                    source_url=url
                )

        return author_id

    def scrape_all(self, resume=True):
        """Scrape all authors and series from the site."""
        # Get all URLs
        progress = self.get_progress()

        if resume and progress and progress['status'] == 'in_progress':
            print(f"Resuming from last position: {progress['last_item']}")
            # Load URLs and skip to last position
            all_urls = self.get_all_urls_from_sitemaps()
            if progress['last_item']:
                try:
                    start_idx = all_urls.index(progress['last_item']) + 1
                    all_urls = all_urls[start_idx:]
                    print(f"Skipping {start_idx} already scraped URLs")
                except ValueError:
                    pass
        else:
            all_urls = self.get_all_urls_from_sitemaps()
            self.save_progress(total_items=len(all_urls), status='in_progress')

        total = len(all_urls)
        print(f"\nStarting scrape of {total} URLs...")

        for i, url in enumerate(all_urls):
            try:
                print(f"[{i+1}/{total}] {url}")

                response = self.fetch(url)
                if not response:
                    continue

                data = self.parse_author_page(url, response.text)
                if data:
                    self.save_author_data(data)
                    series_count = len(data['series'])
                    book_count = sum(len(s['books']) for s in data['series'])
                    print(f"  → {data['author']}: {series_count} series, {book_count} books")

                # Save progress every 10 URLs
                if i % 10 == 0:
                    self.save_progress(last_page=i, last_item=url)

            except Exception as e:
                print(f"  Error: {e}")
                continue

        self.save_progress(status='completed')
        print("\nScrape completed!")

    def scrape_series(self, series_name):
        """Search for and scrape a specific series."""
        # Search URL
        search_url = f'{self.BASE_URL}/?s={series_name.replace(" ", "+")}'

        response = self.fetch(search_url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find search results
        results = soup.find_all('article') or soup.find_all('div', class_='post')

        for result in results[:5]:  # Check first 5 results
            link = result.find('a', href=True)
            if link:
                page_url = link['href']
                if not page_url.startswith('http'):
                    page_url = self.BASE_URL + page_url

                # Fetch and parse
                response = self.fetch(page_url)
                if response:
                    data = self.parse_author_page(page_url, response.text)
                    if data:
                        # Check if this page has our series
                        for series in data['series']:
                            if normalize_text(series_name) in normalize_text(series['name']):
                                self.save_author_data(data)
                                return data

        return None


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape BookSeriesInOrder.com')
    parser.add_argument('--search', type=str, help='Search for a specific series')
    parser.add_argument('--full', action='store_true', help='Full scrape of all content')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh, don\'t resume')

    args = parser.parse_args()

    scraper = BookSeriesInOrderScraper()

    if args.search:
        print(f"Searching for: {args.search}")
        result = scraper.scrape_series(args.search)
        if result:
            print(f"Found: {result['author']}")
            for series in result['series']:
                print(f"  {series['name']}: {len(series['books'])} books")
        else:
            print("Not found")
    elif args.full:
        scraper.scrape_all(resume=not args.no_resume)
    else:
        # Show stats
        from database import get_stats
        print("Current database stats:", get_stats())
        print("\nUse --full to start full scrape")
        print("Use --search 'series name' to search for specific series")


if __name__ == '__main__':
    main()
