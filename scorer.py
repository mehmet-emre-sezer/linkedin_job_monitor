import json
import logging
import os
from config import CANDIDATE_PROFILE
from llm import ask

PROFILE_FILE = "profile.json"

logger = logging.getLogger(__name__)

# Profil bir kere yüklenir, process boyunca bellekte tutulur
def _load_profile() -> str:
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("candidate_profile", CANDIDATE_PROFILE)
    return CANDIDATE_PROFILE

_PROFILE: str = _load_profile()

SCORING_PROMPT = """Bir adayın iş ilanlarını değerlendiriyorsun.

Aday profili:
{profile}

İş ilanı:
Başlık: {title}
Şirket: {company}
Açıklama:
{description}

Bu ilanı adaya uygunluk açısından 0-100 arasında puanla.
Kurallar:
- Puan artır: junior/entry-level, remote/hybrid, Python/ML/NLP odaklı ise
- Puan düşür: 3+ yıl deneyim şartı, senior ünvan, alakasız teknoloji stack'i varsa
- 70 ve üzeri iyi eşleşme sayılır

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{"score": <sayı>, "reason": "<tek cümle Türkçe açıklama>"}}"""


def score_job(job: dict) -> dict | None:
    # Boş başlıklı ilanları atla
    if not job.get("title", "").strip():
        logger.warning("Boş başlıklı ilan atlandı.")
        return None

    prompt = SCORING_PROMPT.format(
        profile=_PROFILE,
        title=job["title"],
        company=job["company"],
        description=job["description"] or "Açıklama mevcut değil.",
    )

    try:
        raw    = ask(prompt, expect_json=True)
        result = json.loads(raw)
        return {"score": int(result["score"]), "reason": str(result["reason"])}
    except Exception as e:
        logger.error(f"Scoring failed for '{job['title']}': {e}")
        return None
