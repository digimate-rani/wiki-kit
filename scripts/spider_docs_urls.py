"""
Optional: spider a documentation site and print every URL matching a filter.

Requires Playwright. Install it with:
    python install.py --with-playwright

Usage:
    python scripts/wiki/spider_docs_urls.py <start-url> <path-filter> [--deep N]

  start-url    any page with the full nav visible (usually the docs home page)
  path-filter  substring every wanted URL contains, e.g. "docs/" or "api-reference"
  --deep N     also open the first N discovered pages and collect their links
               (use when the nav only shows the current section)

Output: one URL per line on stdout, sorted and de-duplicated. Review the list,
then feed each URL to scrape_web.py.

Shortcut worth trying first: many docs sites publish a sitemap. Try
<site>/sitemap.xml before spidering. Mintlify-based sites also return clean
markdown for any page if you append ".md" to its URL, which skips scraping too.
"""

import argparse
import sys
from urllib.parse import urljoin, urlparse


def collect(page, base, path_filter):
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
    found = set()
    for href in hrefs:
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        full = urljoin(base, href).split("#")[0]
        if path_filter in full:
            found.add(full)
    return found


def main():
    ap = argparse.ArgumentParser(description="Spider a docs site for URLs")
    ap.add_argument("start_url")
    ap.add_argument("path_filter")
    ap.add_argument("--deep", type=int, default=0,
                    help="Also visit the first N discovered pages to find more links")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright not installed. Re-run: python install.py --with-playwright")

    origin = f"{urlparse(args.start_url).scheme}://{urlparse(args.start_url).netloc}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(args.start_url, wait_until="networkidle", timeout=30000)
        urls = collect(page, origin, args.path_filter)

        for url in sorted(urls)[: args.deep]:
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                urls |= collect(page, origin, args.path_filter)
            except Exception as exc:  # a single bad page must not kill the crawl
                print(f"skip {url}: {exc}", file=sys.stderr)

        browser.close()

    if not urls:
        sys.exit("No URLs found - the page may not have loaded, or the filter is too narrow.")

    for url in sorted(urls):
        print(url)
    print(f"\nFound {len(urls)} pages", file=sys.stderr)


if __name__ == "__main__":
    main()
