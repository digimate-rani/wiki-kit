"""
Convert a PDF into markdown so it can be ingested into the wiki.

Usage:
    python scripts/wiki/convert_pdf_to_md.py --pdf "path/to/file.pdf" [--slug NAME] [--out DIR]

Saves to <wiki>/sources/pdf/<slug>.md by default.

Notes:
    - Uses PyMuPDF (fitz). No system dependencies (no poppler needed).
    - Headings are detected by font size relative to the document's body size.
    - Hebrew/RTL: PDF text is stored visually and some producers emit reversed
      runs. --fix-rtl reverses Hebrew-majority lines. The script warns on stderr
      when it suspects this; always eyeball the output before trusting it.
    - Scanned/image-only PDFs produce almost no text. The script says so; OCR
      (not included) would be required.
"""

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _kitconfig import sources_dir  # noqa: E402

try:
    import pymupdf as fitz  # PyMuPDF 1.24+
except ImportError:
    try:
        import fitz  # older PyMuPDF
    except ImportError:
        fitz = None

if fitz is None:
    sys.exit(
        "Missing dependency: pymupdf\n"
        "Run the installer again, or:  <venv-python> -m pip install -r requirements.txt"
    )

HEBREW = re.compile(r"[֐-׿]")
THIN_WORDS = 150


def is_hebrew_line(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return sum(1 for c in letters if HEBREW.match(c)) / len(letters) > 0.5


def looks_reversed(text: str) -> bool:
    """
    Heuristic: in correctly-ordered Hebrew, common prefixes (ה, ו, ב, ל, מ, ש)
    start words far more often than they end them. If the ratio inverts across
    the document, the runs are stored reversed.
    """
    words = [w for w in re.findall(r"[֐-׿]+", text) if len(w) > 2]
    if len(words) < 20:
        return False
    starts = sum(1 for w in words if w[0] in "הובלמש")
    ends = sum(1 for w in words if w[-1] in "הובלמש")
    return ends > starts * 1.6


def body_size(doc) -> float:
    sizes = Counter()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        sizes[round(span["size"], 1)] += len(span["text"])
    return sizes.most_common(1)[0][0] if sizes else 10.0


def convert(pdf_path: str, fix_rtl: bool = False) -> str:
    doc = fitz.open(pdf_path)
    base = body_size(doc)
    out = []

    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if s["text"].strip()]
                if not spans:
                    continue

                text = re.sub(r"\s+", " ", "".join(s["text"] for s in spans).strip())
                size = max(s["size"] for s in spans)
                bold = any("bold" in s["font"].lower() for s in spans)

                if fix_rtl and is_hebrew_line(text):
                    text = text[::-1]

                # Heading levels from font size relative to body text
                if size >= base * 1.6:
                    out.append(f"# {text}")
                elif size >= base * 1.3:
                    out.append(f"## {text}")
                elif size >= base * 1.12 or (bold and len(text) < 80):
                    out.append(f"### {text}")
                else:
                    out.append(text)

        out.append("")  # page break

    doc.close()

    # Join wrapped body lines back into paragraphs, then collapse blank runs
    merged = []
    for ln in (line.rstrip() for line in out):
        if (
            merged
            and ln
            and merged[-1]
            and not ln.startswith("#")
            and not merged[-1].startswith("#")
            and not re.match(r"^\s*[-*•\d]", ln)
        ):
            merged[-1] += " " + ln
        else:
            merged.append(ln)

    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(merged)).strip()


def main():
    ap = argparse.ArgumentParser(description="Convert a PDF to markdown for the wiki")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--slug", default=None,
                    help="Output filename without .md (defaults to the PDF filename)")
    ap.add_argument("--out", default=None,
                    help="Output directory (default: <wiki>/sources/pdf)")
    ap.add_argument("--fix-rtl", action="store_true",
                    help="Reverse Hebrew-majority lines (only if the output reads backwards)")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        sys.exit(f"Not found: {args.pdf}")

    slug = args.slug or re.sub(r"[^a-zA-Z0-9֐-׿\-]+", "-",
                               Path(args.pdf).stem.lower()).strip("-")
    out_dir = Path(args.out) if args.out else sources_dir("pdf")

    md = convert(args.pdf, fix_rtl=args.fix_rtl)

    if not args.fix_rtl and looks_reversed(md):
        print("WARNING: the Hebrew in this PDF looks stored in reverse order.\n"
              "         Run the same command again with --fix-rtl, then compare\n"
              "         the two files by eye and keep the one that reads correctly.",
              file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{slug}.md"
    header = f"<!-- source: {Path(args.pdf).name} -->\n\n"
    dest.write_text(header + md + "\n", encoding="utf-8")

    words = len(md.split())
    print(f"Saved: {dest}")
    print(f"Words: {words}  |  Chars: {len(md)}")
    if words == 0:
        print("No text layer at all - this PDF is images only (a scan). "
              "Nothing can be extracted without OCR, which this kit does not do.")
    elif words < THIN_WORDS:
        print(f"Short output ({words} words). That is fine for a short document, "
              "but open the file and confirm nothing was missed before ingesting it.")
    print("\nDone. Next: ingest this file into the wiki.")


if __name__ == "__main__":
    main()
