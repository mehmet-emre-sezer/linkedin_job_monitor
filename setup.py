"""
CV'den otomatik profil ve LinkedIn sorguları oluşturur.

Kullanım:
    python setup.py /path/to/cv.pdf

Çıktı:
    profile.json  — aday profili (scorer.py tarafından kullanılır)
    queries.json  — LinkedIn arama sorguları (main.py tarafından kullanılır)
"""

import json
import logging
import sys
import pdfplumber
from config import SEARCH_QUERIES
from llm import ask

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROFILE_FILE = "profile.json"
QUERIES_FILE = "queries.json"

SETUP_PROMPT = """Bir CV metni verilecek. Bu CV'yi analiz ederek iki şey üret:

1. Aday profili: CV'deki tüm önemli bilgileri (beceriler, deneyim, projeler, eğitim, tercihler) çıkar
2. LinkedIn arama sorguları: Adaya uygun 5 adet LinkedIn boolean arama sorgusu oluştur

Sorgu kuralları:
- LinkedIn keyword alanına direkt yapıştırılabilir olmalı
- AND, OR, NOT ve "tırnak içi exact match" kullanabilirsin
- Her sorgu farklı bir açıdan arama yapmalı
- Junior/entry-level pozisyonları hedeflemeli
- Adayın güçlü alanlarına odaklan

Örnek sorgu formatı:
{example_query}

CV metni:
{cv_text}

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{
  "candidate_profile": "adayın tüm önemli bilgilerini içeren detaylı metin",
  "queries": [
    "sorgu 1",
    "sorgu 2",
    "sorgu 3",
    "sorgu 4",
    "sorgu 5"
  ]
}}"""


def extract_text_from_pdf(pdf_path: str) -> str:
    logger.info(f"PDF okunuyor: {pdf_path}")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text.strip():
        raise ValueError("PDF'den metin çıkarılamadı. Taranmış görsel PDF olabilir.")

    logger.info(f"{len(text)} karakter metin çıkarıldı.")
    return text.strip()


def generate_profile_and_queries(cv_text: str) -> tuple[str, list[str]]:
    example_query = SEARCH_QUERIES[0] if SEARCH_QUERIES else ""

    prompt = SETUP_PROMPT.format(
        cv_text=cv_text,
        example_query=example_query,
    )

    logger.info("LLM profil ve sorgular oluşturuyor...")
    raw    = ask(prompt, expect_json=True)
    result = json.loads(raw)
    return result["candidate_profile"], result["queries"]


def save(profile: str, queries: list[str]):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump({"candidate_profile": profile}, f, ensure_ascii=False, indent=2)
    logger.info(f"Profil kaydedildi → {PROFILE_FILE}")

    with open(QUERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
    logger.info(f"Sorgular kaydedildi → {QUERIES_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python setup.py /path/to/cv.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        cv_text = extract_text_from_pdf(pdf_path)
        profile, queries = generate_profile_and_queries(cv_text)
        save(profile, queries)

        print("\n✅ Kurulum tamamlandı!")
        print(f"   {PROFILE_FILE} ve {QUERIES_FILE} oluşturuldu.")
        print("\nÜretilen sorgular:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q[:100]}")
        print("\nArtık 'python main.py' ile başlatabilirsin.")

    except Exception as e:
        logger.error(f"Kurulum başarısız: {e}")
        sys.exit(1)
