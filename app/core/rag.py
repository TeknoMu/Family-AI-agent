"""
RAG module - Retrieval Augmented Generation using Pinecone + Voyage AI.
Stores and retrieves domain-specific knowledge chunks.
"""
import structlog
from app.config import get_settings

logger = structlog.get_logger()

# Cache the Pinecone index to avoid reconnecting on every call
_index = None


def _get_index():
    """Get or create the Pinecone index connection."""
    global _index
    if _index is not None:
        return _index

    settings = get_settings()
    if not settings.pinecone_api_key:
        logger.warning("rag_no_pinecone_key", message="PINECONE_API_KEY not set")
        return None

    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        _index = pc.Index(settings.pinecone_index_name)
        logger.info("rag_connected", index=settings.pinecone_index_name)
        return _index
    except Exception as e:
        logger.error("rag_connect_error", error=str(e))
        return None


def _embed_text(text: str) -> list[float]:
    """Embed a single text using Voyage AI."""
    settings = get_settings()
    import voyageai
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed([text], model="voyage-3-lite")
    return result.embeddings[0]


async def retrieve_knowledge(query: str, domain: str, top_k: int = 5) -> str:
    """
    Retrieve relevant knowledge chunks for a query from Pinecone.

    Args:
        query: The user's question.
        domain: The domain to filter by (doctor, psychologist, etc.)
        top_k: Number of chunks to retrieve.

    Returns:
        Formatted string of relevant knowledge chunks, or empty string if unavailable.
    """
    settings = get_settings()

    if not settings.pinecone_api_key or not settings.voyage_api_key:
        return ""

    try:
        index = _get_index()
        if index is None:
            return ""

        # Embed the query
        query_vector = _embed_text(query)

        # Search Pinecone with domain filter
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            filter={"domain": domain},
            include_metadata=True,
        )

        if not results.matches:
            logger.info("rag_no_matches", domain=domain, query=query[:80])
            return ""

        # Format the retrieved chunks
        parts = []
        for i, match in enumerate(results.matches, 1):
            meta = match.metadata
            source = meta.get("source", "unknown")
            text = meta.get("text", "")
            score = match.score
            if score > 0.3:  # Only include reasonably relevant matches
                parts.append(f"[Knowledge {i}] (source: {source}, relevance: {score:.2f})\n{text}")

        formatted = "\n\n".join(parts)
        logger.info(
            "rag_retrieved",
            domain=domain,
            num_chunks=len(parts),
            query=query[:80],
        )
        return formatted

    except Exception as e:
        logger.error("rag_retrieve_error", error=str(e), domain=domain)
        return ""


def index_document(doc_id: str, text: str, domain: str, source: str, chunk_size: int = 500):
    """
    Split a document into chunks, embed them, and store in Pinecone.
    Used by the indexing script, not at runtime.

    Args:
        doc_id: Unique identifier prefix for this document.
        text: The full document text.
        domain: Domain label (doctor, psychologist, science, technology, news).
        source: Source name (e.g. "AIFA Guidelines 2024").
        chunk_size: Approximate words per chunk.
    """
    settings = get_settings()
    index = _get_index()
    if index is None:
        print("ERROR: Cannot connect to Pinecone")
        return

    # Split text into chunks by paragraphs, then by size
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk.split()) + len(para.split()) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    print(f"  Indexing {len(chunks)} chunks from {source}...")

    # Embed and upsert in batches
    import voyageai
    client = voyageai.Client(api_key=settings.voyage_api_key)

    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        embeddings = client.embed(batch_chunks, model="voyage-3-lite").embeddings

        vectors = []
        for j, (chunk_text, embedding) in enumerate(zip(batch_chunks, embeddings)):
            vectors.append({
                "id": f"{doc_id}-{i + j}",
                "values": embedding,
                "metadata": {
                    "text": chunk_text,
                    "domain": domain,
                    "source": source,
                    "doc_id": doc_id,
                }
            })

        index.upsert(vectors=vectors)

    print(f"  Done: {len(chunks)} chunks indexed for {domain}/{source}")
