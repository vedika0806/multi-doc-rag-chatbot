"""
Multi-Document RAG Chatbot — Streamlit UI
Cybersecurity Intelligence Assistant
"""

import streamlit as st
import tempfile
import os
import plotly.graph_objects as go
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.rag_engine import RAGEngine  # noqa: E402

# ── Page config (must be first) ───────────────────────────────────────────────
st.set_page_config(
    page_title="CyberRAG — Threat Intelligence Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #0a0e1a;
    --bg-secondary: #0d1220;
    --bg-card: #111827;
    --bg-card-hover: #1a2235;
    --accent-cyan: #00d4ff;
    --accent-green: #00ff88;
    --accent-red: #ff4757;
    --accent-orange: #ffa502;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #475569;
    --border: #1e293b;
    --border-accent: #00d4ff33;
}

/* Global */
.stApp { background: var(--bg-primary); font-family: 'Space Grotesk', sans-serif; }
.main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* Hide streamlit default elements */
#MainMenu, footer, .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1rem; }

/* Hero header */
.hero-header {
    background: linear-gradient(135deg, #0d1220 0%, #111827 50%, #0a1628 100%);
    border: 1px solid var(--border-accent);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-green), transparent);
}
.hero-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-cyan);
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #00ff8815;
    border: 1px solid #00ff8840;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: var(--accent-green);
    font-family: 'JetBrains Mono', monospace;
    margin-top: 0.5rem;
}
.status-dot {
    width: 6px; height: 6px;
    background: var(--accent-green);
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.metric-card {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--accent-cyan); }
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-cyan);
    line-height: 1;
}
.metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Chat messages */
.chat-message {
    padding: 1rem 1.2rem;
    border-radius: 10px;
    margin-bottom: 0.8rem;
    border-left: 3px solid transparent;
    font-size: 0.9rem;
    line-height: 1.6;
}
.chat-user {
    background: #1e3a5f22;
    border-left-color: var(--accent-cyan);
    color: var(--text-primary);
}
.chat-assistant {
    background: var(--bg-card);
    border-left-color: var(--accent-green);
    color: var(--text-primary);
}
.chat-role {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
}
.chat-user .chat-role { color: var(--accent-cyan); }
.chat-assistant .chat-role { color: var(--accent-green); }

/* Source cards */
.source-card {
    background: #0d1220;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.8rem;
}
.source-filename { color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }
.source-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 4px;
}
.score-high { background: #00ff8820; color: var(--accent-green); border: 1px solid #00ff8840; }
.score-mid { background: #ffa50220; color: var(--accent-orange); border: 1px solid #ffa50240; }
.score-low { background: #ff475720; color: var(--accent-red); border: 1px solid #ff475740; }

/* Section headers */
.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-muted);
    margin: 1.2rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}

/* Upload zone */
.upload-hint {
    background: var(--bg-card);
    border: 1px dashed var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-bottom: 1rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff15, #00ff8815) !important;
    border: 1px solid var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00d4ff30, #00ff8830) !important;
    transform: translateY(-1px) !important;
}

/* Input */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 1px var(--accent-cyan) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* Tags */
.tech-tag {
    display: inline-block;
    background: #00d4ff10;
    border: 1px solid #00d4ff30;
    color: var(--accent-cyan);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin: 2px;
}

/* Latency indicator */
.latency-info {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine()
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "init_message" not in st.session_state:
    st.session_state.init_message = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ingested_docs" not in st.session_state:
    st.session_state.ingested_docs = []
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0

engine: RAGEngine = st.session_state.rag_engine

# ── Auto-initialize on first load ─────────────────────────────────────────────
if not st.session_state.initialized:
    with st.spinner("🔧 Initializing RAG engine..."):
        ok, msg = engine.initialize()
        st.session_state.initialized = ok
        st.session_state.init_message = msg

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">⚡ System Status</div>', unsafe_allow_html=True)

    if st.session_state.initialized:
        st.markdown(f"""
        <div style="background:#00ff8810;border:1px solid #00ff8830;border-radius:8px;padding:0.7rem;margin-bottom:1rem;">
            <div style="color:#00ff88;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
            ✓ ENGINE ONLINE<br>
            <span style="color:#94a3b8;">Model: {engine.model_name or 'N/A'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#ff475710;border:1px solid #ff475730;border-radius:8px;padding:0.7rem;margin-bottom:1rem;">
            <div style="color:#ff4757;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
            ✗ ENGINE OFFLINE<br>
            <span style="color:#94a3b8;">{st.session_state.init_message}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.code("ollama pull llama3", language="bash")
        if st.button("🔄 Retry Init"):
            ok, msg = engine.initialize()
            st.session_state.initialized = ok
            st.session_state.init_message = msg
            st.rerun()

    # ── Document Upload ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📂 Ingest Documents</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        disabled=not st.session_state.initialized,
    )

    if uploaded_files:
        for uf in uploaded_files:
            already = any(d.filename == uf.name for d in st.session_state.ingested_docs)
            if not already:
                with st.spinner(f"Ingesting {uf.name}..."):
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=Path(uf.name).suffix
                    ) as tmp:
                        tmp.write(uf.read())
                        tmp_path = tmp.name
                    ok, msg, doc_info = engine.ingest_file(tmp_path, uf.name)
                    os.unlink(tmp_path)
                    if ok and doc_info:
                        st.session_state.ingested_docs.append(doc_info)
                        st.success(msg)
                    else:
                        st.error(msg)

    # ── URL Ingestion ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🌐 Ingest URL</div>', unsafe_allow_html=True)
    url_input = st.text_input(
        "Web URL",
        placeholder="https://attack.mitre.org/...",
        label_visibility="collapsed",
        disabled=not st.session_state.initialized,
    )
    if st.button("🔗 Scrape & Ingest", disabled=not url_input or not st.session_state.initialized):
        with st.spinner("Scraping URL..."):
            ok, msg, doc_info = engine.ingest_url(url_input)
            if ok and doc_info:
                st.session_state.ingested_docs.append(doc_info)
                st.success(msg)
            else:
                st.error(msg)

    # ── Ingested docs list ────────────────────────────────────────────────────
    if st.session_state.ingested_docs:
        st.markdown('<div class="section-header">📚 Knowledge Base</div>', unsafe_allow_html=True)
        for doc in st.session_state.ingested_docs:
            icon = {"pdf": "📄", "txt": "📝", "md": "📋", "url": "🌐"}.get(doc.source_type, "📄")
            with st.expander(f"{icon} {doc.filename[:30]}{'...' if len(doc.filename) > 30 else ''}"):
                st.markdown(f"""
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#94a3b8;">
                Chunks: <span style="color:#00d4ff">{doc.chunk_count}</span> &nbsp;|&nbsp;
                Type: <span style="color:#00d4ff">{doc.source_type.upper()}</span><br>
                Added: {doc.ingested_at}<br><br>
                <span style="color:#475569">{doc.preview[:120]}...</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑 Remove", key=f"del_{doc.doc_id}"):
                    engine.delete_document(doc.doc_id)
                    st.session_state.ingested_docs = [
                        d for d in st.session_state.ingested_docs if d.doc_id != doc.doc_id
                    ]
                    st.rerun()

    # ── Danger zone ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚠️ Danger Zone</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Clear DB", disabled=not st.session_state.initialized):
            engine.clear_all()
            st.session_state.ingested_docs = []
            st.success("Cleared!")
    with col2:
        if st.button("💬 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # ── Tech stack ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🛠 Stack</div>', unsafe_allow_html=True)
    for tag in ["LangChain", "ChromaDB", "Ollama", "Sentence-Transformers", "Streamlit", "FastAPI"]:
        st.markdown(f'<span class="tech-tag">{tag}</span>', unsafe_allow_html=True)

# ── MAIN PANEL ────────────────────────────────────────────────────────────────
stats = engine.get_collection_stats()

# Hero
st.markdown(f"""
<div class="hero-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
            <div class="hero-title">🛡️ CyberRAG</div>
            <div class="hero-subtitle">// Multi-Document Threat Intelligence Assistant</div>
            <div class="status-badge">
                <div class="status-dot"></div>
                {'ONLINE · ' + (engine.model_name or 'no model') if st.session_state.initialized else 'OFFLINE'}
            </div>
        </div>
        <div style="text-align:right;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#475569;">
            RAG · ChromaDB · Local LLM<br>
            No API keys required<br>
            <span style="color:#00d4ff">all-MiniLM-L6-v2</span> embeddings
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics row
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="metric-value">{stats.get('total_docs', 0)}</div>
        <div class="metric-label">Documents Loaded</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{stats.get('total_chunks', 0)}</div>
        <div class="metric-label">Vector Chunks</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{st.session_state.total_queries}</div>
        <div class="metric-label">Queries Run</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{'✓' if st.session_state.initialized else '✗'}</div>
        <div class="metric-label">Engine Status</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Layout: chat + sources ─────────────────────────────────────────────────────
chat_col, source_col = st.columns([2, 1])

with chat_col:
    st.markdown('<div class="section-header">💬 Intelligence Chat</div>', unsafe_allow_html=True)

    # Suggested queries
    if not st.session_state.chat_history and st.session_state.initialized:
        st.markdown("""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:1rem;margin-bottom:1rem;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#475569;margin-bottom:0.5rem;">
            // SUGGESTED QUERIES — upload documents first
            </div>
            <div style="font-size:0.82rem;color:#94a3b8;line-height:2;">
            🔍 &nbsp;"What are the primary attack vectors described in this document?"<br>
            🔍 &nbsp;"List all CVEs mentioned and their severity ratings"<br>
            🔍 &nbsp;"What MITRE ATT&CK techniques are referenced?"<br>
            🔍 &nbsp;"Summarize the threat actor TTPs described"<br>
            🔍 &nbsp;"What defensive mitigations are recommended?"
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                st.markdown(f"""
                <div class="chat-message chat-user">
                    <div class="chat-role">▶ Analyst Query</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message chat-assistant">
                    <div class="chat-role">◈ CyberRAG Response</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)
                if msg.get("latency_ms"):
                    st.markdown(f"""
                    <div class="latency-info">
                    ⏱ {msg['latency_ms']}ms &nbsp;·&nbsp;
                    🧩 {msg.get('token_estimate', '?')} tokens &nbsp;·&nbsp;
                    🤖 {msg.get('model', '?')}
                    </div>
                    """, unsafe_allow_html=True)

    # Query input
    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
    with st.form("query_form", clear_on_submit=True):
        query = st.text_area(
            "Query",
            placeholder="Ask anything about your ingested threat intelligence documents...",
            height=80,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "⚡ Run Query",
            disabled=not st.session_state.initialized,
            use_container_width=True,
        )

    if submitted and query.strip():
        st.session_state.chat_history.append({"role": "user", "content": query.strip()})
        with st.spinner("🔍 Retrieving & generating..."):
            result = engine.query(query.strip())
        if result:
            st.session_state.total_queries += 1
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result.answer,
                "sources": result.sources,
                "latency_ms": result.latency_ms,
                "token_estimate": result.token_estimate,
                "model": result.model_used,
                "scores": result.retrieval_scores,
            })
            st.session_state._last_result = result
        st.rerun()

with source_col:
    st.markdown('<div class="section-header">📎 Retrieved Sources</div>', unsafe_allow_html=True)

    last_result = getattr(st.session_state, "_last_result", None)

    if last_result and last_result.sources:
        for src in last_result.sources:
            score = src["score"]
            score_class = "score-high" if score > 0.7 else ("score-mid" if score > 0.4 else "score-low")
            icon = {"pdf": "📄", "txt": "📝", "md": "📋", "url": "🌐"}.get(src["source_type"], "📄")
            st.markdown(f"""
            <div class="source-card">
                <div>
                    <div class="source-filename">{icon} {src['filename'][:28]}</div>
                    <div style="font-size:0.7rem;color:#475569;margin-top:2px;">
                        chunk #{src['chunk_index']} · page {src['page']}
                    </div>
                </div>
                <div class="source-score {score_class}">{score:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        # Retrieval score chart
        if last_result.retrieval_scores:
            fig = go.Figure(go.Bar(
                x=[f"chunk {i + 1}" for i in range(len(last_result.retrieval_scores))],
                y=last_result.retrieval_scores,
                marker=dict(
                    color=last_result.retrieval_scores,
                    colorscale=[[0, "#1e293b"], [0.5, "#00d4ff44"], [1.0, "#00d4ff"]],
                    showscale=False,
                ),
                text=[f"{s:.3f}" for s in last_result.retrieval_scores],
                textposition="outside",
                textfont=dict(color="#94a3b8", size=9, family="JetBrains Mono"),
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=20, b=0),
                height=160,
                title=dict(text="Cosine Similarity Scores", font=dict(color="#475569", size=10, family="JetBrains Mono"), x=0),
                xaxis=dict(tickfont=dict(color="#475569", size=8, family="JetBrains Mono"), gridcolor="#1e293b"),
                yaxis=dict(tickfont=dict(color="#475569", size=8), gridcolor="#1e293b", range=[0, 1]),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:10px;padding:1.5rem;text-align:center;">
            <div style="font-size:1.5rem;margin-bottom:0.5rem;">🔍</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#475569;">
            Sources appear here<br>after each query
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Architecture diagram section
    st.markdown('<div class="section-header">🏗 Architecture</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#475569;line-height:2;">
    📄 PDF/TXT/URL<br>
    &nbsp;&nbsp;&nbsp;↓ LangChain loader<br>
    ✂️ Chunking (800t/150 overlap)<br>
    &nbsp;&nbsp;&nbsp;↓ RecursiveTextSplitter<br>
    🔢 Embeddings (MiniLM-L6-v2)<br>
    &nbsp;&nbsp;&nbsp;↓ sentence-transformers<br>
    💾 ChromaDB (cosine similarity)<br>
    &nbsp;&nbsp;&nbsp;↓ top-5 retrieval<br>
    🤖 Ollama LLM (local)<br>
    &nbsp;&nbsp;&nbsp;↓ context-grounded answer<br>
    💬 <span style="color:#00d4ff">Streamlit UI</span>
    </div>
    """, unsafe_allow_html=True)
    