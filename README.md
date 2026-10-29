# EventWise AI — Smart Event Planning Assistant

EventWise AI is a full-stack, **local-first Generative AI application** for planning weddings, birthdays, and community events. It generates personalized event plans, deterministic integer-INR budgets, relative preparation timelines, interactive task checklists, theme concepts, and source-cited recommendations using a custom Python **Retrieval-Augmented Generation (RAG)** pipeline.

---

## 1. Key Highlights & Non-Negotiable Architecture

- **100% Local AI & Vector Pipeline**:
  - **LLM Inference**: Local **Ollama** (`llama3.2:3b` or any installed instruction-tuned model). Zero OpenAI, Gemini, Claude, or paid cloud inference APIs.
  - **Embeddings**: Local **Sentence Transformers** (`sentence-transformers/all-MiniLM-L6-v2` default).
  - **Vector Store**: Local persistent **ChromaDB** (`./backend/chroma_db`).
  - **Application Database**: Local **SQLite** via SQLAlchemy (`./backend/eventwise.db`).
  - *Note on Network Usage*: An internet connection is only needed during initial `pip` / `npm` package installation and first-time Hugging Face / Ollama model weight downloads. Normal application operation, embedding, retrieval, and inference run completely offline/locally.
- **Authoritative Deterministic Python Business Logic**:
  - **Monetary Representation**: All monetary amounts are stored, validated, and calculated consistently as **integer Indian Rupees (INR)** (`integer_rupees`).
  - **Illustrative ₹25,000 Birthday Template**: Venue ₹5,000 (20%), Food and beverages ₹8,000 (32%), Decoration ₹3,000 (12%), Cake ₹2,000 (8%), Entertainment ₹2,000 (8%), Miscellaneous ₹2,000 (8%), and Emergency reserve ₹3,000 (12%).
  - **Budget Protection**: The LLM can never silently alter a user's approved budget or tasks. Any proposed budget reduction or reallocation in chat requires explicit user approval before saving.
  - **Timeline & Date Boundary Handling**: Deadlines are calculated relative to `event_date` (e.g., 3 weeks, 2 weeks, 1 week, 3 days, 1 day before, and Event Day for birthdays), scaled for guest count (`150+` guests adds crowd-flow milestones), and safely clamped when events are scheduled near or in the past.
- **Grounded RAG & Verified Citations**:
  - Supports `.pdf` (via `pypdf`), `.txt`, `.csv`, `.json`, and structured knowledge entries.
  - Uses deterministic chunk IDs (`{doc_id}_chunk_{idx}_{hash}`) so re-indexing never creates duplicate vectors.
  - Treats retrieved documents as untrusted data, strips any hallucinated chunk IDs, falls back gracefully to general guidance when location-specific evidence is absent, and labels all sample prices as **illustrative estimates**.
- **Modern Mario-Inspired SaaS Interface**:
  - Built with Next.js App Router, strict TypeScript, Tailwind CSS, Recharts, React Hook Form, Zod, and original CSS/SVG motifs (`#8EDBFA` sky blue, `#E8483F` red, `#279B52` pipe green, `#FFC928` coin gold, `#20304A` deep navy).

---

## 2. Project Structure

```text
.
├── CLAUDE.md
├── README.md
├── .gitignore
├── .env.example
├── frontend/
│   ├── CLAUDE.md
│   ├── package.json
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # / (Home & Dashboard)
│   │   ├── planner/page.tsx          # /planner (AI + RAG Event Planner)
│   │   ├── budget/page.tsx           # /budget (Authoritative INR Budget Planner & Recharts)
│   │   ├── chat/page.tsx             # /chat (Persistent RAG Chatbot with Proposal Approval)
│   │   ├── knowledge-base/page.tsx   # /knowledge-base (Upload, Search, Re-index, Delete)
│   │   └── events/[id]/
│   │       ├── page.tsx              # /events/[id] (Event Plan Details & Embedded Chat)
│   │       └── timeline/page.tsx     # /events/[id]/timeline (Quest Timeline & Checklist)
│   ├── components/
│   ├── lib/
│   └── types/
└── backend/
    ├── CLAUDE.md
    ├── requirements.txt
    ├── .env.example
    ├── pytest.ini
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── routes/
    │   ├── schemas/
    │   ├── services/
    │   ├── rag/
    │   │   ├── CLAUDE.md
    │   │   ├── ingestion.py
    │   │   ├── extraction.py
    │   │   ├── chunking.py
    │   │   ├── embeddings.py
    │   │   ├── retrieval.py
    │   │   ├── generation.py
    │   │   └── prompts.py
    │   ├── database/
    │   └── prompts/
    ├── data/
    │   ├── documents/
    │   └── sample_data/              # 9 curated sample guides (.txt, .json, .csv)
    └── tests/
        ├── CLAUDE.md
        ├── conftest.py
        ├── test_budget.py
        ├── test_timeline.py
        ├── test_ingestion.py
        ├── test_retrieval.py
        ├── test_planner.py
        ├── test_integration_local.py
        └── evaluation/
            ├── eval_dataset.json
            └── test_rag_evaluation.py
```

---

## 3. Setup & Run Instructions

### Prerequisites
- **Python** 3.11+
- **Node.js** 18+ and `npm`
- **Ollama** installed locally ([https://ollama.com](https://ollama.com))

### Step 1: Prepare Local Ollama Model
```bash
ollama serve
ollama pull llama3.2:3b
```
*(You can configure any installed instruction-tuned model in `.env` via `OLLAMA_MODEL`, such as `llama3.2:3b` or `qwen3:8b`. If Ollama is stopped, EventWise AI automatically falls back to deterministic grounded synthesis so the application remains usable.)*

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` (and/or `backend/.env`):
```bash
cp .env.example .env
```

### Step 3: Install & Start the FastAPI Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- On first startup, the backend automatically initializes `eventwise.db` and indexes the 9 curated documents in `backend/data/sample_data/` into ChromaDB, plus seeds one clearly labeled illustrative sample event.
- OpenAPI documentation is available at `http://localhost:8000/docs`.

### Step 4: Install & Start the Next.js Frontend
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 4. Changing the Embedding Model & Rebuilding ChromaDB

EventWise AI stores the active `EMBEDDING_MODEL` name in ChromaDB collection metadata and raises an explicit `EmbeddingModelMismatchError` if you change `EMBEDDING_MODEL` without rebuilding the collection. To switch embedding models:
1. Stop the backend server.
2. Update `EMBEDDING_MODEL` in `.env`.
3. Delete `backend/chroma_db/`.
4. Restart the backend and click **Re-Index** on existing documents in `/knowledge-base` (or let startup re-seed the initial collection).

---

## 5. Testing & Evaluation

### Offline Unit & API Tests (No Ollama or Network Required)
```bash
cd backend
pytest -v -m "not integration"
```

### Live Local Integration Tests (Sentence Transformers + ChromaDB + Ollama Check)
```bash
cd backend
pytest -v -m integration
```

### Run All Backend Tests (20 / 20 Passing)
```bash
cd backend
pytest -v
```

### Frontend TypeScript & Production Build Checks
```bash
cd frontend
npm run typecheck
npm run build
```
