# DriftGuard

Agent trajectory observability. Logs step-by-step agent trajectories and surfaces a real-time signal when the agent's behavior drifts from its declared intent.

---

## How it works

1. User sends a message to the agent
2. DriftGuard infers the agent's intent from that message via a NIM LLM call
3. The agent runs (LangChain + NeMo Guardrails wrapper), emitting a trajectory step at each tool call
4. Each step is embedded via NIM and scored against the inferred intent embedding
5. Per-step drift scores and trajectory-level coherence scores are computed in real time
6. Results are stored and surfaced on the React dashboard

---

## Stack

| Layer | Technology |
|---|---|
| Agent runtime | LangChain AgentExecutor |
| LLM | NIM: meta/llama-3.1-8b-instruct |
| Embeddings | NIM: nvidia/nv-embed-v2 |
| Vector search | FAISS (CuVS upgrade path at scale) |
| Trajectory storage | Local JSON (Phoenix upgrade path) |
| Backend API | FastAPI |
| Frontend | React + Recharts + Tailwind |
| Deployment | Vercel (frontend) |

---

## Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA API key (get one free at https://build.nvidia.com)

### 2. Clone and configure

```bash
git clone <repo>
cd driftguard

cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

> **Important:** The `.env.example` contains a placeholder key. You must add your own key. Never commit `.env` to version control.

### 3. Generate the demo document

```bash
cd demo
python generate_lease.py
cd ..
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the backend

```bash
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

### 6. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000
Backend API at http://localhost:8000

---

## Running the demo

1. Open http://localhost:3000
2. Click **Load demo scenario** to pre-fill the demo inputs
3. Click **Run Agent**
4. Watch the drift timeline populate as results come in
5. Run a second scenario and use **Compare Runs** to see the difference side by side

### Demo scenario explained

- **User message:** asks the agent to identify risky clauses in the lease
- **Inferred intent:** DriftGuard extracts a clean intent sentence via NIM
- **Distraction message:** mid-run, a follow-up asks about monthly payment amounts
- **Expected result:** drift spike at the distraction step, visible on the timeline

---

## Project structure

```
driftguard/
├── backend/
│   ├── agent/
│   │   └── doc_qa.py          # LangChain agent + callback handler
│   ├── detector/
│   │   └── drift.py           # Per-step and trajectory drift scoring
│   ├── intent/
│   │   └── infer.py           # NIM-based intent inference
│   ├── config.py              # Environment config
│   ├── nim_client.py          # NIM API wrapper (LLM + embeddings)
│   └── server.py              # FastAPI endpoints
├── frontend/
│   └── src/
│       ├── components/        # React UI components
│       ├── utils/api.js       # Backend API calls
│       ├── App.jsx
│       └── index.css
├── demo/
│   ├── generate_lease.py      # Synthetic lease PDF generator
│   └── lease_agreement.pdf    # Generated demo document
├── runs/                      # Stored run results (auto-created)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Deploying the frontend to Vercel

```bash
cd frontend
npm run build
npx vercel deploy dist/
```

Set `VITE_API_URL` in Vercel environment variables to point to your deployed backend URL.

Update `frontend/src/utils/api.js` to use `import.meta.env.VITE_API_URL` as the base URL for production.

---

## Design notes

See `docs/design_doc.pdf` for the full design rationale including the trajectory-level coherence framing, intent sourcing tradeoffs, and calibration considerations.
