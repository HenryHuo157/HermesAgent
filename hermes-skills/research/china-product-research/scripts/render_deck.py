"""Render a .pptx deck to per-slide PNGs for visual QA.

Usage:
    python render_deck.py <deck.pptx> <out_dir> [dpi]

Finds soffice (LibreOffice) on PATH or at common Windows/macOS install paths,
converts PPTX -> PDF, then renders each page to <out_dir>/slide-N.png via
PyMuPDF (pdftoppm-free fallback for Windows machines without poppler).
"""
import os
import shutil
import subprocess
import sys

SOFFICE_CANDIDATES = [
    "/c/Program Files/LibreOffice/program/soffice.exe",
    "C:/Program Files/LibreOffice/program/soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_soffice():
    found = shutil.which("soffice")
    if found:
        return found
    for path in SOFFICE_CANDIDATES:
        if os.path.exists(path):
            return path
    raise SystemExit(
        "soffice not found. Install LibreOffice or add it to PATH "
        "(https://mirrors.tuna.tsinghua.edu.cn/libreoffice/libreoffice/stable/)."
    )


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    deck, out_dir = sys.argv[1], sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 110
    os.makedirs(out_dir, exist_ok=True)

    soffice = find_soffice()
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, deck],
        check=True,
        capture_output=True,
    )

    pdf = os.path.join(
        out_dir, os.path.splitext(os.path.basename(deck))[0] + ".pdf"
    )
    import pymupdf

    doc = pymupdf.open(pdf)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=dpi).save(os.path.join(out_dir, f"slide-{i + 1}.png"))
    print(f"rendered {len(doc)} slides -> {out_dir}")


if __name__ == "__main__":
    main()
