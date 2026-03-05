"""
Index knowledge base documents into Pinecone.

Usage:
    cd ~/family-ai-agent
    source venv/bin/activate
    python scripts/index_knowledge.py

This reads all .txt files from knowledge/<domain>/ folders,
splits them into chunks, embeds them with Voyage AI,
and stores them in Pinecone.

Run this whenever you add or update knowledge documents.
"""
import os
import sys

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.core.rag import index_document


KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")


def create_index_if_needed():
    """Create the Pinecone index if it does not exist yet."""
    settings = get_settings()
    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=settings.pinecone_api_key)

    existing = [idx.name for idx in pc.list_indexes()]
    if settings.pinecone_index_name in existing:
        print(f"Index '{settings.pinecone_index_name}' already exists.")
        return

    print(f"Creating index '{settings.pinecone_index_name}'...")
    pc.create_index(
        name=settings.pinecone_index_name,
        dimension=512,  # voyage-3-lite embedding dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    print("Index created. Waiting for it to be ready...")

    import time
    while not pc.describe_index(settings.pinecone_index_name).status.get("ready", False):
        time.sleep(2)
    print("Index is ready!")


def index_all_documents():
    """Walk through knowledge/ directories and index all .txt files."""
    domains = ["doctor", "psychologist", "science", "technology", "news"]
    total_files = 0

    for domain in domains:
        domain_dir = os.path.join(KNOWLEDGE_DIR, domain)
        if not os.path.isdir(domain_dir):
            print(f"Skipping {domain}/ (directory not found)")
            continue

        txt_files = [f for f in os.listdir(domain_dir) if f.endswith(".txt")]
        if not txt_files:
            print(f"Skipping {domain}/ (no .txt files)")
            continue

        print(f"\n--- Indexing {domain} ({len(txt_files)} files) ---")

        for filename in txt_files:
            filepath = os.path.join(domain_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            # Extract source from first line if it starts with SOURCE:
            source = filename.replace(".txt", "")
            for line in text.split("\n"):
                if line.startswith("SOURCE:"):
                    source = line.replace("SOURCE:", "").strip()
                    break

            doc_id = f"{domain}-{filename.replace('.txt', '')}"
            index_document(doc_id=doc_id, text=text, domain=domain, source=source)
            total_files += 1

    print(f"\n=== Done! Indexed {total_files} files across all domains. ===")


if __name__ == "__main__":
    settings = get_settings()

    if not settings.pinecone_api_key:
        print("ERROR: Set PINECONE_API_KEY in .env")
        sys.exit(1)
    if not settings.voyage_api_key:
        print("ERROR: Set VOYAGE_API_KEY in .env")
        sys.exit(1)

    print("Family AI Agent - Knowledge Base Indexer")
    print("=" * 45)

    create_index_if_needed()
    index_all_documents()
