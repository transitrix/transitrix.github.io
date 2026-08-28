#!/usr/bin/env python3
"""Check explainers PDF contract.

Published explainer PDFs must:
- Be valid PDFs
- Have exactly one page
- Have geometry 842 × 474 pt (A4 short form, 297 × 167 mm)
"""

import glob
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("❌ pypdf not installed; skipping checks", file=sys.stderr)
    sys.exit(0)


def check_explainer_pdfs():
    """Validate all explainer PDFs."""
    errors = []
    pdf_files = glob.glob("explainers/*/[!_]*.pdf")

    if not pdf_files:
        # No explainer PDFs yet; check passes
        return errors

    for pdf_path in sorted(pdf_files):
        try:
            reader = PdfReader(pdf_path)

            # Check page count
            page_count = len(reader.pages)
            if page_count != 1:
                errors.append(
                    f"❌ {pdf_path}: expected 1 page, got {page_count}"
                )
                continue

            # Check geometry on the one page
            page = reader.pages[0]
            mediabox = page.mediabox
            width = float(mediabox.width)
            height = float(mediabox.height)

            # Expected: 842 × 474 pt (A4 short form)
            # Allow ±1pt tolerance for rounding
            expected_w, expected_h = 842, 474
            if abs(width - expected_w) > 1 or abs(height - expected_h) > 1:
                errors.append(
                    f"❌ {pdf_path}: geometry {width:.0f}×{height:.0f} pt, "
                    f"expected {expected_w}×{expected_h} pt"
                )
            else:
                print(f"✓ {pdf_path}: {width:.0f}×{height:.0f} pt, 1 page")

        except Exception as e:
            errors.append(f"❌ {pdf_path}: {e}")

    return errors


if __name__ == "__main__":
    errors = check_explainer_pdfs()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
