# 🧠 Multi-Agent RAG Pipeline

A production-grade **Multi-Agent Retrieval-Augmented Generation** system featuring five specialized agents orchestrated by **LangGraph**, a **FastAPI** backend, **ChromaDB** vector store, and a **React + Vite** dark glassmorphism frontend.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                 OrchestratorAgent (LangGraph)            │
│                                                         │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐ │
│  │ Retriever  │→ │  Ranker  │→ │Synthesizer │→ │ FactChecker  │ │
│  │(bi-encoder)│  │(cross-enc│  │  (Claude)  │  │  (Claude)    │ │
│  │ ChromaDB   │  │   top-3) │  │  citations │  │ confidence   │ │
│  └────────────┘  └──────────┘  └────────────┘  └──────────────┘ │
│         ▲                                              │         │
│         └──────────── re-retrieval loop ───────────────┘         │
│                    (if confidence < 0.6)                         │
└─────────────────────────────────────────────────────────┘
```

## 🤖 Agents

| Agent | Model | Role |
|-------|-------|------|
| **RetrieverAgent** | `all-MiniLM-L6-v2` | Embeds query → cosine search → top-10 chunks |
| **RankerAgent** | `ms-marco-MiniLM-L-6-v2` | Cross-encoder reranking → top-3 |
| **SynthesizerAgent** | `claude-sonnet-4-6` | Grounded answer with `[Source: file, p.N]` citations |
| **FactCheckerAgent** | `claude-sonnet-4-6` | Sentence-level entailment check, confidence 0–1 |
| **OrchestratorAgent** | LangGraph StateGraph | Routes agents, handles re-retrieval retry loop |

---

## 🚀 Quick Start

### Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 4. Run the API
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check + chunk count |
| `POST` | `/ingest` | Upload PDF / TXT / MD |
| `POST` | `/query` | Run full RAG pipeline |

### Example query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?"}'
```

---

## 📁 Project Structure

```
multiagent-rag/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py   # LangGraph StateGraph
│   │   ├── retriever.py      # Bi-encoder + ChromaDB
│   │   ├── ranker.py         # Cross-encoder reranker
│   │   ├── synthesizer.py    # Claude synthesis + citations
│   │   └── fact_checker.py   # Claude fact verification
│   ├── api/
│   │   ├── main.py           # FastAPI app
│   │   └── routes.py         # /ingest /query /health
│   ├── ingestion/
│   │   └── loader.py         # PDF + text chunking
│   ├── vector_store/
│   │   └── chroma_store.py   # ChromaDB wrapper
│   ├── config.py             # Pydantic settings
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/       # UploadPanel, ChatWindow, etc.
        ├── hooks/            # useChat, useUpload
        └── api/              # Axios client
```

---

## ⚙️ Configuration

All settings in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Claude API key |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB storage path |
| `TOP_K` | `10` | Chunks retrieved |
| `TOP_N` | `3` | Chunks after reranking |
| `CONFIDENCE_THRESHOLD` | `0.6` | FactChecker re-retrieval trigger |
| `MAX_RETRIES` | `2` | Max re-retrieval attempts |

---

## 🛠️ Tech Stack

- **LLM**: Claude Sonnet 4.6 (Anthropic)
- **Orchestration**: LangGraph
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Vector DB**: ChromaDB (local, persistent)
- **API**: FastAPI + Uvicorn
- **Frontend**: React + Vite + dark glassmorphism CSS
