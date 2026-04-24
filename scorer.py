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

ÖNCE DİSKALİFİYE KONTROL ET:
Aşağıdakilerden biri varsa skor MAKSIMUM 25 olur:
- 3 veya daha fazla yıl deneyim şartı (Required/Qualifications bölümünde)
- Senior / Lead / Principal / Manager ünvanı
- Birincil stack .NET, C#, Java, PHP, Ruby, Swift, Kotlin (Python olmadan)
- Yalnızca mobil geliştirme (iOS/Android)
- Yalnızca frontend (Python/backend olmadan)

DEĞERLENDİRME KURALLARI:
- "Required", "Qualifications", "Must have" bölümündeki eşleşmelere yüksek ağırlık ver
- "Nice to have", "Preferred", "Plus" bölümündeki eşleşmelere düşük ağırlık ver
- Zorunlu bölümde ciddi uyumsuzluk varsa skoru buna göre düşür
- Konum: Remote, Hybrid ve On-site hepsi kabul edilebilir

ÖRNEKLER:

Kötü eşleşme:
Başlık: Agentic AI Data Scientist
Sinyal: "At least 3+ years of work experience in Data Science" — Required bölümünde
Çıktı: {{"score": 15, "matches": [], "mismatches": ["Required: 3+ yıl deneyim şartı"], "reason": "Required bölümünde 3+ yıl deneyim şartı var, diskalifiye edildi"}}

Orta eşleşme:
Başlık: Junior AI Engineer
Sinyal: Node.js/TypeScript/Next.js birincil stack, LLM API kullanımı var, Python yok, Remote
Çıktı: {{"score": 72, "matches": ["Junior pozisyon", "Remote", "LLM API deneyimi"], "mismatches": ["Required: birincil stack Node.js/TypeScript, Python yok"], "reason": "Junior ve remote pozisyon, LLM deneyimi uyuşuyor ancak birincil stack Node.js/TypeScript"}}

İyi eşleşme:
Başlık: Jr. Data Scientist
Sinyal: Python (pandas, numpy, scikit-learn) Required, SQL, 1-2 yıl deneyim, Hybrid İstanbul
Çıktı: {{"score": 88, "matches": ["Required: Python", "Required: SQL", "1-2 yıl deneyim", "Hybrid İstanbul"], "mismatches": [], "reason": "Python ve data science odaklı, 1-2 yıl deneyim şartı uygun, hybrid İstanbul"}}

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{"score": <sayı>, "matches": ["<Required veya Nice-to-have bölümünden somut eşleşmeler>"], "mismatches": ["<Required bölümündeki uyumsuzluklar>"], "reason": "<Türkçe: neden bu skoru verdin, tek cümle>"}}"""


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
        return {
            "score":      int(result["score"]),
            "reason":     str(result["reason"]),
            "matches":    result.get("matches", []),
            "mismatches": result.get("mismatches", []),
        }
    except Exception as e:
        logger.error(f"Scoring failed for '{job['title']}': {e}")
        return None
