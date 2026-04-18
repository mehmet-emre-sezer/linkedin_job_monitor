"""
Geçmiş run verilerine bakarak LLM ile sorguları otomatik optimize eder.

Her run sonunda main.py tarafından çağrılır.
OPTIMIZE_EVERY_N_RUNS run tamamlanınca devreye girer.
"""

import json
import logging
import os
from datetime import datetime
from config import SEARCH_QUERIES
from llm import ask

logger = logging.getLogger(__name__)

RUN_HISTORY_FILE = "run_history.json"
QUERIES_FILE     = "queries.json"
OPTIMIZE_EVERY_N_RUNS = 10  # kaç run'da bir optimize edilsin

OPTIMIZER_PROMPT = """Sen bir iş arama sorgu optimizasyon uzmanısın.

Aşağıda LinkedIn iş arama sisteminin geçmiş performans verileri var.
Her sorgu için: kaç ilan bulundu, kaçı eşiği geçti ve precision oranı gösteriliyor.

Geçmiş Performans:
{history_summary}

Mevcut Sorgular:
{current_queries}

Görevin:
- En önemli metrik PRECISION'dır: eşiği geçen ilan sayısı / toplam ilan sayısı
- Ortalama skoru değil, precision'ı maksimize et — çok ilan getirmek değil, doğru ilan getirmek önemli
- İdeal sorgu: run başına 3-7 ilan getirir, bunların %60'ı+ eşiği geçer
- Çok az ilan getiren sorgu (0-1): çok spesifik, biraz genişlet
- Çok fazla ilan getiren sorgu (10+): çok geniş, daha spesifik hale getir
- Düşük precision'lı sorguları kaldır veya daralt
- Yüksek precision'lı sorguların yapısını koru veya benzerlerini ekle
- Sorgu sayısını 5 ile sınırla
- LinkedIn boolean syntax kullan: AND, OR, NOT, "tırnak içi exact match"

SADECE geçerli JSON döndür, başka hiçbir şey yazma:
{{
  "analysis": "kısa analiz: hangi sorgular iyi/kötü çalıştı ve neden",
  "queries": [
    "optimize edilmiş sorgu 1",
    "optimize edilmiş sorgu 2",
    "optimize edilmiş sorgu 3",
    "optimize edilmiş sorgu 4",
    "optimize edilmiş sorgu 5"
  ]
}}"""


# ─── History yönetimi ─────────────────────────────────────────────────────────

def load_history() -> list[dict]:
    if not os.path.exists(RUN_HISTORY_FILE):
        return []
    with open(RUN_HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: list[dict]):
    with open(RUN_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def record_run(query_results: list[dict]):
    """
    Her run sonunda çağrılır.
    query_results: [{"query": str, "jobs": [{"title", "company", "score"}]}]
    """
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "queries": query_results,
    })
    save_history(history)
    logger.info(f"Run geçmişe kaydedildi. Toplam run: {len(history)}")
    return len(history)


# ─── Optimizasyon ─────────────────────────────────────────────────────────────

def _build_history_summary(history: list[dict]) -> str:
    """Son N run'daki sorgu performansını precision odaklı özetle."""
    from config import SCORE_THRESHOLD
    recent = history[-OPTIMIZE_EVERY_N_RUNS:]

    # Sorgu bazında istatistik topla
    query_stats: dict[str, dict] = {}
    for run in recent:
        for q_data in run["queries"]:
            q = q_data["query"][:80]
            if q not in query_stats:
                query_stats[q] = {"total_jobs": 0, "passed": 0, "scores": [], "runs": 0}

            query_stats[q]["runs"] += 1
            for job in q_data["jobs"]:
                score = job.get("score")
                if score is None:
                    continue
                query_stats[q]["total_jobs"] += 1
                query_stats[q]["scores"].append(score)
                if score >= SCORE_THRESHOLD:
                    query_stats[q]["passed"] += 1

    summary_lines = []
    for q, s in query_stats.items():
        avg       = round(sum(s["scores"]) / len(s["scores"]), 1) if s["scores"] else 0
        precision = round(s["passed"] / s["total_jobs"] * 100, 1) if s["total_jobs"] > 0 else 0
        avg_per_run = round(s["total_jobs"] / s["runs"], 1) if s["runs"] > 0 else 0

        # Değerlendirme etiketi
        if precision >= 60 and 3 <= avg_per_run <= 7:
            tag = "✅ İyi"
        elif avg_per_run > 10:
            tag = "⚠️ Çok geniş"
        elif avg_per_run < 2:
            tag = "⚠️ Çok dar"
        elif precision < 30:
            tag = "❌ Düşük precision"
        else:
            tag = "🔸 Orta"

        summary_lines.append(
            f'Sorgu: "{q}"\n'
            f'  {tag} | Run başına ilan: {avg_per_run} | '
            f'Precision: %{precision} | Ortalama skor: {avg}'
        )

    return "\n\n".join(summary_lines)


def _load_current_queries() -> list[str]:
    if os.path.exists(QUERIES_FILE):
        with open(QUERIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return SEARCH_QUERIES


def optimize_queries():
    logger.info("Sorgu optimizasyonu başlıyor...")
    history = load_history()

    if len(history) < OPTIMIZE_EVERY_N_RUNS:
        logger.info(f"Henüz yeterli veri yok ({len(history)}/{OPTIMIZE_EVERY_N_RUNS} run).")
        return

    history_summary  = _build_history_summary(history)
    current_queries  = _load_current_queries()

    prompt = OPTIMIZER_PROMPT.format(
        history_summary=history_summary,
        current_queries=json.dumps(current_queries, ensure_ascii=False, indent=2),
    )

    try:
        raw    = ask(prompt, expect_json=True)
        result = json.loads(raw)
        new_queries = result["queries"]
        analysis    = result.get("analysis", "")

        # Yeni sorguları kaydet
        with open(QUERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(new_queries, f, ensure_ascii=False, indent=2)

        logger.info(f"Sorgular optimize edildi. Analiz: {analysis}")
        logger.info("Yeni sorgular:")
        for i, q in enumerate(new_queries, 1):
            logger.info(f"  {i}. {q[:100]}")

        # History'yi sıfırla — yeni döngü başlasın
        save_history([])
        logger.info("Run geçmişi sıfırlandı, yeni döngü başlıyor.")

    except Exception as e:
        logger.error(f"Sorgu optimizasyonu başarısız: {e}")


def should_optimize(total_runs: int) -> bool:
    return total_runs % OPTIMIZE_EVERY_N_RUNS == 0
