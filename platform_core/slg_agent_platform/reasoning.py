"""
Bedrock reasoning for the agent workflow Lambdas — boto3-direct, with a deterministic
fallback so CI / demos / unit tests run offline and green.

Why boto3 and not the LangChain `llm_factory`: the Step Functions Lambdas keep a light
layer (no LangChain). boto3 is already in the Lambda runtime. The control story is the
same — Bedrock reached over the VPC endpoint (PrivateLink), and the **deployed Bedrock
Guardrail** is applied inline on generation AND re-applied on the output in `check`.

Modes (env LLM_MODE, default "deterministic"):
  deterministic  — no model call; grounded answer assembled from retrieved sources.
                   This is the default so the suite stays offline and reproducible.
  bedrock|llm    — call Amazon Bedrock (Converse) with the ANSWER_PROMPT + sources and
                   the configured Guardrail. ANY failure (no creds, throttle, missing
                   dep) falls back to deterministic — fail safe, never fail the workflow.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

ANSWER_PROMPT = (
    "You are a resident-services assistant for a U.S. local government. Answer the resident's "
    "question using ONLY the provided sources, in plain language, and cite them. Do NOT make any "
    "eligibility, legal, or benefit determination — if one is needed, say a staff member will "
    "review. If the sources do not answer the question, say so plainly.\n\n"
    "Question: {question}\n\nSources:\n{sources}"
)


def _deterministic(question: str, sources: List[Dict[str, Any]]) -> str:
    if sources:
        s = sources[0]
        return s.get("snippet", "") or f"See {s.get('title', 'the policy')}."
    return "A staff member will follow up; no published source matched this request."


def _format_sources(sources: List[Dict[str, Any]]) -> str:
    return "\n".join(f"- {s.get('title','source')}: {s.get('snippet','')} ({s.get('url','')})"
                     for s in (sources or [])) or "(none)"


def draft_answer(question: str, sources: List[Dict[str, Any]],
                 *, mode: str = None) -> Tuple[str, bool]:
    """Return (answer_text, used_llm). Falls back to deterministic on anything but a clean call."""
    mode = (mode or os.getenv("LLM_MODE", "deterministic")).strip().lower()
    if mode not in ("bedrock", "llm"):
        return _deterministic(question, sources), False
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=os.getenv("BEDROCK_REGION", "us-east-1"))
        prompt = ANSWER_PROMPT.format(question=question or "", sources=_format_sources(sources))
        kwargs: Dict[str, Any] = dict(
            modelId=os.getenv("BEDROCK_NARRATIVE_MODEL_ID",
                              os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")),
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.0},
        )
        gid = os.getenv("BEDROCK_GUARDRAIL_ID")
        if gid:
            kwargs["guardrailConfig"] = {"guardrailIdentifier": gid,
                                         "guardrailVersion": os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")}
        resp = client.converse(**kwargs)
        text = resp["output"]["message"]["content"][0]["text"]
        return (text or _deterministic(question, sources)), True
    except Exception:  # fail safe — never break the workflow on a model/infra hiccup
        return _deterministic(question, sources), False


def guardrail_check(text: str, *, source: str = "OUTPUT") -> Dict[str, Any]:
    """Apply the DEPLOYED Bedrock Guardrail to text. {action, blocked}. Skips when not configured/offline."""
    gid = os.getenv("BEDROCK_GUARDRAIL_ID")
    if not gid or not text:
        return {"action": "SKIPPED", "blocked": False}
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=os.getenv("BEDROCK_REGION", "us-east-1"))
        resp = client.apply_guardrail(
            guardrailIdentifier=gid,
            guardrailVersion=os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT"),
            source=source,
            content=[{"text": {"text": text}}],
        )
        action = resp.get("action", "NONE")
        return {"action": action, "blocked": action == "GUARDRAIL_INTERVENED"}
    except Exception:
        return {"action": "SKIPPED", "blocked": False}
