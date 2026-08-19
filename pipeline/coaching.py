"""Step 6 of the pipeline: coaching layer.

Turns per-feature deltas into ranked faults and a drill recommendation
in plain-language coaching terms. This is the eval-suite-critical piece:
per the build plan, "confident nonsense is the failure mode that kills
this product" -- the prompt below is instructed to say so explicitly
when deltas are too small or too noisy to support a confident call.

Model: claude-opus-5. The build plan's unit economics assume ~$0.02 of
inference per analysis; if that gets tight in practice, this is the one
call in the pipeline to consider moving to claude-sonnet-5 for -- the
prompt and parsing below don't depend on anything opus-specific.
"""

from __future__ import annotations

import json
import re

import anthropic

from datatypes import CoachingFault, CoachingResult, FeatureDelta

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are a pickleball technique coach reviewing measured \
deviations between an amateur player's third shot drop and a reference \
corpus of 4.5-5.0 level players. You are given per-feature deltas -- not \
video -- so you must reason only from the numbers.

Rules:
- Only call out a fault if |delta_pct| is large enough to plausibly be a \
real technique difference, not measurement noise. A good rule of thumb: \
under ~8% is likely noise -- don't invent a fault to fill space.
- If nothing in the deltas is clearly meaningful, say so plainly instead \
of manufacturing a confident-sounding fault. A false "you're doing X wrong" \
destroys trust faster than an honest "nothing stands out here."
- Rank real faults by severity, worst first.
- Recommend exactly one drill that addresses the single worst fault -- \
not a generic list.
- Keep language plain and actionable, the way a coach would talk courtside, \
not clinical or robotic.

Respond with ONLY a JSON object, no prose outside it, matching this shape:
{
  "faults": [{"feature_name": str, "severity": float (0-1), "explanation": str}],
  "drill": str,
  "summary": str
}
If there are no meaningful faults, return an empty "faults" list and use \
"summary" to say the shot looks clean relative to the corpus.
"""


def _format_deltas(deltas: list[FeatureDelta]) -> str:
    lines = [
        f"- {d.feature_name}: amateur={d.amateur_value:.1f}, "
        f"corpus_mean={d.corpus_mean:.1f}, delta={d.delta:+.1f} ({d.delta_pct:+.1f}%)"
        for d in deltas
    ]
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Claude is instructed to return only JSON, but strip code fences
    defensively in case a response wraps it anyway."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in coaching response: {text!r}")
    return json.loads(match.group(0))


def generate_coaching(deltas: list[FeatureDelta], client: anthropic.Anthropic | None = None) -> CoachingResult:
    client = client or anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _format_deltas(deltas)}],
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    parsed = _extract_json(text)

    faults = [
        CoachingFault(
            feature_name=f["feature_name"],
            severity=float(f["severity"]),
            explanation=f["explanation"],
        )
        for f in parsed.get("faults", [])
    ]
    faults.sort(key=lambda f: f.severity, reverse=True)

    return CoachingResult(
        faults=faults,
        drill=parsed.get("drill", ""),
        summary=parsed.get("summary", ""),
        raw_response=text,
    )
