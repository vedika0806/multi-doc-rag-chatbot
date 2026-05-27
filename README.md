# 🛡️ CyberRAG — Multi-Document Threat Intelligence Assistant

> **RAG-powered cybersecurity Q&A system** | LangChain · ChromaDB · Ollama · Streamlit · Docker

[![CI](https://github.com/YOUR_USERNAME/multi-doc-rag-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/multi-doc-rag-chatbot/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-green.svg)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-orange.svg)](https://trychroma.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **production-grade Retrieval-Augmented Generation (RAG) chatbot** specialized for cybersecurity threat intelligence. Upload PDFs, text files, or scrape URLs — then ask precise questions grounded in your documents. **No API keys. Fully local. Zero hallucination risk on sourced facts.**

---

## 🎯 What It Does

| Capability | Detail |
|---|---|
| **Multi-source ingestion** | PDF, TXT, Markdown, Web URLs |
| **Semantic search** | `all-MiniLM-L6-v2` embeddings via sentence-transformers |
| **Vector storage** | ChromaDB with cosine similarity, persistent across sessions |
| **Local LLM** | Ollama auto-detects best available model (llama3 → mistral → phi3) |
| **Source attribution** | Every answer cites exact document + chunk + cosine score |
| **Real-time scoring** | Retrieval similarity chart per query |
| **Containerized** | Docker + docker-compose with Ollama sidecar |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
│                                                         │
│  PDF/TXT/MD/URL                                         │
│       │                                                 │
│       ▼                                                 │
│  LangChain Loaders ──► RecursiveTextSplitter            │
│  (PyPDFLoader,          chunk_size=800                  │
│   TextLoader,           chunk_overlap=150               │
│   BeautifulSoup)               │                        │
│                                ▼                        │
│                   SentenceTransformer Embeddings        │
│                   (all-MiniLM-L6-v2, local)             │
│                                │                        │
│                                ▼                        │
│                   ChromaDB (cosine similarity)          │
│                   Persistent vector store               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    QUERY PIPELINE                        │
│                                                         │
│  User Query                                             │
│       │                                                 │
│       ▼                                                 │
│  Embed query (MiniLM) ──► ChromaDB top-5 retrieval      │
│                                │                        │
│                                ▼                        │
│                   Context assembly + source metadata    │
│                                │                        │
│                                ▼                        │
│                   Ollama LLM (llama3/mistral)           │
│                   System prompt: cybersec analyst       │
│                                │                        │
│                                ▼                        │
│                   Grounded answer + citations +         │
│                   similarity scores                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Local (Recommended)

```bash
# 1. Clone
git clone https://github.com/vedika0806/multi-doc-rag-chatbot.git
cd multi-doc-rag-chatbot

# 2. Install Ollama and pull a model
# Mac/Linux: https://ollama.com/download
ollama pull llama3        # ~4.7GB — best quality
# or: ollama pull mistral  # ~4.1GB — faster

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
streamlit run app/main.py
# → Open http://localhost:8501
```

### Option 2: Docker Compose (One command)

```bash
git clone https://github.com/vedika0806/multi-doc-rag-chatbot.git
cd multi-doc-rag-chatbot

# Start app + Ollama sidecar
docker-compose up --build

# In another terminal, pull a model into the container
docker exec cyberrag-ollama ollama pull llama3

# → Open http://localhost:8501
```

---

## 📖 Usage

### 1. Upload Documents
- Click **"Upload files"** in the sidebar
- Supports: `.pdf`, `.txt`, `.md`
- Or paste a **URL** to scrape (MITRE ATT&CK pages, CVE advisories, NVD entries)

### 2. Ask Questions
Example queries for cybersecurity documents:
```
"What are the primary attack vectors described?"
"List all CVEs mentioned and their CVSS scores"
"What MITRE ATT&CK techniques does this threat actor use?"
"What lateral movement techniques are referenced?"
"What defensive mitigations are recommended?"
"Summarize the threat actor's TTPs"
```

### 3. Interpret Results
- **Green scores (>0.70)**: High relevance — answer is well-grounded
- **Orange scores (0.40–0.70)**: Medium relevance — answer may be partial
- **Red scores (<0.40)**: Low relevance — consider uploading more relevant docs

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Ollama (llama3 / mistral) | Local inference, no API cost |
| **Orchestration** | LangChain 0.2 | Document loading, splitting, chain management |
| **Embeddings** | sentence-transformers / all-MiniLM-L6-v2 | Dense vector embeddings |
| **Vector DB** | ChromaDB 0.5 | Persistent cosine similarity search |
| **Loaders** | PyPDF, TextLoader, BeautifulSoup | Multi-format ingestion |
| **UI** | Streamlit | Interactive chat interface |
| **Containerization** | Docker + docker-compose | Reproducible deployment |
| **CI** | GitHub Actions | Lint + test on every push |

---

## 📁 Project Structure

```
multi-doc-rag-chatbot/
├── app/
│   ├── main.py              # Streamlit UI
│   └── rag_engine.py        # Core RAG pipeline
├── tests/
│   ├── conftest.py
│   └── test_rag_engine.py   # Unit tests
├── data/
│   ├── chroma_db/           # Persistent vector store (gitignored)
│   └── sample_docs/         # Sample cybersec documents
├── .github/
│   └── workflows/ci.yml     # GitHub Actions CI
├── .streamlit/
│   └── config.toml          # Streamlit theme
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration

Key constants in `app/rag_engine.py`:

```python
CHUNK_SIZE = 800          # tokens per chunk
CHUNK_OVERLAP = 150       # overlap between chunks
TOP_K = 5                 # retrieved chunks per query
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # local embedding model
PREFERRED_MODELS = ["llama3", "mistral", "phi3"]  # Ollama priority
```

---

## 🧪 Running Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v --tb=short

# With coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Performance

| Metric | Value |
|---|---|
| Embedding speed | ~500 chunks/sec (CPU) |
| Query latency | 2–8s (llama3, M1 Mac / modern CPU) |
| Chunk size | 800 tokens, 150 overlap |
| Retrieval | Top-5 cosine similarity |
| Max document size | ~500 pages (PDF) |

---

## 🔒 Security & Privacy

- **Fully local** — no data leaves your machine
- No API keys required
- Documents stored in local ChromaDB only
- Ollama runs inference locally

---

## 🗺 Roadmap

- [ ] Hybrid search (BM25 + dense embeddings)
- [ ] Multi-collection support (isolate documents by project)
- [ ] Streaming LLM responses
- [ ] Export chat history as PDF report
- [ ] MITRE ATT&CK structured extraction
- [ ] FastAPI backend for production decoupling

---

## 👤 Author

**Vedika Sumbli**
MS Applied Data Intelligence, San Jose State University
[LinkedIn](https://linkedin.com/in/vedikasumbli) · [GitHub](https://github.com/vedika0806)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
