"""
Groq API üzerinden LLM çağrısı yapan ortak modül.
scorer.py, setup.py, query_generator.py ve query_optimizer.py buradan import eder.
"""

import json
import logging
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)


def ask(prompt: str, expect_json: bool = True) -> str:
    """
    Groq'a prompt gönderir, yanıtı string olarak döner.
    expect_json=True ise JSON parse hataları için temizlik de yapar.
    """
    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()

    if not expect_json:
        return raw

    # Markdown code fence temizle
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    # Sadece { } arasını al
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return raw
