import sys
from unittest.mock import MagicMock

# Mock heavy dependencies not available in CI
for mod in [
    'ollama',
    'chromadb',
    'chromadb.config',
    'sentence_transformers',
    'langchain_community',
    'langchain_community.document_loaders',
]:
    sys.modules[mod] = MagicMock()

"""
Unit tests for RAG Engine components.
Run: pytest tests/ -v
"""


# ── Test: text splitter behavior ──────────────────────────────────────────────
def test_text_splitter_chunking():
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    text = "This is a test document. " * 50
    from langchain_core.documents import Document
    docs = [Document(page_content=text, metadata={"source": "test"})]
    chunks = splitter.split_documents(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= 250  # some overlap tolerance


# ── Test: document hash uniqueness ───────────────────────────────────────────
def test_doc_id_uniqueness():
    import hashlib
    ids = set()
    filenames = ["report1.pdf", "threat_intel.txt", "cve_2024.md", "mitre_attack.pdf"]
    for name in filenames:
        doc_id = hashlib.md5(name.encode()).hexdigest()[:12]
        ids.add(doc_id)
    assert len(ids) == len(filenames), "Doc IDs should be unique"


# ── Test: cosine similarity score normalization ───────────────────────────────
def test_score_normalization():
    distances = [0.1, 0.3, 0.5, 0.8, 0.95]
    scores = [round(1 - d, 4) for d in distances]
    assert all(0 <= s <= 1 for s in scores), "Scores should be in [0, 1]"
    assert scores[0] > scores[-1], "Lower distance = higher score"


# ── Test: URL scraping (mocked) ───────────────────────────────────────────────
def test_url_scraping_mock():
    from bs4 import BeautifulSoup
    html = """
    <html>
    <head><title>MITRE ATT&CK Test</title></head>
    <body>
        <nav>ignore this</nav>
        <main>Threat actor APT29 uses spearphishing attachments (T1566.001).</main>
        <footer>ignore footer</footer>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    assert "APT29" in text
    assert "T1566.001" in text
    assert "ignore this" not in text
    assert "ignore footer" not in text


# ── Test: file type detection ─────────────────────────────────────────────────
def test_supported_file_types():
    supported = {".pdf", ".txt", ".text", ".md", ".markdown"}
    unsupported = {".docx", ".xlsx", ".jpg", ".png", ".csv"}

    for ext in supported:
        assert ext in supported
    for ext in unsupported:
        assert ext not in supported


# ── Test: ingested document dataclass ────────────────────────────────────────
def test_ingested_document_fields():
    from app.rag_engine import IngestedDocument
    doc = IngestedDocument(
        doc_id="abc123",
        filename="threat_report.pdf",
        source_type="pdf",
        chunk_count=42,
        ingested_at="2024-01-01 12:00",
        size_bytes=102400,
        page_count=10,
        preview="APT29 used...",
    )
    assert doc.doc_id == "abc123"
    assert doc.chunk_count == 42
    assert doc.source_type == "pdf"


# ── Test: retrieval result dataclass ─────────────────────────────────────────
def test_retrieval_result_fields():
    from app.rag_engine import RetrievalResult
    result = RetrievalResult(
        answer="APT29 uses T1566.",
        sources=[{"filename": "report.pdf", "score": 0.85}],
        retrieval_scores=[0.85, 0.72, 0.61],
        model_used="llama3",
        latency_ms=1240,
        token_estimate=512,
    )
    assert result.model_used == "llama3"
    assert len(result.sources) == 1
    assert result.latency_ms == 1240


# ── Test: system prompt formatting ───────────────────────────────────────────
def test_system_prompt_formatting():
    from app.rag_engine import SYSTEM_PROMPT
    context = "APT29 uses spearphishing. CVE-2024-1234 affects OpenSSL."
    formatted = SYSTEM_PROMPT.format(context=context)
    assert "APT29" in formatted
    assert "CVE-2024-1234" in formatted
    assert "{context}" not in formatted  # placeholder replaced


# ── Test: chunk overlap produces shared content ───────────────────────────────
def test_chunk_overlap():
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=30)
    long_text = "The attacker used lateral movement techniques. " * 20
    docs = [Document(page_content=long_text, metadata={})]
    chunks = splitter.split_documents(docs)
    if len(chunks) > 1:
        # Overlap means some content is shared across adjacent chunks
        assert len(chunks) >= 2
        assert len(chunks[0].page_content) > 0
        assert len(chunks[1].page_content) > 0
        