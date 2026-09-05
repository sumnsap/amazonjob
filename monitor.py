import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.json"
SEEN_JOBS_PATH = SCRIPT_DIR / "seen_jobs.json"

def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        logging.warning(f"Config file not found at {config_path}. Using environment defaults.")
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def load_seen_jobs() -> set:
    if SEEN_JOBS_PATH.exists():
        try:
            with open(SEEN_JOBS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            logging.error(f"Could not read seen_jobs.json: {e}")
    return set()

def save_seen_jobs(seen_jobs: set):
    try:
        with open(SEEN_JOBS_PATH, "w", encoding="utf-8") as f:
            json.dump(list(seen_jobs), f, indent=2)
    except Exception as e:
        logging.error(f"Could not write seen_jobs.json: {e}")

async def scrape_jobs(url: str) -> list:
    jobs = []
    async with async_playwright() as p:
        # Linux / GitHub Actions flags
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        logging.info(f"Navigating to {url}...")
        try:
            # Use domcontentloaded for fast reliable loading on Linux cloud runners
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(5000)
            
            body_text = await page.evaluate("document.body.innerText")
            lines = [line.strip() for line in body_text.split("\n") if line.strip()]
            
            current_job = None
            for idx, line in enumerate(lines):
                if line in ["Warehouse Operative", "Customer Service Associate", "Warehouse Associate", "Delivery Station Warehouse Associate", "Fulfilment Centre Warehouse Associate"]:
                    if current_job and current_job.get("title"):
                        jobs.append(current_job)
                    current_job = {
                        "title": line,
                        "job_type": "Standard",
                        "duration": "Fixed-term / Permanent",
                        "pay_rate": "Standard Rate",
                        "location": "Multiple Locations"
                    }
                elif current_job:
                    if line.startswith("Type:"):
                        current_job["job_type"] = line.replace("Type:", "").strip()
                    elif line.startswith("Duration:"):
                        current_job["duration"] = line.replace("Duration:", "").strip()
                    elif line.startswith("Pay rate:"):
                        current_job["pay_rate"] = line.replace("Pay rate:", "").strip()
                    elif any(c in line for c in ["England", "Wales", "Scotland", "Northern Ireland", "Coventry", "Birmingham", "Derby", "Remote", "Multiple"]):
                        current_job["location"] = line
                        jobs.append(current_job)
                        current_job = None
            
            if current_job and current_job.get("title"):
                jobs.append(current_job)

        except Exception as e:
            logging.error(f"Error scraping jobsatamazon.co.uk: {e}")
        finally:
            await browser.close()
            
    return jobs

def generate_job_id(job: dict) -> str:
    return f"{job.get('title')}_{job.get('location')}_{job.get('pay_rate')}"

async def check_once(config: dict, notifier: TelegramNotifier):
    raw_locations = config.get("target_locations", [])
    target_locations = [loc.lower() for loc in raw_locations]
    url = config.get("url", "https://www.jobsatamazon.co.uk/app#/jobSearch")
    
    seen_jobs = load_seen_jobs()
    if not target_locations:
        logging.info("Checking for jobs at Amazon UK across ALL locations...")
    else:
        logging.info(f"Checking for jobs at Amazon UK for target locations: {target_locations}...")
    
    all_jobs = await scrape_jobs(url)
    logging.info(f"Total jobs found on portal: {len(all_jobs)}")
    
    new_jobs_count = 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for job in all_jobs:
        job_loc = job.get("location", "").lower()
        if not target_locations:
            location_matched = True
        else:
            location_matched = any(target in job_loc for target in target_locations) or any(target in job.get("title", "").lower() for target in target_locations)
            if not location_matched and ("multiple" in job_loc or "midlands" in job_loc):
                location_matched = True
            
        if location_matched:
            job_id = generate_job_id(job)
            if job_id not in seen_jobs:
                logging.info(f"🚨 NEW MATCHED JOB: {job.get('title')} - {job.get('location')} ({job.get('pay_rate')})")
                job["detected_at"] = now_str
                notifier.send_job_alert(job, url)
                seen_jobs.add(job_id)
                new_jobs_count += 1

    save_seen_jobs(seen_jobs)
    logging.info(f"Check complete. {new_jobs_count} new alerts sent.")

async def main():
    parser = argparse.ArgumentParser(description="Amazon UK Job Search Monitor")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--single-run", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    
    tg_config = config.get("telegram", {})
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg_config.get("bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or tg_config.get("chat_id", "")
    
    notifier = TelegramNotifier(
        bot_token=bot_token,
        chat_id=chat_id
    )

    interval_minutes = config.get("check_interval_minutes", 60)

    try:
        if args.single_run or os.environ.get("GITHUB_ACTIONS"):
            await check_once(config, notifier)
        else:
            logging.info(f"Starting Amazon UK Job Notifier daemon (Interval: {interval_minutes} minutes)...")
            while True:
                await check_once(config, notifier)
                logging.info(f"Sleeping for {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
    except Exception as e:
        logging.error(f"Execution finished with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
