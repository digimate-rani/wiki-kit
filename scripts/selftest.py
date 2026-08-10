"""
Self-test for the wiki-kit installation.

Runs offline by default: every check uses locally generated input, so a failure
means something is genuinely broken, not that the network is down.

Usage:
    <venv-python> scripts/wiki/selftest.py [--network]

Exit code 0 = everything works.
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((PASS, name, detail or ""))
    except Exception as exc:
        results.append((FAIL, name, f"{type(exc).__name__}: {exc}"))


def t_imports():
    import requests, bs4, html2text, pymupdf  # noqa: F401
    return f"pymupdf {pymupdf.__version__}, html2text ok"


def t_config():
    from _kitconfig import config, project_root, wiki_dir
    cfg = config()
    root = project_root()
    if not wiki_dir().is_dir():
        raise AssertionError(f"wiki folder missing at {wiki_dir()}")
    if not (wiki_dir() / "index.md").is_file():
        raise AssertionError("wiki/index.md missing")
    if not (wiki_dir() / "log.md").is_file():
        raise AssertionError("wiki/log.md missing")
    return f"root={root.name} categories={len(cfg.get('categories', []))}"


def t_html_to_markdown():
    from scrape_web import html_to_markdown, clean_markdown
    html = """
    <html><head><title>T</title><style>a{}</style></head>
    <body><nav>menu</nav>
    <h1>Heading One</h1>
    <p>Body text with a <a href="https://example.org">link</a>.</p>
    <ul><li>first</li><li>second</li></ul>
    <p>Cookie settings</p>
    <footer>footer junk</footer></body></html>
    """
    md = clean_markdown(html_to_markdown(html))
    for needed in ("# Heading One", "first", "https://example.org"):
        if needed not in md:
            raise AssertionError(f"missing {needed!r} in converted markdown")
    for banned in ("menu", "footer junk", "Cookie settings"):
        if banned in md:
            raise AssertionError(f"noise {banned!r} survived cleaning")
    return f"{len(md.split())} words from sample HTML"


def t_main_content():
    """Sidebars and breadcrumbs must not end up in the captured page."""
    from scrape_web import html_to_markdown, clean_markdown
    real = "Real article sentence that carries the actual meaning. " * 15
    html = f"""
    <html><body>
      <div class="sidebar"><a href="/a">Sidebar link</a> navigation junk</div>
      <div class="breadcrumb">Home / Docs / Page</div>
      <main><h1>The Article</h1><p>{real}</p></main>
      <div id="site-nav">More nav junk</div>
    </body></html>
    """
    md = clean_markdown(html_to_markdown(html))
    if "# The Article" not in md or "Real article sentence" not in md:
        raise AssertionError("main content was lost")
    for banned in ("Sidebar link", "Home / Docs", "More nav junk"):
        if banned in md:
            raise AssertionError(f"chrome {banned!r} leaked into the output")
    return "main content isolated, chrome dropped"


def t_noise_filter_guard():
    """
    Regression: a navigation-shaped class can sit on the element that holds the
    whole page (Wikipedia puts `vector-feature-main-menu-pinned` on <html>).
    Stripping it once emptied every page on the site.
    """
    from scrape_web import html_to_markdown, clean_markdown
    real = "Actual page content that has to survive the noise filter. " * 20

    on_root = f"""
    <html class="vector-feature-main-menu-pinned-disabled">
      <body class="skin-vector menu-enabled">
        <div class="mw-content-container"><p>{real}</p></div>
        <div class="vector-main-menu">nav junk here</div>
      </body></html>
    """
    md = clean_markdown(html_to_markdown(on_root))
    if "Actual page content" not in md:
        raise AssertionError("nav class on <html>/<body> wiped the page")
    if "nav junk here" in md:
        raise AssertionError("genuine navigation survived")

    # Same trap one level down: the content wrapper itself matches the pattern.
    on_wrapper = f'<html><body><div class="sidebar-content"><p>{real}</p></div></body></html>'
    if "Actual page content" not in clean_markdown(html_to_markdown(on_wrapper)):
        raise AssertionError("content wrapper with a nav-like class was deleted")

    return "content survives nav-shaped classes on its own container"


def t_encoding():
    """A server that sends no charset must not produce mojibake."""
    from scrape_web import html_to_markdown, clean_markdown
    raw = "<html><body><p>Ünïcode — em dash, עברית, 中文</p></body></html>"
    md = clean_markdown(html_to_markdown(raw))
    for needed in ("Ünïcode", "—", "עברית", "中文"):
        if needed not in md:
            raise AssertionError(f"lost {needed!r} in conversion")
    if "â" in md or "Ã" in md:
        raise AssertionError("mojibake in output")
    return "unicode survives the pipeline"


def t_pdf_roundtrip():
    import pymupdf as fitz
    from convert_pdf_to_md import convert

    tmp = Path(tempfile.mkdtemp(prefix="wikikit-"))
    try:
        pdf_path = tmp / "sample.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 100), "Wiki Kit Test Document", fontsize=24)
        page.insert_text((72, 150), "This is body copy used by the installer self test.",
                         fontsize=11)
        page.insert_text((72, 170), "It has to survive the conversion to markdown.",
                         fontsize=11)
        doc.save(pdf_path)
        doc.close()

        md = convert(str(pdf_path))
        if "Wiki Kit Test Document" not in md:
            raise AssertionError("title text lost in conversion")
        if "body copy" not in md:
            raise AssertionError("body text lost in conversion")
        if "# Wiki Kit Test Document" not in md:
            raise AssertionError("large text was not promoted to a heading")
        return f"{len(md.split())} words extracted, heading detected"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_hebrew_rtl():
    from convert_pdf_to_md import is_hebrew_line, looks_reversed
    if not is_hebrew_line("שלום עולם"):
        raise AssertionError("Hebrew line not detected")
    if is_hebrew_line("hello world"):
        raise AssertionError("English line flagged as Hebrew")
    correct = " ".join(["הבית", "ולכן", "בגלל", "לפני", "מהיום", "שלנו"] * 5)
    if looks_reversed(correct):
        raise AssertionError("correctly ordered Hebrew flagged as reversed")
    if not looks_reversed(correct[::-1]):
        raise AssertionError("reversed Hebrew not detected")
    return "detection + reversal heuristics behave"


def t_network():
    from scrape_web import fetch_static, html_to_markdown, clean_markdown
    md = clean_markdown(html_to_markdown(fetch_static("https://example.com")))
    if "Example Domain" not in md:
        raise AssertionError("unexpected content from example.com")
    return "fetched example.com"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", action="store_true",
                    help="Also run one live HTTP fetch")
    args = ap.parse_args()

    check("dependencies importable", t_imports)
    check("wiki structure + config", t_config)
    check("web scraper: HTML to markdown", t_html_to_markdown)
    check("web scraper: main content isolation", t_main_content)
    check("web scraper: noise filter guard", t_noise_filter_guard)
    check("web scraper: unicode handling", t_encoding)
    check("pdf converter: PDF to markdown", t_pdf_roundtrip)
    check("pdf converter: Hebrew RTL guards", t_hebrew_rtl)
    if args.network:
        check("live fetch", t_network)

    width = max(len(name) for _, name, _ in results)
    print()
    for status, name, detail in results:
        print(f"  [{status}] {name.ljust(width)}  {detail}")

    failed = [r for r in results if r[0] == FAIL]
    print()
    if failed:
        print(f"{len(failed)} of {len(results)} checks failed.")
        return 1
    print(f"All {len(results)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
