import logging
import os
import sys
from config import SCORE_THRESHOLD, CV_PATH
from query_generator import load_queries
from scraper import scrape_jobs
from scorer import score_job
from storage import load_seen_jobs, save_seen_jobs, is_new_job, mark_job_seen
from notifier import send_job_notification, send_summary
from query_optimizer import record_run, optimize_queries, should_optimize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("run.log")],
)
logger = logging.getLogger(__name__)

PROFILE_FILE = "profile.json"


def _auto_setup():
    """profile.json yoksa CV'den otomatik oluştur."""
    if os.path.exists(PROFILE_FILE):
        return

    if not CV_PATH or not os.path.exists(CV_PATH):
        logger.warning(
            "profile.json bulunamadı ve CV_PATH ayarlanmamış. "
            "config.py'deki varsayılan profil kullanılıyor."
        )
        return

    logger.info("profile.json bulunamadı, CV'den otomatik oluşturuluyor...")
    from setup import extract_text_from_pdf, generate_profile_and_queries, save
    try:
        cv_text = extract_text_from_pdf(CV_PATH)
        profile, queries = generate_profile_and_queries(cv_text)
        save(profile, queries)
        logger.info("Profil ve sorgular başarıyla oluşturuldu.")
    except Exception as e:
        logger.error(f"Otomatik setup başarısız: {e}. Varsayılan profil kullanılıyor.")


def run():
    logger.info("=== Job monitor başlatıldı ===")
    _auto_setup()

    seen    = load_seen_jobs()
    queries = load_queries()
    all_jobs = scrape_jobs(queries)
    logger.info(f"{len(all_jobs)} ilan tarandı (query'ler arası tekrarlar dahil)")

    # Dedup'tan önce: hangi job ID hangi querylerde göründü → map'e kaydet
    # Aynı ilan birden fazla query tarafından bulunmuş olabilir
    job_to_queries: dict[str, list[str]] = {}
    for job in all_jobs:
        jid = job["id"]
        q   = job.get("source_query", "")
        if jid not in job_to_queries:
            job_to_queries[jid] = []
        if q and q not in job_to_queries[jid]:
            job_to_queries[jid].append(q)

    # Unique job listesi (ID bazında ilk görülen tutulur)
    seen_ids: set[str] = set()
    unique_jobs = []
    for job in all_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    new_jobs = [j for j in unique_jobs if is_new_job(j["id"], seen)]
    logger.info(f"{len(unique_jobs)} unique ilan, {len(new_jobs)} yeni")

    # Her sorgu için performans takibi
    query_results: dict[str, list] = {q: [] for q in queries}

    sent = 0
    for job in new_jobs:
        result = score_job(job)
        if result is None:
            # Scoring başarısız — seen'e ekleme, bir sonraki run'da tekrar denensin
            logger.warning(f"  Scoring başarısız, atlanıyor: {job['title']}")
            continue

        # Scoring başarılıysa seen'e ekle
        mark_job_seen(job["id"], seen)

        score, reason = result["score"], result["reason"]
        status = "✓ GÖNDERİLDİ" if score >= SCORE_THRESHOLD else "✗ atlandı"
        logger.info(f"  [{score}] {status} — {job['title']} @ {job['company']}")

        # Bu ilanı bulan TÜM querylere skoru yaz
        entry = {
            "title":   job["title"],
            "company": job["company"],
            "score":   score,
            "sent":    score >= SCORE_THRESHOLD,
        }
        for q in job_to_queries.get(job["id"], []):
            if q in query_results:
                query_results[q].append(entry)

        if score >= SCORE_THRESHOLD:
            send_job_notification(job, score=score, reason=reason)
            sent += 1

    save_seen_jobs(seen)
    send_summary(len(unique_jobs), len(new_jobs), sent)
    logger.info(f"=== Tamamlandı. {sent} bildirim gönderildi ===")

    # Run'u geçmişe kaydet
    formatted = [{"query": q, "jobs": jobs_list} for q, jobs_list in query_results.items()]
    total_runs = record_run(formatted)

    # Yeterli veri birikti mi? Optimize et
    if should_optimize(total_runs):
        logger.info(f"{total_runs} run tamamlandı, sorgular optimize ediliyor...")
        optimize_queries()


if __name__ == "__main__":
    run()
