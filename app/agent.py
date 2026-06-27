# ruff: noqa
# FakeNewsGuard - Multi-Agent Fake News Detection System
# Built with Google Agent Development Kit (ADK) 2.0

import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


# ── SECURITY TOOL ─────────────────────────────────────────────────────────────
# Plain Python function attached directly to the orchestrator.
# Runs BEFORE any sub-agent is called — no LLM needed for security screening.
# It protects the pipeline from prompt injection attacks — attempts by malicious
# users to embed instructions inside the article text to hijack agent behavior.
def check_security(article_text: str) -> dict:
    """
    Scans article text for prompt injection attempts.
    Args:
        article_text: The raw news article text submitted by the user.
    Returns:
        dict with 'safe' (bool) and 'reason' (str) keys.
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


# ── VERDICT FORMATTING TOOL ───────────────────────────────────────────────────
# Structures the final verdict into a consistent, parseable format.
# Called directly by the orchestrator after evidence is gathered.
def format_verdict(verdict: str, confidence: int, reasoning: str) -> dict:
    """
    Formats the final fact-checking verdict into a structured response.
    Args:
        verdict: REAL, FAKE, or INSUFFICIENT_EVIDENCE
        confidence: Integer 0-100
        reasoning: Explanation of the verdict
    Returns:
        Structured dict with verdict details and human review flag.
    """
    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "requires_human_review": confidence < 60
    }


# ── AGENT 1: FACT CHECKER ─────────────────────────────────────────────────────
# Combined agent that extracts claims AND retrieves evidence in one step.
# Uses Google Search grounding to search the live web for each claim.
# Combining these steps reduces orchestrator handoffs and improves reliability.
fact_checker_agent = Agent(
    name="fact_checker",
    model=Gemini(
        model="gemini-flash-latest",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a fact-checking researcher.
    Given a news article, do TWO things in sequence:

    First, extract 3-5 specific verifiable factual claims.
    Focus on statistics, dates, names, quotes, locations.

    Then, for each claim, search for evidence online.
    For each claim report:
    - The claim
    - Evidence found (SUPPORTS or CONTRADICTS)
    - Source URL if available

    Return both the claims list and evidence summary together.""",
)


# ── ROOT AGENT: ORCHESTRATOR ──────────────────────────────────────────────────
# Coordinates the pipeline using ADK's sub-agent and tool patterns.
# Uses check_security and format_verdict as direct tools.
# Delegates fact-checking to fact_checker_agent via A2A.
#
# Pipeline flow:
# User Input → check_security → fact_checker → format_verdict → Final Verdict
root_agent = Agent(
    name="fakenews_guard_orchestrator",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the FakeNewsGuard orchestrator.

STEP 1: Call check_security(article_text).
        If safe=False: output BLOCKED:[reason] and stop.
        If safe=True: go to Step 2 immediately.

STEP 2: Call fact_checker with the article text.
        It will return claims and evidence.
        After it responds: go to Step 3 immediately.
        Do NOT present the claims to the user yet.

STEP 3: Based on the evidence from Step 2, call format_verdict with:
        - verdict: REAL, FAKE, or INSUFFICIENT_EVIDENCE
        - confidence: 0-100
        - reasoning: brief summary of what the evidence showed
        Then present the structured verdict to the user.

CRITICAL: Never respond to the user until Step 3 is complete.""",
    tools=[check_security, format_verdict],
    sub_agents=[fact_checker_agent],
)


# ── APP WRAPPER ───────────────────────────────────────────────────────────────
# ADK App wrapper. Name must match directory name for web server resolution.
app = App(
    root_agent=root_agent,
    name="app",
)