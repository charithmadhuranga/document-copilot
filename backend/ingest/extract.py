from __future__ import annotations

from pathlib import Path

import html2text


def extract_markdown(html_path: Path) -> str:
    raw = html_path.read_text(encoding="utf-8", errors="replace")
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.ignore_tables = False
    converter.single_line_break = True
    return converter.handle(raw)
