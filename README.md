# Architectural Patterns for Agentic AI

A curated, non-exhaustive learning collection of recurring architectural patterns for agentic AI.
Each included pattern has a runnable implementation so readers can understand both the design idea
and its working behavior:

- **[Single_Agent_Pattern/](Single_Agent_Pattern/)** — 9 patterns, one agent progressing from a plain LLM call to full multi-path planning with tools.
- **[Multi_Agent_Pattern/](Multi_Agent_Pattern/)** — 12 patterns covering how multiple agents cooperate, from voting to swarms to dual-LLM security.
- **[Memory_Pattern/](Memory_Pattern/)** — 5 patterns for core, archival, recall, scratchpad, and shared agent memory.

## Interactive field guide

The architectural field guide is published at:

**https://karthikv1392.github.io/agentic-patterns/**

It presents each included pattern through its context, quality-attribute problem, reusable solution,
interaction sequence, benefits, liabilities, and a code sketch linked to the runnable examples. A
client-side recommender also ranks patterns against the quality attributes readers want to strengthen
and those they need to protect from degradation.

This project is not intended to be a comprehensive catalogue of all agentic patterns. It curates
patterns with architectural relevance and emphasizes runnable implementations, interaction sketches,
and SEI-style quality-attribute reasoning.

### Influences and related catalogues

1. Liu, Y., Lo, S. K., Lu, Q., Zhu, L., Zhao, D., Xu, X., Harrer, S., & Whittle, J. (2025).
   [Agent design pattern catalogue: A collection of architectural patterns for foundation model based agents](https://doi.org/10.1016/j.jss.2024.112278).
   *Journal of Systems and Software, 220*, 112278.
2. [Agentic Patterns](https://www.agentic-patterns.com/) — a broad reference library for discovering
   patterns across agent architecture and product practice.

The static website source lives in [`website/`](website/). Every push to `main` builds it with
Vite and deploys it through the GitHub Pages workflow in [`.github/workflows/pages.yml`](.github/workflows/pages.yml).

Each pattern lives in its own folder with a self-contained `agent.py`, so
you can read the implementation in isolation or explore it live through the UI.

## Prerequisites

- **Python 3.9+**
- **[Ollama](https://ollama.com)** running locally, with the model pulled that the demos call:
  ```bash
  ollama pull gemma4
  ```
  (Model name is configured in `Single_Agent_Pattern/shared/llm.py` and `Multi_Agent_Pattern/shared/llm.py` — change it there if you use a different local model.)

## Quickstart

Run everything through the unified launcher — it handles the virtual
environment for you:

```bash
./run.sh
```

The first run creates a shared `.venv` at the repo root and installs both
folders' dependencies (`streamlit`, `ollama`, `Pillow`). Every run after that
reuses it, so startup is instant.

You'll see a menu:

```
Which demo would you like to run?
  1) Single Agent Patterns   (port 8501)
  2) Multi Agent Patterns    (port 8502)
```

Pick one, and it opens at `http://localhost:8501` (Single) or
`http://localhost:8502` (Multi). Since the two demos use different ports,
you can run `./run.sh` twice — once per demo — to have both open side by side.

Stop a demo with `Ctrl+C` in its terminal.

### Manual setup (without run.sh)

If you'd rather manage the environment yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Single_Agent_Pattern/requirements.txt -r Multi_Agent_Pattern/requirements.txt

cd Single_Agent_Pattern && streamlit run app.py   # or Multi_Agent_Pattern
```

## Patterns catalogue

### Single-Agent Patterns

| # | Pattern | Idea |
|---|---------|------|
| 01 | Passive Goal Creator | Plain prompt → sub-task breakdown → final answer. Pure LLM, no tools. |
| 02 | Proactive Goal Creator | Enriches the goal with live context (date, time, platform) and optional image analysis before calling the LLM. |
| 03 | Prompt Optimizer | A first LLM call rewrites the user's rough prompt to be clearer before it's used. |
| 04 | RAG | Retrieves relevant chunks from a local knowledge base and injects them as grounding context. |
| 05 | One-Step Tool Agent | A single LLM call produces a plan AND selects the tool + parameters; the tool runs, then the answer is synthesised. |
| 06 | Incremental Tool Agent | Three sequential LLM calls — analysis → tool selection → exact parameters — before the tool runs. |
| 07 | Single Path Plan | Generates a linear 4-6 step plan; each step optionally calls a tool, then all steps are synthesised. |
| 08 | Multi-Path Plan | Each step has 2-3 alternative approaches; an evaluator picks the best one per step before execution. |
| 09 | Self-Reflection | The agent drafts a plan, reflects on its own tool/approach choices, then revises and executes. |

### Multi-Agent Patterns

| # | Pattern | Idea |
|---|---------|------|
| 01 | Voting-based Cooperation | N agents independently answer; an aggregator merges votes (majority, weighted, or LLM-judged). |
| 02 | Role-based Cooperation | An orchestrator divides the task and assigns pieces to specialist agents. |
| 03 | Debate-based Cooperation | Agents with distinct temperaments (Skeptic, Pragmatist, Visionary) debate before a judge decides. |
| 04 | Registry & Adapter | Agents and tools live in separate typed registries, decoupling discovery from execution. |
| 05 | Parallel / Fan-Out | A complex task is decomposed into independent sub-tasks run in parallel. |
| 06 | Hierarchical Decomposition | A coordinator recursively breaks a problem down when it's too complex to decompose in one step. |
| 07 | Swarm | Agents communicate directly with each other instead of routing everything through a coordinator. |
| 08 | Human-in-the-Loop | Actions that are hard to revoke pause for human approval before executing. |
| 09 | Generator-Critic | A Generator drafts, a Critic reviews, and the loop repeats until the draft is good enough. |
| 10 | Sub-Agent Spawning | A spawner creates fresh sub-agents on demand for tasks too large for one context window. |
| 11 | Skill Library Evolution | Agents persist reusable skills across sessions instead of starting fresh every time. |
| 12 | Dual-LLM Security | A quarantined LLM handles untrusted external data; a privileged LLM never sees it directly, mitigating prompt injection. |

## Repository structure

```
agentic-patterns/
├── run.sh                      ← unified launcher (start here)
├── website/                    ← React/Vite architectural field guide
├── .github/workflows/pages.yml ← automatic GitHub Pages deployment
├── Single_Agent_Pattern/
│   ├── app.py                  ← Streamlit UI, pattern registry
│   ├── requirements.txt
│   ├── shared/                 ← shared LLM client, tools
│   └── patterns/p01.../agent.py ... p09.../agent.py
├── Multi_Agent_Pattern/
│   ├── app.py                  ← Streamlit UI, pattern registry
│   ├── requirements.txt
│   ├── shared/                 ← shared LLM client, base agent/tool classes
│   └── patterns/p01.../ ... p12.../
└── Memory_Pattern/
    └── memgpt_demo/            ← memory pattern examples
```
