import json
import os
from config import SEEN_JOBS_FILE


def load_seen_jobs() -> set:
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    with open(SEEN_JOBS_FILE, "r") as f:
        return set(json.load(f))


def save_seen_jobs(seen: set):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)


def is_new_job(job_id: str, seen: set) -> bool:
    return job_id not in seen


def mark_job_seen(job_id: str, seen: set):
    seen.add(job_id)
