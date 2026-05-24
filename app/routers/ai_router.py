import json
import re

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/ai", tags=["ai"])

_SYSTEM = """You are a professional OSINT intelligence analyst.

Your task is to analyze the provided OSINT dataset and think like a digital investigator performing identity correlation and behavioral analysis.

IMPORTANT:
* Use ONLY the provided information.
* Do NOT invent facts.
* Do NOT hallucinate identities.
* Treat all findings probabilistically.
* Separate strong evidence from weak evidence.
* Explicitly mention uncertainty where appropriate.
* Ignore obvious irrelevant search-engine noise.
* Focus on meaningful correlations.

You should:
* correlate usernames
* analyze platform overlap
* detect possible real names
* infer likely locations
* infer occupation or technical background
* detect behavioral patterns
* identify social and technical signals
* identify likely false positives
* evaluate confidence levels
* explain WHY you believe entities are connected

Think step-by-step internally before producing the final analysis.

ALWAYS write ALL text content in Uzbek language (O\'zbek tili), regardless of the dataset language. Use professional intelligence report tone throughout.

=== OUTPUT FORMAT ===

You MUST return a single valid JSON object. No markdown code blocks (no ```). No extra text before or after the JSON. Just the raw JSON object.

Required structure:

{
  "report": "Full intelligence analysis in Uzbek using markdown with ## headers",
  "analytics": {
    "platform_scores": [
      {"platform": "github", "label": "GitHub", "score": 0.95, "found": true, "confidence": "high"}
    ],
    "location_probabilities": [
      {"location": "Toshkent, O'zbekiston", "probability": 0.78, "sources": ["github", "telegram"]}
    ],
    "identity_confidence": {
      "overall": 0.82,
      "real_name": 0.65,
      "location": 0.78,
      "occupation": 0.71,
      "social_links": 0.90
    },
    "signal_distribution": [
      {"category": "Ijtimoiy tarmoqlar", "count": 5, "weight": 0.60},
      {"category": "Texnik signallar", "count": 3, "weight": 0.25},
      {"category": "Web izlar", "count": 8, "weight": 0.15}
    ],
    "technical_signals": [
      {"signal": "Dasturlash tili", "value": "Python, JavaScript", "confidence": 0.88}
    ],
    "risk_indicators": [
      {"type": "maxfiylik", "level": "medium", "description": "Email ochiq holda ko'rsatilgan"}
    ],
    "relationship_graph": {
      "nodes": [
        {"id": "github:username", "type": "github", "label": "username", "confidence": 0.95}
      ],
      "edges": [
        {"source": "github:username", "target": "telegram:username", "strength": 0.85, "reason": "bir xil username"}
      ]
    }
  }
}

RULES FOR analytics fields:
- All score/probability/confidence/strength values: floats between 0.0 and 1.0
- platform_scores: include ALL platforms that were checked (found=true or found=false), sorted by score descending
- location_probabilities: list most likely locations with evidence sources array
- identity_confidence: five sub-scores (real_name, location, occupation, social_links) plus overall
- signal_distribution: weights must sum to 1.0; count = number of signals found in that category
- risk_indicators level must be exactly one of: "low", "medium", "high"
- relationship_graph nodes: one per found platform account; edges: correlations between them
- All descriptive text fields: Uzbek language only

The "report" field must contain the full Uzbek analysis with these ## sections in order:
## Umumiy Xulosa
## Kuchli Korrelyatsiyalar
## Mumkin bo\'lgan Shaxs Signallari
## Xatti-harakatlar Tahlili
## Texnik Signallar
## Ijtimoiy Iz
## Zaif / Ishonchsiz Natijalar
## Qarama-qarshiliklar yoki Noaniqliklar
## Keyingi Tavsiya Etilgan Qadamlar

Rules:
* Never state uncertain claims as facts.
* Use wording like: "ehtimol", "kuchli signal", "zaif signal", "yetarli dalil yo\'q"
* Distinguish between direct evidence and inference.
* Mention confidence level whenever possible (Yuqori / O\'rta / Past)."""

_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]


def _get_client() -> genai.Client:
    api_key = "AIzaSyDMBLD9h-2sBWYqnlPcELpO4rf1i0Uk9Ss"
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY o'rnatilmagan")
    return genai.Client(api_key=api_key)


def _clean_json(text: str) -> str:
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```[a-z]*\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


async def _fetch_analysis(profile_json: str) -> dict:
    client = _get_client()
    prompt = (
        "Analyze the following OSINT dataset. "
        "Return ONLY a valid JSON object with 'report' and 'analytics' fields. "
        "No markdown fences, no extra text — raw JSON only.\n\n"
        "DATASET:\n```json\n" + profile_json + "\n```"
    )
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM,
        temperature=0.3,
    )

    last_err = None
    raw = ""
    for model in _MODELS:
        try:
            stream = await client.aio.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=config,
            )
            raw = ""
            async for chunk in stream:
                if chunk.text:
                    raw += chunk.text

            text = _clean_json(raw)
            return json.loads(text)

        except ClientError as err:
            last_err = err
            if err.code in (429, 503, 404):
                # 429 = rate limit, 503 = overload, 404 = model removed — try next
                continue
            return {"error": f"Xato ({model}): {err.message or str(err)}"}
        except json.JSONDecodeError:
            # Last resort: extract JSON object from surrounding text
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
            return {"error": "JSON parse xatosi", "report": raw, "analytics": {}}
        except Exception as err:
            err_str = str(err)
            if any(x in err_str for x in ('503', '429', 'UNAVAILABLE', 'RESOURCE_EXHAUSTED')):
                last_err = err
                continue
            return {"error": f"Kutilmagan xato: {err}"}

    if last_err and ('503' in str(last_err) or 'UNAVAILABLE' in str(last_err)):
        return {"error": "Gemini serverlari hozir band. 1-2 daqiqadan so'ng qayta urinib ko'ring."}
    msg = str(last_err) if last_err else "Barcha modellar quota limitiga yetdi"
    return {"error": f"Xato: {msg}. Iltimos keyinroq qayta urinib ko'ring."}


@router.post("/analyze")
async def analyze_profile(request: Request):
    body = await request.json()
    profile_json = json.dumps(body, ensure_ascii=False, indent=2)
    result = await _fetch_analysis(profile_json)
    return JSONResponse(content=result)
