"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-06-09
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("create extension if not exists vector")

    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chat_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_chat_threads_owner", "chat_threads", "profiles",
        ["owner_id"], ["id"], ondelete="CASCADE"
    )

    op.create_table(
        "source_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("filing_type", sa.String(10), nullable=False),
        sa.Column("filing_date", sa.String(10), nullable=False),
        sa.Column("report_date", sa.String(10), nullable=False),
        sa.Column("accession_number", sa.String(50), unique=True, nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("markdown_content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("section", sa.String(255), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_chunks_document", "document_chunks", "source_documents",
        ["document_id"], ["id"], ondelete="CASCADE"
    )
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)"
    )
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_messages_thread", "chat_messages", "chat_threads",
        ["thread_id"], ["id"], ondelete="CASCADE"
    )

    op.create_table(
        "message_citations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", UUID(as_uuid=True), nullable=False),
        sa.Column("citation_index", sa.Integer, nullable=False),
        sa.Column("excerpt", sa.Text, nullable=False),
    )
    op.create_foreign_key(
        "fk_citations_message", "message_citations", "chat_messages",
        ["message_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_citations_chunk", "message_citations", "document_chunks",
        ["chunk_id"], ["id"], ondelete="CASCADE"
    )

    op.execute(
        "CREATE INDEX ix_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200)"
    )
    op.create_index("ix_chunks_search_vector", "document_chunks", ["search_vector"], postgresql_using="gin")
    op.create_index("ix_chunks_metadata", "document_chunks", ["metadata"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("message_citations")
    op.drop_table("chat_messages")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("chat_threads")
    op.drop_table("profiles")
