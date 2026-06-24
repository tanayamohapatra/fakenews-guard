# ruff: noqa
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
# ── TOOL: Prompt Injection Detector ───────────────────────────────────────────
def check_security(article_text: str) -> dict:
    """
    Scans article text for prompt injection attempts.
    Returns a dict with 'safe' (bool) and 'reason' (str).
    """
    injection_keywords = [
        "ignore instructions",
        "ignore previous instructions",
        "disregard",
        "jailbreak",
        "system prompt",
        "override instructions",
        "forget your instructions",
    ]
    lowered = article_text.lower()
    for keyword in injection_keywords:
        if keyword in lowered:
            return {
                "safe": False,
                "reason": f"Prompt injection detected: '{keyword}'"
            }
    return {"safe": True, "reason": "Input passed security check."}


# ── TOOL: Claim Extractor ──────────────────────────────────────────────────────
def extract_claims(article_text: str) -> str:
    """
    Extracts 3-5 specific verifiable factual claims from the article.
    Args:
        article_text: The news article text to analyze.
    Returns:
        A numbered list of factual claims as a string.
    """
    return f"Extract 3 to 5 specific, verifiable factual claims from this article. Return them as a numbered list. Article: {article_text}"


# ── TOOL: Verdict Formatter ────────────────────────────────────────────────────
def format_verdict(verdict: str, confidence: int, reasoning: str) -> dict:
    """
    Formats the final verdict output.
    Args:
        verdict: REAL, FAKE, or INSUFFICIENT_EVIDENCE
        confidence: Score from 0-100
        reasoning: Explanation of the verdict
    Returns:
        Formatted verdict dictionary
    """
    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "requires_human_review": confidence < 60
    }


# ── AGENT: Security Gate ───────────────────────────────────────────────────────
security_agent = Agent(
    name="security_gate",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a security screening agent. 
    Your ONLY job is to check if the input is safe to process.
    Use the check_security tool on the article text.
    If safe=False, respond with: BLOCKED: [reason]. Stop immediately.
    If safe=True, respond with: SAFE: Proceeding to analysis.""",
    tools=[check_security],
)

# ── AGENT: Claim Extractor ─────────────────────────────────────────────────────
claim_extractor_agent = Agent(
    name="claim_extractor",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a claim extraction specialist.
    Extract exactly 3-5 specific, verifiable factual claims from the article.
    Focus on: statistics, dates, names, events, quotes, locations.
    Avoid opinions or vague statements.
    Return a clean numbered list of claims.""",
    tools=[extract_claims],
)

# ── AGENT: Evidence Retriever ──────────────────────────────────────────────────
evidence_retriever_agent = Agent(
    name="evidence_retriever",
    model=Gemini(
        model="gemini-flash-latest",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an evidence researcher.
    Given a list of factual claims, search for evidence supporting or contradicting each one.
    For each claim, provide:
    - What evidence was found
    - Whether it SUPPORTS or CONTRADICTS the claim
    - Source URL if available
    Be concise and factual.""",
)

# ── AGENT: Verdict Agent ───────────────────────────────────────────────────────
verdict_agent = Agent(
    name="verdict_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a fact-checking verdict agent.
    Given claims and evidence, determine:
    - verdict: REAL, FAKE, or INSUFFICIENT_EVIDENCE
    - confidence: 0-100 score
    - reasoning: clear explanation

    Rules:
    - FAKE only if 2+ claims are clearly contradicted by evidence
    - INSUFFICIENT_EVIDENCE if search returned limited results
    - confidence < 60 means human review is recommended
    
    Use format_verdict tool to structure your final output.""",
    tools=[format_verdict],
)

# ── ROOT AGENT: Orchestrator ───────────────────────────────────────────────────
root_agent = Agent(
    name="fakenews_guard_orchestrator",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
instruction="""You are the FakeNewsGuard orchestrator.
When given a news article, you MUST call ALL of these agents 
in sequence, one after another. Do not stop early.

MANDATORY SEQUENCE - complete all 4 steps:
Step 1: Call security_gate. If it returns BLOCKED stop immediately.
        If it returns SAFE, continue to Step 2.
Step 2: Call claim_extractor with the original article text.
        Wait for the list of claims before continuing.
Step 3: Call evidence_retriever with the claims from Step 2.
        Wait for evidence before continuing.
Step 4: Call verdict_agent with both the claims and evidence.
        Present the final REAL/FAKE/INSUFFICIENT_EVIDENCE verdict.

You must complete all 4 steps. Never return intermediate 
results as the final answer.""",
    sub_agents=[
        security_agent,
        claim_extractor_agent,
        evidence_retriever_agent,
        verdict_agent,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)