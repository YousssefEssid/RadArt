from __future__ import annotations

import json
import re
from typing import Any

from config import settings


def generate_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    key = (settings.openai_api_key or "").strip()
    if key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Reply with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt[:6000]},
                ],
                temperature=0.4,
                max_tokens=1200,
            )
            text = (resp.choices[0].message.content or "").strip()
            return _parse_json_loose(text, fallback)
        except Exception:
            pass

    gkey = (settings.gemini_api_key or "").strip()
    if gkey:
        try:
            import google.generativeai as genai

            genai.configure(api_key=gkey)
            model = genai.GenerativeModel("gemini-1.5-flash")
            r = model.generate_content(
                "Return only valid JSON.\n\n" + prompt[:6000],
                generation_config={"temperature": 0.4, "max_output_tokens": 1200},
            )
            text = (r.text or "").strip()
            return _parse_json_loose(text, fallback)
        except Exception:
            pass

    return fallback


def _parse_json_loose(text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {**fallback, **data}
    except json.JSONDecodeError:
        pass
    return fallback
