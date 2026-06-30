# FakeNewsGuard 🛡️

> A multi-agent fake news detection system built with Google Agent Development 
> Kit (ADK) 2.0. FakeNewsGuard uses AI agents to analyze news articles, 
> retrieve real-world evidence via live web search, and issue structured 
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
- Screen for adversarial inputs before processing
- Extract specific verifiable claims from noisy article text
- Search the web for each claim and weigh the evidence
- Issue a calibrated, explainable verdict

Each of these is a distinct cognitive task best handled by a **specialized 
agent or tool** with focused instructions. The architecture below decomposes 
fact-checking into reliable, auditable steps.

---

## Architecture

```text

User Input (News Article)
│
▼
┌─────────────────────────┐
│  check_security()       │  ← Plain Python tool, no LLM
│  (direct tool)          │    Blocks prompt injection before any AI runs
└─────────┬───────────────┘
│ SAFE
▼
┌─────────────────────────┐
│  fact_checker agent     │  ← LLM agent + Google Search grounding
│                         │
│  1. Extract 3-5 claims  │    Combines claim extraction and evidence
│  2. Search each claim   │    retrieval in a single reasoning step
│  3. SUPPORTS/CONTRADICTS│
└─────────┬───────────────┘
│
▼
┌─────────────────────────┐
│  format_verdict()       │  ← Plain Python tool
│  (direct tool)          │    Structures the final output consistently
└─────────┬───────────────┘
│
▼
REAL / FAKE / INSUFFICIENT_EVIDENCE

Confidence Score + Reasoning
Human review flag (if confidence < 60)
```


All components are coordinated by a **root orchestrator agent** using ADK's 
sub-agent pattern for `fact_checker` and direct tool calls for 
`check_security` and `format_verdict`. This implements Agent-to-Agent (A2A) 
communication via `transfer_to_agent`.

> **Design note:** The architecture was originally a 4-agent pipeline 
> (security gate, claim extractor, evidence retriever, verdict agent), each 
> as a separate sub-agent. This was simplified to the current 2-component 
> design after testing revealed that multiple sequential handoffs reduced 
> orchestrator reliability. Combining claim extraction and evidence retrieval 
> into one `fact_checker` agent, and using direct tool calls for security and 
> verdict formatting, produced consistently complete pipeline runs.

---

## Course Concepts Demonstrated

| Concept | Implementation |
|---|---|
| **Multi-agent system (ADK)** | Orchestrator + `fact_checker` sub-agent, coordinated via ADK 2.0 |
| **Agent-to-Agent (A2A)** | Orchestrator delegates to `fact_checker` via `transfer_to_agent` |
| **Security features** | `check_security` tool detects prompt injection before any LLM call |
| **Agent skills (agents-cli)** | Project scaffolded and managed via `google-agents-cli` |
| **Human-in-the-loop** | Low confidence verdicts (`< 60`) flagged for human review |
| **Tool use** | `check_security`, `format_verdict`, Google Search grounding |

---

## Project Structure

```text

fakenews-guard/
├── app/
│   ├── agent.py          # Orchestrator, fact_checker agent, and tools
│   ├── init.py       # Exports app and root_agent for ADK web server
│   └── app_utils/        # Telemetry and typing utilities
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── eval/             # ADK evaluation datasets and config
├── GEMINI.md             # AI-assisted development context
├── pyproject.toml        # Project dependencies
└── README.md             # This file
```

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
last week. The study followed 5 million participants over 50 years and had
a 100% success rate.

**Output:**
Claim 1: Drinking 10 cups of coffee increases lifespan by 20 years
→ CONTRADICTS: Harvard T.H. Chan School research shows moderate coffee
consumption (3-5 cups) reduces premature death risk by 8-15%, not 20 years.
Claim 2: Study conducted by Harvard, published last week
→ CONTRADICTS: No such study found in Harvard publications.
Claim 3: Study followed 5 million participants over 50 years
→ CONTRADICTS: Harvard's largest cohort studies (Nurses' Health Study,
Health Professionals Follow-Up Study) track ~280,000 participants
combined, not 5 million. A 50-year, 5-million-person study is
unprecedented in nutritional epidemiology.
Claim 4: Study had a "100% success rate"
→ CONTRADICTS: A "100% success rate" is scientifically meaningless in
observational epidemiology — no legitimate peer-reviewed study would
claim this.
VERDICT: FAKE
Confidence: 92/100
Reasoning: The article fabricates statistics, misrepresents scientific
methodology, and invents a non-existent study attributed to Harvard
University.
Human review recommended: No

---

## Security Design

FakeNewsGuard implements a **Security Gate** as the first tool call in the 
pipeline — `check_security()`. This is a plain Python function (no LLM) that 
scans for prompt injection keywords before any AI agent sees the input.

Detected threats include:
- `"ignore instructions"` / `"ignore previous instructions"`
- `"jailbreak"` / `"system prompt override"`
- `"disregard"` / `"forget your instructions"`

If a threat is detected, the pipeline terminates immediately and returns a 
BLOCKED response. No LLM tokens are consumed on adversarial inputs.

This follows a key security principle: **security gates should not depend on 
AI judgment.** An LLM asked to detect a jailbreak attempt might itself be 
susceptible to that attempt. A plain Python function has no such vulnerability.

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
> model servers. If the agent is unresponsive, wait 60-120 seconds and retry.