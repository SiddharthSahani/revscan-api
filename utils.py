
from constants import *
from selenium import webdriver
from logging import getLogger, StreamHandler, Formatter
from dataclasses import dataclass
import re


logger = getLogger("api")
logger.setLevel("INFO")
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class FlipkartReview:
    text: str
    user: str
    rating: str
    time: str
    ldr: list[int]
    score: dict[str, float]
    final: float


def make_webdriver():
    options = [
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "--accept-language=en-US,en;q=0.9",
        "--headless",
    ]

    webdriver_options = webdriver.ChromeOptions()
    for opt in options:
        webdriver_options.add_argument(opt)

    logger.info("Created webdriver.Chrome instance")
    return webdriver.Chrome(webdriver_options)


def score_reviews(reviews: list[FlipkartReview]) -> None:
    overall_ldr = get_overall_ldr(reviews)

    for review in reviews:
        length_score = min(len(review.text) / 300, 1.0)
        review_ldr = get_single_ldr(review)
        ldr_aligment = 1.0 - abs(review_ldr - overall_ldr)
        engagement = min(sum(review.ldr) / 10, 1.0)
        review.score = {
            'ldr': ldr_aligment,
            'eng': engagement,
            'len': length_score,
        }


def get_uuid(url: str) -> str:
    start = 'https://www.flipkart.com/'
    assert url.startswith(start)
    return url.replace(start, "").split("/")[0]


def clean_text(string: str) -> str:
    string = re.sub(r"[^a-zA-Z0-9\s]", "", string)
    string = re.sub(r"\s+", " ", string.strip())
    return string.replace("READ MORE", "").strip()


def batch_pages(page_count: int) -> list[tuple[int, int]]:
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
