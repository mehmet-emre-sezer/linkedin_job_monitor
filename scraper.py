import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import SEARCH_LOCATION, JOBS_PER_QUERY

logger = logging.getLogger(__name__)


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))


def _extract_job_id(url: str) -> str:
    try:
        return url.split("/view/")[1].split("/")[0].split("?")[0]
    except IndexError:
        return url


def scrape_jobs(queries: list[str]) -> list[dict]:
    driver = _build_driver()
    all_jobs = []

    try:
        for query in queries:
            logger.info(f"Searching: '{query[:80]}...'")
            jobs = _scrape_query(driver, query)
            logger.info(f"  → {len(jobs)} jobs found")
            for job in jobs:
                job["source_query"] = query  # hangi query'den geldiğini işaretle
            all_jobs.extend(jobs)
            _delay(3, 7)
    finally:
        driver.quit()

    return all_jobs


def _scrape_query(driver: webdriver.Chrome, query: str) -> list[dict]:
    location_param = (
        f"&location={SEARCH_LOCATION.replace(' ', '%20')}" if SEARCH_LOCATION else ""
    )
    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={query.replace(' ', '%20')}"
        f"{location_param}"
        "&f_TPR=r86400"   # son 24 saat
        "&sortBy=DD"
    )

    driver.get(url)
    _delay(3, 5)

    # Public sayfada LinkedIn bazen "Sign in" popup gösteriyor, kapat
    _dismiss_signin_modal(driver)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
        )
    except Exception:
        logger.warning(f"Sonuç listesi yüklenemedi: '{query}'")
        return []

    cards = driver.find_elements(
        By.CSS_SELECTOR, "ul.jobs-search__results-list li"
    )[:JOBS_PER_QUERY]

    jobs = []
    for card in cards:
        try:
            job = _extract_card(driver, card)
            if job:
                jobs.append(job)
                _delay(1, 3)
        except Exception as e:
            logger.debug(f"Kart parse hatası: {e}")

    return jobs


def _dismiss_signin_modal(driver: webdriver.Chrome):
    """LinkedIn'in 'Sign in to view' modal'ını kapat."""
    try:
        dismiss_btn = driver.find_element(
            By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']"
        )
        dismiss_btn.click()
        _delay(1, 2)
    except Exception:
        pass  # modal yoksa sorun değil


def _extract_card(driver: webdriver.Chrome, card) -> dict | None:
    try:
        link_el = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
        title = link_el.get_attribute("aria-label") or link_el.text.strip()
        link = link_el.get_attribute("href").split("?")[0]
        job_id = _extract_job_id(link)
    except Exception:
        return None

    try:
        company = card.find_element(
            By.CSS_SELECTOR, "h4.base-search-card__subtitle"
        ).text.strip()
    except Exception:
        company = "Unknown"

    try:
        location = card.find_element(
            By.CSS_SELECTOR, "span.job-search-card__location"
        ).text.strip()
    except Exception:
        location = ""

    try:
        posted_at = card.find_element(
            By.CSS_SELECTOR, "time.job-search-card__listdate, time.job-search-card__listdate--new"
        ).get_attribute("datetime") or card.find_element(
            By.CSS_SELECTOR, "time"
        ).text.strip()
    except Exception:
        posted_at = ""

    description, applicants = _get_description_and_applicants(driver, link)

    return {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location,
        "posted_at": posted_at,
        "applicants": applicants,
        "link": link,
        "description": description,
    }


def _get_description_and_applicants(driver: webdriver.Chrome, job_url: str) -> tuple[str, str]:
    """
    İlan sayfasından açıklama ve başvuran sayısını çek.
    Returns: (description, applicants)
    """
    description = ""
    applicants = ""

    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(job_url)
        _delay(2, 4)

        _dismiss_signin_modal(driver)

        # Açıklama
        try:
            desc_el = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.show-more-less-html__markup")
                )
            )
            description = desc_el.text.strip()[:3000]
        except Exception:
            try:
                description = driver.find_element(
                    By.CLASS_NAME, "description__text"
                ).text.strip()[:3000]
            except Exception:
                pass

        # Başvuran sayısı — birden fazla selector dene, LinkedIn class'ları değişebiliyor
        for selector in [
            "span.num-applicants__caption",
            "figcaption.num-applicants__caption",
            "span.jobs-unified-top-card__applicant-count",
            "span[class*='applicant']",
        ]:
            try:
                applicants = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                if applicants:
                    break
            except Exception:
                continue

    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return description, applicants
