
from utils import score_reviews
from scraper import scrape_reviews
from ml_models import get_sentiment_scores, get_verifier_scores


def main_func(url: str):
    reviews = scrape_reviews(url)
    score_reviews(reviews)

    review_texts = [r.text for r in reviews]
    sentiment_scores = get_sentiment_scores(review_texts)
    verifier_scores = get_verifier_scores(review_texts)

    grads = {
        "ldr": 0.0829,
        "eng": 0.4726,
        "len": 0.0363,
        "sent": 0.3277,
        "plag": 0.4035,
    }

    for review, sentiment, plagarism in zip(reviews, sentiment_scores, verifier_scores):
        review.score['sent'] = sentiment
        review.score['plag'] = plagarism

    for review in reviews:
        review.final = sum(grads[k] * review.score[k] for k in grads)
        review.final = min(review.final, 1.0)

    return reviews


if __name__ == '__main__':
    import time

    link = "https://www.flipkart.com/frozen-nuts-premium-mewa-mix-almonds-cashews-kiwi-walnuts-apricots-dates-blueberry-assorted-fruits/product-reviews/itmb599a803d76cb?pid=NDFH9GZZKGEQV8YK&lid=LSTNDFH9GZZKGEQV8YK24UYEG&marketplace=FLIPKART"

    start_time = time.perf_counter()
    reviews = main_func(link)
    stop_time = time.perf_counter()

    print(f"Took {stop_time - start_time:.3f} seconds to scrape")
    print(f"Scraped: {len(reviews)} reviews")
