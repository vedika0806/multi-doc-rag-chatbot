"""
RAG Engine — Core document ingestion, chunking, embedding & retrieval pipeline.
Supports: PDF, TXT, Markdown, Web URLs
Embeddings: sentence-transformers (local, no API key needed)
Vector store: ChromaDB (persistent)
LLM: Ollama (llama3 / mistral, auto-detected)
"""

import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import ollama
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CHROMA_PATH = Path("./data/chroma_db")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 5
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
PREFERRED_MODELS = ["llama3", "llama3:8b", "mistral", "phi3", "llama2"]

SYSTEM_PROMPT = """You are a specialized cybersecurity intelligence analyst assistant with deep expertise in threat detection, attack vectors, CVEs, and MITRE ATT&CK framework.

You answer questions strictly based on the provided document context. Follow these rules:
1. Only answer from the provided context — never hallucinate facts.
2. If context is insufficient, say: "The uploaded documents don't contain enough information to answer this. Try uploading more relevant documents."
3. Always cite the source document and page/section when referencing specific facts.
4. Use precise technical language appropriate for security professionals.
5. Structure complex answers with clear headings and bullet points.
6. If you identify a potential threat or vulnerability, assess its severity.

Context from retrieved documents:
{context}
"""

# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class IngestedDocument:
    doc_id: str
    filename: str
    source_type: str  # pdf | txt | md | url
    chunk_count: int
    ingested_at: str
    size_bytes: int = 0
    page_count: int = 0
    preview: str = ""


@dataclass
class RetrievalResult:
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_scores: List[float]
    model_used: str
    latency_ms: float
    token_estimate: int

# ── RAG Engine ─────────────────────────────────────────────────────────────────


class RAGEngine:
    def __init__(self):
        self._embedding_model: Optional[SentenceTransformer] = None
        self._chroma_client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[Any] = None
        self._available_model: Optional[str] = None
        self._ingested_docs: Dict[str, IngestedDocument] = {}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._initialized = False

    # ── Initialization ────────────────────────────────────────────────────────
    def initialize(self) -> Tuple[bool, str]:
        """Initialize all components. Returns (success, message)."""
        try:
            # 1. Embedding model
            logger.info("Loading embedding model...")
            self._embedding_model = SentenceTransformer(EMBEDDING_MODEL)

            # 2. ChromaDB
            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_PATH),
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._chroma_client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"},
            )

            # 3. Ollama model detection
            self._available_model = self._detect_ollama_model()
            if not self._available_model:
                return False, "❌ No Ollama model found. Run: `ollama pull llama3`"

            self._initialized = True
            count = self._collection.count()
            return True, f"✅ Ready — model: `{self._available_model}` | {count} chunks in DB"

        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False, f"❌ Initialization error: {str(e)}"

    def _detect_ollama_model(self) -> Optional[str]:
        """Auto-detect best available Ollama model."""
        try:
            models = ollama.list()
            available = [m["name"] for m in models.get("models", [])]
            logger.info(f"Available Ollama models: {available}")
            for preferred in PREFERRED_MODELS:
                for avail in available:
                    if preferred in avail.lower():
                        return avail
            return available[0] if available else None
        except Exception as e:
            logger.warning(f"Ollama detection failed: {e}")
            return None

    # ── Document Ingestion ────────────────────────────────────────────────────
    def ingest_file(self, file_path: str, filename: str) -> Tuple[bool, str, Optional[IngestedDocument]]:
        """Ingest a file (PDF/TXT/MD) into the vector store."""
        if not self._initialized:
            return False, "Engine not initialized", None

        path = Path(file_path)
        ext = path.suffix.lower()
        file_size = path.stat().st_size

        try:
            # Load documents
            if ext == ".pdf":
                loader = PyPDFLoader(str(path))
                raw_docs = loader.load()
                source_type = "pdf"
            elif ext in [".txt", ".text"]:
                loader = TextLoader(str(path), encoding="utf-8")
                raw_docs = loader.load()
                source_type = "txt"
            elif ext in [".md", ".markdown"]:
                loader = UnstructuredMarkdownLoader(str(path))
                raw_docs = loader.load()
                source_type = "md"
            else:
                return False, f"Unsupported file type: {ext}", None

            return self._process_and_store(
                raw_docs, filename, source_type, file_size
            )

        except Exception as e:
            logger.error(f"Ingestion error for {filename}: {e}")
            return False, f"Failed to ingest {filename}: {str(e)}", None

    def ingest_url(self, url: str) -> Tuple[bool, str, Optional[IngestedDocument]]:
        """Scrape a URL and ingest its text content."""
        if not self._initialized:
            return False, "Engine not initialized", None
        try:
            headers = {"User-Agent": "Mozilla/5.0 (RAG-Research-Bot/1.0)"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove nav/footer/script noise
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            title = soup.find("title")
            display_name = title.string.strip() if title else url

            doc = Document(page_content=text, metadata={"source": url, "title": display_name})
            return self._process_and_store(
                [doc], display_name[:80], "url", len(text.encode())
            )

        except Exception as e:
            return False, f"Failed to scrape URL: {str(e)}", None

    def _process_and_store(
        self,
        raw_docs: List[Document],
        filename: str,
        source_type: str,
        file_size: int,
    ) -> Tuple[bool, str, Optional[IngestedDocument]]:
        """Chunk, embed, and store documents."""
        chunks = self._splitter.split_documents(raw_docs)
        if not chunks:
            return False, "No text extracted from document", None

        doc_id = hashlib.md5(filename.encode()).hexdigest()[:12]
        texts, ids, metadatas = [], [], []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            texts.append(chunk.page_content)
            ids.append(chunk_id)
            metadatas.append({
                "filename": filename,
                "source_type": source_type,
                "doc_id": doc_id,
                "chunk_index": i,
                "page": chunk.metadata.get("page", 0),
                "source": chunk.metadata.get("source", filename),
            })

        # Embed and upsert
        embeddings = self._embedding_model.encode(texts, show_progress_bar=False).tolist()
        self._collection.upsert(
            ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas
        )

        page_count = len(set(m.get("page", 0) for m in metadatas))
        preview = chunks[0].page_content[:200].replace("\n", " ") + "..."

        doc_info = IngestedDocument(
            doc_id=doc_id,
            filename=filename,
            source_type=source_type,
            chunk_count=len(chunks),
            ingested_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            size_bytes=file_size,
            page_count=page_count,
            preview=preview,
        )
        self._ingested_docs[doc_id] = doc_info

        return True, f"✅ Ingested **{filename}** → {len(chunks)} chunks", doc_info

    # ── Query & Retrieval ─────────────────────────────────────────────────────
    def query(self, question: str, top_k: int = TOP_K) -> Optional[RetrievalResult]:
        """Full RAG pipeline: embed query → retrieve → LLM answer."""
        if not self._initialized:
            return None
        if self._collection.count() == 0:
            return RetrievalResult(
                answer="⚠️ No documents ingested yet. Please upload PDFs, text files, or paste a URL first.",
                sources=[], retrieval_scores=[], model_used=self._available_model or "none",
                latency_ms=0, token_estimate=0,
            )

        import time
        start = time.time()

        # 1. Embed query
        q_embedding = self._embedding_model.encode([question], show_progress_bar=False).tolist()

        # 2. Retrieve top-k chunks
        results = self._collection.query(
            query_embeddings=q_embedding,
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]
        scores = [round(1 - d, 4) for d in distances]  # cosine similarity

        # 3. Build context
        context_parts = []
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            source_label = f"[Source {i + 1}: {meta.get('filename', '?')}, chunk {meta.get('chunk_index', 0)}]"
            context_parts.append(f"{source_label}\n{doc}")
        context = "\n\n---\n\n".join(context_parts)

        # 4. Build sources for UI
        sources = []
        seen = set()
        for meta, score in zip(metas, scores):
            key = meta.get("filename", "?")
            if key not in seen:
                seen.add(key)
                sources.append({
                    "filename": meta.get("filename", "?"),
                    "source_type": meta.get("source_type", "?"),
                    "page": meta.get("page", "N/A"),
                    "score": score,
                    "chunk_index": meta.get("chunk_index", 0),
                })

        # 5. LLM call
        prompt = SYSTEM_PROMPT.format(context=context)
        response = ollama.chat(
            model=self._available_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0.1, "num_predict": 1024},
        )

        answer = response["message"]["content"]
        latency_ms = round((time.time() - start) * 1000)
        token_estimate = len(answer.split()) + len(context.split())

        return RetrievalResult(
            answer=answer,
            sources=sources,
            retrieval_scores=scores,
            model_used=self._available_model,
            latency_ms=latency_ms,
            token_estimate=token_estimate,
        )

    # ── Utilities ─────────────────────────────────────────────────────────────
    def get_ingested_docs(self) -> List[IngestedDocument]:
        return list(self._ingested_docs.values())

    def get_collection_stats(self) -> Dict[str, Any]:
        if not self._initialized:
            return {}
        return {
            "total_chunks": self._collection.count(),
            "total_docs": len(self._ingested_docs),
            "model": self._available_model,
            "embedding_model": EMBEDDING_MODEL,
        }

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document."""
        try:
            results = self._collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self._collection.delete(ids=results["ids"])
            if doc_id in self._ingested_docs:
                del self._ingested_docs[doc_id]
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def clear_all(self) -> bool:
        """Wipe the entire vector store."""
        try:
            self._chroma_client.delete_collection("rag_documents")
            self._collection = self._chroma_client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"},
            )
            self._ingested_docs.clear()
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False
        

    @property
    def is_ready(self) -> bool:
        return self._initialized

    @property
    def model_name(self) -> Optional[str]:
        return self._available_model

