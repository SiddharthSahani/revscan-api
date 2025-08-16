from constants import *
from selenium import webdriver
from logging import getLogger, StreamHandler, Formatter
from dataclasses import dataclass
from pydantic import BaseModel
import re


def make_logger(name):
    logger = getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel("INFO")
    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = make_logger("api")


# used by fast api to create docs and automatic parsing of json body
class UrlRequest(BaseModel):
    url: str


@dataclass
class FlipkartReview:
    text: str
    user: str
    rating: str
    time: str
    ldr: list[int]
    score: dict[str, float]
    final: float

    def format(self) -> dict[str]:
        return {
            "review": self.text,
            "user": self.user,
            "rating": self.rating,
            "time": self.time,
            "ldr": self.ldr,
            "score": self.score,
            "final_score": self.final,
        }


@dataclass
class AmazonProduct:
    title: str
    url: str
    image: str
    price: str

    def format(self) -> dict[str]:
        return {
            "title": self.title,
            "url": self.url,
            "image": self.image,
            "price": self.price,
        }


def make_webdriver(use_proxy=False):
    from selenium.webdriver.chrome.service import Service
    import os
    import time
    import random

    # Use different user agents to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    proxies = [
        "23.95.150.145:6114",
        "198.23.239.134:6540",
        "45.38.107.97:6014",
        "207.244.217.165:6712",
        "107.172.163.27:6543",
        "104.222.161.211:6343",
        "64.137.96.74:6641",
        "216.10.27.159:6837",
        "136.0.207.84:6661",
        "142.147.128.93:6593",
    ]

    selected_user_agent = random.choice(user_agents)

    options = [
        f"--user-agent={selected_user_agent}",
        "--accept-language=en-US,en;q=0.9",
        "--headless=new",  # Keep headless for Docker
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",  # Hide automation
        "--exclude-switches=enable-automation",  # Hide automation
        "--disable-extensions-except=/usr/lib/chromium-browser/extensions",
        "--disable-plugins-except=/usr/lib/chromium-browser/plugins",
        "--window-size=1366,768",  # More common resolution
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--disable-ipc-flooding-protection",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI,VizDisplayCompositor",
        "--disable-default-apps",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--safebrowsing-disable-auto-update",
        "--user-data-dir=/app/tmp",
        "--crash-dumps-dir=/tmp",
        "--disable-crash-reporter",
        "--enable-logging",
        "--log-level=0",
        "--v=1",
    ]

    if use_proxy:
        options.append(f"--proxy-server={random.choice(proxies)}")

    webdriver_options = webdriver.ChromeOptions()
    webdriver_options.binary_location = "/usr/bin/chromium"

    # Add experimental options to make browser less detectable
    webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    webdriver_options.add_experimental_option("useAutomationExtension", False)

    for opt in options:
        webdriver_options.add_argument(opt)

    # Try to find the ChromeDriver in various possible locations
    possible_driver_paths = [
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromium-driver",
    ]

    driver_path = None
    for path in possible_driver_paths:
        if os.path.exists(path):
            driver_path = path
            break

    # Retry logic for webdriver creation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if driver_path:
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=webdriver_options)

                # Execute script to hide webdriver property
                driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                logger.info(
                    f"Created webdriver.Chrome instance with driver at {driver_path} (attempt {attempt + 1})"
                )
                return driver
            else:
                # Fallback to default (may not work on ARM64)
                logger.warning(
                    "ChromeDriver not found in expected locations, using default"
                )
                return webdriver.Chrome(options=webdriver_options)
        except Exception as e:
            logger.error(
                f"Failed to create webdriver (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                raise e


def score_reviews(reviews: list[FlipkartReview]) -> None:
    overall_ldr = get_overall_ldr(reviews)

    for review in reviews:
        length_score = min(len(review.text) / 300, 1.0)
        review_ldr = get_single_ldr(review)
        ldr_aligment = 1.0 - abs(review_ldr - overall_ldr)
        engagement = min(sum(review.ldr) / 10, 1.0)
        review.score = {
            "ldr": ldr_aligment,
            "eng": engagement,
            "len": length_score,
        }


def get_uuid(url: str) -> str:
    start = "https://www.flipkart.com/"
    assert url.startswith(start)
    return url.replace(start, "").split("/")[0]


def get_sentiment_text(score: float) -> str:
    if 0.0 <= score < 0.05:
        return "very negative"
    elif 0.05 <= score < 0.15:
        return "negative"
    elif 0.15 <= score < 0.35:
        return "neutral"
    elif 0.35 <= score < 0.75:
        return "positive"
    else:
        return "very positive"


def clean_text(string: str) -> str:
    if not string:
        return ""
    string = re.sub(r"\s+", " ", string.strip())
    string = string.replace("READ MORE", "").strip()
    return string


def batch_pages(page_count: int) -> list[tuple[int, int]]:
    page_count = min(page_count, MAX_REVIEW_PAGES)
    batches = []
    pages_per_thread, remainder = divmod(page_count, NUM_THREADS)

    start = 1
    for i in range(NUM_THREADS):
        end = start + pages_per_thread + (i < remainder)
        if start < end:
            batches.append((start, end - 1))
        start = end

    return batches


def get_overall_ldr(reviews: list[FlipkartReview]) -> float:
    likes = sum(rev.ldr[0] for rev in reviews)
    dislikes = sum(rev.ldr[1] for rev in reviews)
    if likes + dislikes == 0:
        return 0.0
    return (likes - dislikes) / (likes + dislikes)


def get_single_ldr(review: FlipkartReview) -> float:
    likes = review.ldr[0]
    dislikes = review.ldr[1]
    if likes + dislikes == 0:
        return 0.0
    return (likes - dislikes) / (likes + dislikes)
