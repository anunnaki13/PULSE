"""Phase-6 Pedoman Konkin source chunks for grounded AI retrieval."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pedoman_ai import PEDOMAN_CHUNKS, embedding_literal, source_hash


async def seed_pedoman_chunks(db: AsyncSession) -> int:
    ensured = 0
    for chunk in PEDOMAN_CHUNKS:
        content = chunk.text
        await db.execute(
            text(
                """
                INSERT INTO pedoman_chunks
                    (source_id, title, section, page, content, source_hash, embedding)
                VALUES
                    (:source_id, :title, :section, :page, :content, :source_hash, (:embedding)::vector)
                ON CONFLICT (source_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    section = EXCLUDED.section,
                    page = EXCLUDED.page,
                    content = EXCLUDED.content,
                    source_hash = EXCLUDED.source_hash,
                    embedding = EXCLUDED.embedding,
                    updated_at = now()
                """
            ),
            {
                "source_id": chunk.source_id,
                "title": chunk.title,
                "section": chunk.section,
                "page": chunk.page,
                "content": content,
                "source_hash": source_hash(content),
                "embedding": embedding_literal(f"{chunk.title} {chunk.section} {content}"),
            },
        )
        ensured += 1
    print(f"[seed] pedoman_chunks: ensured {ensured} source chunks")
    return ensured
