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

ÖNCE ŞUNLARı KONTROL ET:
Aşağıdakilerden biri varsa skor MAKSIMUM 25 olur:
- 3 veya daha fazla yıl deneyim şartı
- Senior / Lead / Principal / Manager ünvanı
- Birincil stack .NET, C#, Java, PHP, Ruby, Swift, Kotlin (Python olmadan)
- Yalnızca mobil geliştirme (iOS/Android)
- Yalnızca frontend (Python/backend olmadan)

Yukarıdakiler yoksa adayın profilini, deneyim seviyesini, teknoloji tercihlerini ve kariyer hedeflerini göz önünde bulundurarak 0-100 arasında puanla.

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{"score": <sayı>, "reason": "<Türkçe: neden bu skoru verdin, tek cümle>"}}"""


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
