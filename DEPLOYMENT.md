# 🚀 GitHub Deployment Guide — CyberRAG

## Step 1: Create the GitHub Repository

1. Go to https://github.com/new
2. Repository name: `multi-doc-rag-chatbot`
3. Description: `RAG-powered cybersecurity threat intelligence assistant | LangChain · ChromaDB · Ollama · Streamlit`
4. Set to **Public**
5. Do NOT initialize with README (we already have one)
6. Click **Create repository**

---

## Step 2: Push Your Code

Open a terminal in the project folder and run:

```bash
# Navigate to project
cd /path/to/multi-doc-rag-chatbot

# Initialize git
git init
git add .
git commit -m "feat: initial production RAG chatbot

- Multi-document ingestion: PDF, TXT, Markdown, Web URLs
- LangChain + ChromaDB vector store with cosine similarity
- Ollama local LLM (llama3/mistral auto-detected)
- sentence-transformers embeddings (all-MiniLM-L6-v2)
- Streamlit UI with source attribution and retrieval scoring
- Docker + docker-compose for reproducible deployment
- GitHub Actions CI pipeline
- 8 unit tests covering core pipeline components"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/multi-doc-rag-chatbot.git
git branch -M main
git push -u origin main
```

---

## Step 3: Update README with Your Info

In README.md, replace:
- `YOUR_USERNAME` → your actual GitHub username
- LinkedIn/portfolio URLs with your real links

Then:
```bash
git add README.md
git commit -m "docs: update README with correct profile links"
git push
```

---

## Step 4: Add GitHub Repository Topics

On your repo page → click the gear ⚙️ next to "About":

Add topics:
```
rag langchain chromadb ollama streamlit cybersecurity
llm python machine-learning nlp vector-database
retrieval-augmented-generation local-llm
```

---

## Step 5: Deploy on Streamlit Cloud (Free)

> **Note:** Streamlit Cloud requires an LLM. Since Ollama is local,
> for cloud deployment you have two options:

### Option A: Deploy with a demo mode (recommended for portfolio)
Add a `DEMO_MODE=true` environment variable that uses a pre-computed
set of sample Q&A pairs when no Ollama is available — shows the UI
and demo answers.

### Option B: Keep as local-only (still excellent for portfolio)
The Dockerfile + docker-compose is your deployment artifact.
Mention in README: "Run locally with Docker for full functionality."
This is honest and professional.

**For Streamlit Cloud:**
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repo
4. Main file path: `app/main.py`
5. Add secrets if needed

---

## Step 6: Add a Demo Screenshot

1. Run the app locally: `streamlit run app/main.py`
2. Upload a sample PDF (any cybersec report)
3. Ask a question and get an answer
4. Take a screenshot
5. Save as `docs/demo_screenshot.png`
6. Add to README:

```markdown
## 📸 Demo
![CyberRAG Demo](docs/demo_screenshot.png)
```

---

## Step 7: Pin the Repo on Your GitHub Profile

1. Go to your GitHub profile
2. Click "Customize your pins"
3. Pin `multi-doc-rag-chatbot`

---

## What Your Repo Will Look Like to Recruiters

✅ Production-grade code structure (not a notebook)
✅ Architecture diagram in README
✅ Docker + CI/CD pipeline
✅ Unit tests
✅ Clear setup instructions (< 5 minutes to run)
✅ Quantified performance metrics
✅ Cybersecurity domain (ties to your thesis work)
✅ Local LLM (shows you understand the full LLM stack)
✅ Source attribution (shows ML maturity — not just vibes)
