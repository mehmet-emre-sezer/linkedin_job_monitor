"""
LinkedIn arama sorgularını CV profiline göre LLM ile otomatik oluşturur.
Çalıştırma: python query_generator.py

Üretilen sorgular queries.json dosyasına kaydedilir.
main.py bu dosya varsa oradan okur, yoksa config.py'deki SEARCH_QUERIES'e döner.
"""

import json
import logging
from config import CANDIDATE_PROFILE, SEARCH_QUERIES
from llm import ask

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

QUERIES_FILE = "queries.json"

GENERATOR_PROMPT = """Sen bir iş arama uzmanısın. Aşağıdaki aday profiline göre LinkedIn'de kullanılacak arama sorguları üreteceksin.

Aday Profili:
{profile}

Örnek sorgu formatı (LinkedIn boolean syntax):
{example_query}

Kurallar:
- Her sorgu LinkedIn keyword alanına direkt yapıştırılabilir olmalı
- AND, OR, NOT ve tırnak içi exact match kullanabilirsin
- Her sorgu farklı bir açıdan arama yapmalı (farklı rol kombinasyonları)
- Adayın güçlü olduğu alanlara odaklan: ML, NLP, LLM, Data Science, Backend (Python)
- Tüm sorgular junior/entry-level pozisyonları hedeflemeli
- 5 adet sorgu üret

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{
  "queries": [
    "sorgu 1",
    "sorgu 2",
    "sorgu 3",
    "sorgu 4",
    "sorgu 5"
  ]
}}"""


def generate_queries() -> list[str]:
    example_query = SEARCH_QUERIES[0] if SEARCH_QUERIES else ""

    prompt = GENERATOR_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        example_query=example_query,
    )

    logger.info("LLM'den sorgular üretiliyor...")

    try:
        raw     = ask(prompt, expect_json=True)
        result  = json.loads(raw)
        queries = result["queries"]

        logger.info(f"{len(queries)} sorgu üretildi:")
        for i, q in enumerate(queries, 1):
            logger.info(f"  {i}. {q[:100]}...")

        return queries

    except Exception as e:
        logger.error(f"Sorgu üretimi başarısız: {e}")
        return []


def save_queries(queries: list[str]):
    with open(QUERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
    logger.info(f"Sorgular {QUERIES_FILE} dosyasına kaydedildi.")


def load_queries() -> list[str]:
    """main.py tarafından çağrılır. Dosya yoksa config'e döner."""
    try:
        with open(QUERIES_FILE, "r", encoding="utf-8") as f:
            queries = json.load(f)
        logger.info(f"{QUERIES_FILE} dosyasından {len(queries)} sorgu yüklendi.")
        return queries
    except FileNotFoundError:
        logger.info(f"{QUERIES_FILE} bulunamadı, config.py'deki sorgular kullanılıyor.")
        return SEARCH_QUERIES


if __name__ == "__main__":
    queries = generate_queries()
    if queries:
        save_queries(queries)
        print("\n✅ Sorgular başarıyla üretildi ve kaydedildi.")
        print("main.py artık bu sorguları kullanacak.")
    else:
        print("\n❌ Sorgu üretilemedi, config.py'deki sorgular kullanılmaya devam edecek.")
