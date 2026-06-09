from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken


@dataclass
class Chunk:
    index: int
    content: str
    section: str | None
    token_count: int


_TOKENIZER = tiktoken.get_encoding("cl100k_base")
_DEFAULT_MAX_TOKENS = 800
_DEFAULT_OVERLAP_TOKENS = 100

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def chunk_document(
    markdown: str,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    overlap_tokens: int = _DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    if not markdown.strip():
        return []

    sections = _split_by_headings(markdown)
    chunks: list[Chunk] = []
    chunk_index = 0

    for section_heading, section_content in sections:
        paragraphs = _split_paragraphs(section_content)
        current_text = ""
        current_section = section_heading

        for para in paragraphs:
            para_tokens = _count_tokens(para)

            if para_tokens > max_tokens:
                if current_text.strip():
                    chunks.append(
                        Chunk(
                            index=chunk_index,
                            content=current_text.strip(),
                            section=current_section,
                            token_count=_count_tokens(current_text),
                        )
                    )
                    chunk_index += 1
                for sub_para in _split_oversized(para, max_tokens):
                    chunks.append(
                        Chunk(
                            index=chunk_index,
                            content=sub_para,
                            section=current_section,
                            token_count=_count_tokens(sub_para),
                        )
                    )
                    chunk_index += 1
                current_text = ""
                continue

            candidate = f"{current_text}\n\n{para}".strip() if current_text else para
            candidate_tokens = _count_tokens(candidate)

            if candidate_tokens > max_tokens and current_text:
                chunks.append(
                    Chunk(
                        index=chunk_index,
                        content=current_text.strip(),
                        section=current_section,
                        token_count=_count_tokens(current_text),
                    )
                )
                chunk_index += 1
                current_text = _apply_overlap(current_text, para, overlap_tokens)
            else:
                current_text = candidate

        if current_text.strip():
            chunks.append(
                Chunk(
                    index=chunk_index,
                    content=current_text.strip(),
                    section=current_section,
                    token_count=_count_tokens(current_text),
                )
            )
            chunk_index += 1

    return chunks


def _count_tokens(text: str) -> int:
    return len(_TOKENIZER.encode(text))


def _split_by_headings(markdown: str) -> list[tuple[str | None, str]]:
    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        return [(None, markdown)]

    sections: list[tuple[str | None, str]] = []
    prev_end = 0
    prev_heading = None

    for m in matches:
        start = m.start()
        if start > prev_end:
            sections.append((prev_heading, markdown[prev_end:start].strip()))
        prev_heading = m.group(2)
        prev_end = start

    if prev_end < len(markdown):
        sections.append((prev_heading, markdown[prev_end:].strip()))

    return sections


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _split_oversized(text: str, max_tokens: int) -> list[str]:
    tokens = _TOKENIZER.encode(text)
    if len(tokens) <= max_tokens:
        return [text]

    parts: list[str] = []
    pos = 0
    while pos < len(tokens):
        end = min(pos + max_tokens, len(tokens))
        chunk = _TOKENIZER.decode(tokens[pos:end])
        if end < len(tokens):
            boundary = max(
                chunk.rfind(". "),
                chunk.rfind("! "),
                chunk.rfind("? "),
                chunk.rfind("\n"),
                chunk.rfind(" "),
            )
            if boundary > 0:
                boundary_tokens = _TOKENIZER.encode(chunk[: boundary + 1])
                candidate_end = pos + len(boundary_tokens)
                if candidate_end > pos:
                    end = candidate_end

        chunk = _TOKENIZER.decode(tokens[pos:end])
        if chunk.strip():
            parts.append(chunk.strip())
        if end == pos:
            break
        pos = end

    return parts


def _apply_overlap(current: str, next_para: str, overlap_tokens: int) -> str:
    tokens = _TOKENIZER.encode(current)
    if len(tokens) <= overlap_tokens:
        return current

    overlap_text = _TOKENIZER.decode(tokens[-overlap_tokens:])
    return f"{overlap_text}\n\n{next_para}"
