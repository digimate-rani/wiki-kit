"""
Scrape a web page into clean markdown for wiki ingestion.

Usage:
    python scripts/wiki/scrape_web.py --url "URL" [--slug "my-slug"] [--out DIR]

Saves to <wiki>/sources/web/<slug>.md by default.

Two-pass strategy:
  Pass 1 - plain HTTP request (fast, works for most pages)
  Pass 2 - Playwright, only if the result looks like an empty JS shell
           and Playwright is installed (install.py --with-playwright)
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _kitconfig import project_root, sources_dir  # noqa: E402

try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
except ImportError as exc:  # pragma: no cover - environment problem, not logic
    sys.exit(
        f"Missing dependency: {exc.name}\n"
        "Run the installer again, or:  <venv-python> -m pip install -r requirements.txt"
    )

NOISE_PATTERNS = [
    r"^Loading\.\.\.$",
    r"^Cookie settings$",
    r"^We use cookies",
    r"^Search\.\.\.$",
    r"^⌘K$",
    r"^Was this page helpful\?$",
    r"^Log in$",
    r"^Sign in$",
    r"^Skip to (main )?content$",
    r"^Console$",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)

STRIP_TAGS = ["script", "style", "nav", "footer", "header",
              "noscript", "svg", "button", "form", "iframe", "aside"]

# Many sites mark navigation with classes instead of semantic tags.
STRIP_ATTR_RE = re.compile(
    r"(^|[-_ ])(sidebar|site-?nav|navbar|navigation|breadcrumb|menu|cookie"
    r"|banner|advert|related-pages|pagination|edit-this-page|skip-link"
    r"|headerlink|anchor-link)",
    re.IGNORECASE,
)

# Feature-flag classes on these can look like navigation. Removing one of them
# removes the page.
NEVER_STRIP_TAGS = {"html", "body", "main", "article"}

# The real content usually lives in one of these. Checked in order.
MAIN_SELECTORS = [
    "main", "article", "[role=main]", "#main-content", "#content",
    ".markdown-body", ".prose", "#main", ".content",
]

THIN_WORDS = 150


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "-")
    path = re.sub(r"[^a-zA-Z0-9\-]", "", path)
    path = re.sub(r"-+", "-", path).strip("-")
    return path[:80] if path else parsed.netloc.replace(".", "-")


def fetch_static(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WikiKitBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    # requests falls back to ISO-8859-1 when the server sends no charset, which
    # turns every non-ASCII character into mojibake. Sniff the bytes instead.
    if "charset" not in resp.headers.get("content-type", "").lower():
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def fetch_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Re-run install.py with --with-playwright"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()
    return html


def strip_noise(soup):
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    total = len(soup.get_text(strip=True)) or 1

    def carries_the_page(tag):
        """
        A real navigation block is a small fraction of the page. Anything
        holding most of the text is the content itself, wearing a misleading
        class - e.g. Wikipedia puts `vector-feature-main-menu-pinned` on <html>.
        """
        return len(tag.get_text(strip=True)) > total * 0.4

    # Decomposing a parent detaches its descendants, and a detached tag raises
    # on attribute access - so skip anything already removed.
    for tag in list(soup.find_all(attrs={"role": "navigation"})):
        if not tag.decomposed and not carries_the_page(tag):
            tag.decompose()

    for tag in list(soup.find_all(True)):
        if tag.decomposed or tag.name in NEVER_STRIP_TAGS:
            continue
        ident = " ".join(tag.get("class") or []) + " " + (tag.get("id") or "")
        if not ident.strip() or not STRIP_ATTR_RE.search(ident):
            continue
        if carries_the_page(tag):
            continue
        tag.decompose()
    return soup


def main_content(soup):
    """
    Prefer the page's main content container. Falls back to the whole document
    when nothing matches or the match is too small to be the real content.
    """
    body_text = len(soup.get_text(strip=True))
    for selector in MAIN_SELECTORS:
        try:
            node = soup.select_one(selector)
        except Exception:
            continue
        if node is None:
            continue
        node_text = len(node.get_text(strip=True))
        if node_text > 400 and node_text > body_text * 0.25:
            return node
    return soup


def html_to_markdown(html: str) -> str:
    soup = strip_noise(BeautifulSoup(html, "html.parser"))
    soup = main_content(soup)

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0          # no line-wrapping
    h.protect_links = False
    h.unicode_snob = True
    h.skip_internal_links = True

    return h.handle(str(soup))


def clean_markdown(md: str) -> str:
    cleaned = [ln for ln in md.splitlines() if not NOISE_RE.match(ln.strip())]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()


def scrape(url, slug, out_dir: Path, force_playwright=False, allow_fallback=True) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"

    print(f"Fetching: {url}")

    if force_playwright:
        print("Mode: Playwright (forced)")
        html = fetch_playwright(url)
    else:
        print("Mode: static HTTP")
        html = fetch_static(url)

    cleaned = clean_markdown(html_to_markdown(html))
    words = len(cleaned.split())

    if words < THIN_WORDS and not force_playwright and allow_fallback:
        print(f"Thin content ({words} words) - retrying with Playwright...")
        try:
            cleaned = clean_markdown(html_to_markdown(fetch_playwright(url)))
            words = len(cleaned.split())
            print(f"Playwright result: {words} words")
        except RuntimeError as exc:
            print(f"Playwright unavailable: {exc}")
            print("Keeping the static result - the page may simply be short.")

    header = f"<!-- source: {url} -->\n\n"
    out_path.write_text(header + cleaned + "\n", encoding="utf-8")

    try:
        shown = out_path.resolve().relative_to(project_root())
    except ValueError:
        shown = out_path
    print(f"\nSaved: {shown}")
    print(f"Words: {words}  |  Chars: {len(cleaned)}")
    if words < THIN_WORDS:
        print("Warning: thin output. Read the file before ingesting it.")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Scrape a web page to markdown for the wiki")
    ap.add_argument("--url", required=True, help="URL to scrape")
    ap.add_argument("--slug", default=None,
                    help="Output filename without .md (auto-derived from the URL if omitted)")
    ap.add_argument("--out", default=None,
                    help="Output directory (default: <wiki>/sources/web)")
    ap.add_argument("--playwright", action="store_true",
                    help="Force Playwright for JS-rendered pages")
    ap.add_argument("--no-fallback", action="store_true",
                    help="Do not retry with Playwright when content looks thin")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else sources_dir("web")
    out_path = scrape(
        args.url,
        args.slug or slug_from_url(args.url),
        out_dir,
        force_playwright=args.playwright,
        allow_fallback=not args.no_fallback,
    )
    print(f"\nDone. Next: ingest this file into the wiki.\n  {out_path}")


if __name__ == "__main__":
    main()
