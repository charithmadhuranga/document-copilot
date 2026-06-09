"""
One-off ingestion script.

Usage:
    uv run python -m ingest.run /path/to/downloads/manifest.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ingest.chunk import chunk_document
from ingest.embed import generate_embedding
from ingest.extract import extract_markdown
from ingest.persist import store_chunks, store_document


def run(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text())

    for filing in manifest["filings"]:
        local_path = manifest_path.parent / filing["local_path"]
        if not local_path.exists():
            print(f"Skipping missing file: {local_path}")
            continue

        print(f"Processing {filing['ticker']} {filing['filing_date']}...")

        markdown = extract_markdown(local_path)
        chunks = chunk_document(markdown)

        doc_id = store_document(
            ticker=filing["ticker"],
            company_name=filing["ticker"],
            filing_type=filing["form"],
            filing_date=filing["filing_date"],
            report_date=filing.get("report_date", filing["filing_date"]),
            accession_number=filing["accession_number"],
            source_url=filing["source_url"],
            markdown_content=markdown,
            metadata={"year": filing["filing_date"][:4]},
        )

        embeddings = [generate_embedding(c.content) for c in chunks]
        store_chunks(doc_id, chunks, embeddings)

        print(f"  Stored {len(chunks)} chunks ({doc_id})")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python -m ingest.run <manifest.json>")
        sys.exit(1)

    run(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
