#!/usr/bin/env python3
"""
Master scraper runner - runs all scrapers with proper coordination.
"""
import argparse
import time
import signal
import sys
from datetime import datetime

from database import init_db, get_stats

# Graceful shutdown flag
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    print("\n\nShutdown requested - finishing current task...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run_bookseriesinorder(resume=True):
    """Run BookSeriesInOrder scraper."""
    from scraper_bookseriesinorder import BookSeriesInOrderScraper

    print("=" * 60)
    print("STARTING: BookSeriesInOrder.com scraper")
    print("=" * 60)

    scraper = BookSeriesInOrderScraper()
    scraper.scrape_all(resume=resume)


def run_fictiondb(resume=True):
    """Run FictionDB scraper (placeholder)."""
    print("=" * 60)
    print("FictionDB scraper not yet implemented")
    print("=" * 60)


def run_openlibrary():
    """Run OpenLibrary bulk download (placeholder)."""
    print("=" * 60)
    print("OpenLibrary downloader not yet implemented")
    print("=" * 60)


def run_goodreads(resume=True):
    """Run Goodreads scraper (placeholder)."""
    print("=" * 60)
    print("Goodreads scraper not yet implemented")
    print("=" * 60)


def show_status():
    """Show current scraping status and database stats."""
    from database import get_db

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    stats = get_stats()
    for table, count in stats.items():
        print(f"  {table}: {count:,}")

    print("\n" + "=" * 60)
    print("SCRAPER PROGRESS")
    print("=" * 60)

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM scrape_progress ORDER BY source')
    rows = c.fetchall()

    if not rows:
        print("  No scraping started yet")
    else:
        for row in rows:
            row = dict(row)
            print(f"\n  {row['source']}:")
            print(f"    Status: {row['status']}")
            print(f"    Progress: {row['last_page'] or 0} / {row['total_items'] or '?'}")
            if row['started_at']:
                print(f"    Started: {row['started_at']}")
            if row['completed_at']:
                print(f"    Completed: {row['completed_at']}")

    print("\n" + "=" * 60)
    print("RATE LIMITS")
    print("=" * 60)

    c.execute('SELECT * FROM rate_limits ORDER BY source')
    rows = c.fetchall()

    if rows:
        for row in rows:
            row = dict(row)
            print(f"\n  {row['source']}:")
            print(f"    Requests this hour: {row['requests_made']} / {row['max_per_hour']}")
            if row['last_request']:
                print(f"    Last request: {row['last_request']}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Master scraper runner for book metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scrapers.py --status          # Show current status
  python run_scrapers.py --all             # Run all scrapers
  python run_scrapers.py --source bsio     # Run BookSeriesInOrder only
  python run_scrapers.py --fresh           # Start fresh (don't resume)
        """
    )

    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--all', action='store_true', help='Run all scrapers')
    parser.add_argument('--source', type=str, choices=['bsio', 'fictiondb', 'openlibrary', 'goodreads'],
                       help='Run specific scraper')
    parser.add_argument('--fresh', action='store_true', help='Start fresh, don\'t resume')

    args = parser.parse_args()

    # Initialize database
    init_db()

    if args.status or (not args.all and not args.source):
        show_status()
        return

    resume = not args.fresh

    scrapers = {
        'bsio': ('BookSeriesInOrder', run_bookseriesinorder),
        'fictiondb': ('FictionDB', run_fictiondb),
        'openlibrary': ('OpenLibrary', run_openlibrary),
        'goodreads': ('Goodreads', run_goodreads),
    }

    if args.source:
        name, func = scrapers[args.source]
        print(f"\nStarting {name} scraper...")
        func(resume=resume)
    elif args.all:
        print("\nStarting ALL scrapers in sequence...")
        print("Press Ctrl+C to gracefully stop after current task\n")

        for key, (name, func) in scrapers.items():
            if shutdown_requested:
                print("Shutdown requested - stopping")
                break

            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"{'='*60}\n")

            try:
                func(resume=resume)
            except Exception as e:
                print(f"Error in {name}: {e}")
                continue

            # Brief pause between scrapers
            if not shutdown_requested:
                print(f"\nCompleted {name}. Pausing before next scraper...")
                time.sleep(30)

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    show_status()


if __name__ == '__main__':
    main()
