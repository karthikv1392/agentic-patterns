# MemGPT / Letta Memory System Demo

A hands-on tour of all memory types in Letta (formerly MemGPT),
organized as standalone scripts — easiest first.

## Memory Architecture (MemGPT)

```
┌─────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW                        │
│                                                          │
│  ┌──────────┐  ┌───────┐  ┌───────┐  ┌───────────┐    │  ← CORE MEMORY
│  │  persona │  │ human │  │ tasks │  │ scratchpad│    │    (always visible)
│  └──────────┘  └───────┘  └───────┘  └───────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │          Recent Messages (message buffer)        │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │  agent tool calls
             ┌─────────────┼──────────────┐
             ▼                            ▼
┌────────────────────┐      ┌──────────────────────────┐
│  Archival Storage  │      │     Recall Storage        │
│  (vector DB / RAG) │      │  (full conversation DB)   │
│  • unlimited facts │      │  • every message ever     │
│  • semantic search │      │  • searched on demand     │
│  • persists always │      │  • auto-populated         │
└────────────────────┘      └──────────────────────────┘
```

| Memory Type | In Context? | Searched By | Use For |
|-------------|-------------|-------------|---------|
| `human` block | Always | — | User profile, preferences |
| `persona` block | Always | — | Agent role/identity |
| `tasks` block | Always | — | Goals, to-dos, progress |
| `scratchpad` block | Always | — | Working notes, reasoning |
| Archival | No | `archival_memory_search` | Long-term facts, RAG |
| Recall | No | `conversation_search` | Past conversations |

---

## Quickstart

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — pick Cloud or Local (see below)
```

**Option A — Letta Cloud (recommended for getting started):**
1. Sign up at https://app.letta.com
2. Copy your API key into `.env`:
   ```
   LETTA_API_KEY=your-key-here
   ```

**Option B — Local server (free, no account needed):**
```bash
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="sk-..." \
  letta/letta:latest
```
Then set in `.env`:
```
LETTA_BASE_URL=http://localhost:8283
```

### 3. Run the demos

```bash
# Start simple — core memory basics
python 01_core_memory.py

# Archival memory / RAG
python 02_archival_memory.py

# Recall memory (conversation history)
python 03_recall_memory.py

# Scratchpad (working memory)
python 04_scratchpad.py

# Multi-agent shared memory
python 05_shared_memory_agents.py

# Everything together
python 06_full_demo.py
```

---

## File Guide

| File | Concept |
|------|---------|
| `config.py` | Letta client setup (cloud/local) |
| `01_core_memory.py` | Core memory blocks — human, persona, custom |
| `02_archival_memory.py` | Archival memory — long-term storage + semantic search |
| `03_recall_memory.py` | Recall memory — conversation history search |
| `04_scratchpad.py` | Scratchpad block — agent working notes |
| `05_shared_memory_agents.py` | Shared blocks — two agents, one memory |
| `06_full_demo.py` | Full system — all memory types in one agent |

---

## What you'll see

Each script prints:
- Memory block contents (before/after)
- Tool calls the agent makes (`core_memory_replace`, `archival_memory_search`, etc.)
- Agent responses

The agent autonomously decides when to update memory — you don't call
memory tools manually (unless you want to inject external data).
