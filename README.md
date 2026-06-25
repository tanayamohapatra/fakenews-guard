# FakeNewsGuard 🛡️

> A multi-agent fake news detection system built with Google Agent Development 
> Kit (ADK) 2.0. FakeNewsGuard uses a pipeline of specialized AI agents to 
> analyze news articles, retrieve real-world evidence, and issue structured 
> verdicts — REAL, FAKE, or INSUFFICIENT_EVIDENCE.

---

## Problem Statement

Misinformation spreads faster than corrections. Traditional fake news detectors 
are binary classifiers trained on labeled datasets — they can only recognize 
patterns they've seen before and fail on breaking news or novel narratives.

FakeNewsGuard takes a different approach: instead of pattern matching, it 
**reasons** about each article using live evidence retrieved from the internet 
in real time. This means it can evaluate claims it has never seen before.

---

## Why Agents?

A single LLM prompt cannot reliably:
- Extract specific verifiable claims from noisy article text
- Search the web for each claim independently  
- Cross-reference evidence against claims
- Issue a calibrated confidence score
- Screen for adversarial inputs before processing

Each of these is a distinct cognitive task best handled by a **specialized 
agent** with focused instructions and appropriate tools. The multi-agent 
architecture makes each step transparent, testable, and improvable independently.

---

## Architecture
User Input (News Article)

│

▼

┌─────────────────────┐

│  Security Gate      │  ← Prompt injection detection (plain Python, no LLM)

│  check_security()   │    Blocks adversarial inputs before any AI processing

└─────────┬───────────┘

│ SAFE

▼

┌─────────────────────┐

│  Claim Extractor    │  ← LLM agent: extracts 3-5 verifiable factual claims

│  extract_claims()   │    Focuses on statistics, dates, names, quotes

└─────────┬───────────┘

│

▼

┌─────────────────────┐

│  Evidence Retriever │  ← LLM agent + Google Search grounding

│  [Google Search]    │    Searches the live web for each claim

└─────────┬───────────┘

│

▼

┌─────────────────────┐

│  Verdict Agent      │  ← LLM agent: synthesizes claims + evidence

│  format_verdict()   │    Outputs REAL / FAKE / INSUFFICIENT_EVIDENCE

└─────────┬───────────┘

│

▼

Final Verdict + Confidence Score + Reasoning

(Human review flagged if confidence < 60)

All agents are coordinated by a **root orchestrator** using ADK's sub-agent 
pattern, implementing Agent-to-Agent (A2A) communication.

---

## Course Concepts Demonstrated

| Concept | Implementation |
|---|---|
| **Multi-agent system (ADK)** | 4 specialized agents coordinated by an orchestrator |
| **Agent-to-Agent (A2A)** | Orchestrator delegates via `transfer_to_agent` |
| **Security features** | Prompt injection detection before any LLM processing |
| **Agent skills (agents-cli)** | Project scaffolded and managed via `google-agents-cli` |
| **Human-in-the-loop** | Low confidence verdicts flagged for human review |
| **Tool use** | `check_security`, `extract_claims`, `format_verdict`, Google Search |

---

## Project Structure
fakenews-guard/

├── app/

│   ├── agent.py          # All agent definitions, tools, and orchestrator

│   ├── init.py       # Exports app and root_agent for ADK web server

│   └── app_utils/        # Telemetry and typing utilities

├── tests/

│   ├── unit/             # Unit tests

│   ├── integration/      # Integration tests

│   └── eval/             # ADK evaluation datasets and config

├── GEMINI.md             # AI-assisted development context

├── pyproject.toml        # Project dependencies

└── README.md             # This file

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager — [install here](https://docs.astral.sh/uv/)
- Google AI Studio API key — [get one here](https://aistudio.google.com)
- `agents-cli` — installed automatically in setup

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/tanayamohapatra/fakenews-guard.git
cd fakenews-guard
```

**2. Install agents-cli and ADK skills:**
```bash
uvx google-agents-cli setup
```

**3. Install project dependencies:**
```bash
agents-cli install
```

**4. Configure your API key:**

Create a file at `app/.env` with the following content:
GOOGLE_API_KEY=your_google_ai_studio_api_key_here

> ⚠️ Never commit your API key. The `.env` file is already in `.gitignore`.

### Running the Agent

**Start the local development server:**
```bash
uv run adk web app
```

**Open the ADK playground in your browser:**
http://127.0.0.1:8000

Paste any news article into the chat to receive a structured verdict.

---

## Example Usage

**Input:**
Scientists have discovered that drinking 10 cups of coffee daily increases

lifespan by 20 years, according to a study by Harvard University published

last week. The study followed 5 million participants over 50 years.

**Expected Output:**
VERDICT: FAKE

Confidence: 85/100

Reasoning:

Claim 1: "Harvard study followed 5 million people for 50 years"

→ CONTRADICTED: No such study found in Harvard publications.
Claim 2: "Coffee increases lifespan by 20 years"

→ CONTRADICTED: No scientific evidence supports this magnitude of effect.
Human review recommended: No

---

## Security Design

FakeNewsGuard implements a **Security Gate** as the first node in the pipeline. 
This is a plain Python function (no LLM) that scans for prompt injection 
keywords before any AI agent sees the input.

Detected threats include:
- `"ignore instructions"` / `"ignore previous instructions"`
- `"jailbreak"` / `"system prompt override"`
- `"disregard"` / `"forget your instructions"`

If a threat is detected, the pipeline terminates immediately and returns a 
BLOCKED response. No LLM tokens are consumed on adversarial inputs.

---

## Track

**Agents for Good** — Misinformation is a documented threat to public health, 
democracy, and social cohesion. FakeNewsGuard addresses this by making 
fact-checking accessible, transparent, and explainable to any user.

---

## Built With

- [Google Agent Development Kit (ADK) 2.0](https://adk.dev)
- [Google Agents CLI](https://github.com/google-ai-dev/agents-cli)  
- [Gemini Flash](https://ai.google.dev)
- [Google Search Grounding](https://ai.google.dev/gemini-api/docs/grounding)
- Python 3.11+

---

> ⚠️ **Note:** This project uses the Google AI Studio free tier. 
> High-traffic periods may cause temporary 503/429 errors from Google's 
> model servers. If the agent is unresponsive, wait 60 seconds and retry.