
from utils import *
from scraper import scrape_reviews, get_similar_items_from_amazon
from ml_models import get_sentiment_scores, get_verifier_scores
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from upstash_redis import Redis
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json


load_dotenv()

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    # TODO: change required
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)

try:
    redis = Redis.from_env()
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis = None

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm_model = genai.GenerativeModel("gemini-1.5-flash")

logger = make_logger("entry")


@app.get("/")
def health_check():
    return {"health": "ok"}


@app.post("/analyse")
@limiter.limit(f"{HITS_PER_MINUTE}/minute")
async def analyse(request: Request, url: UrlRequest):
    url = url.url
    url_id = get_uuid(url)
    logger.info(f"Hit with {url_id!r}, {url=}")

    # Check cache only if Redis is available
    if redis:
        try:
            if res := redis.get(url_id):
                logger.info(f"Returning data for {url_id!r} from cache")
                return json.loads(res)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")

    logger.info(f"Processing {url_id!r}")

    reviews = get_processed_reviews(url)

    # If scraping failed or returned nothing, short-circuit with a friendly response
    if not reviews:
        logger.warning(f"No reviews scraped for {url_id!r}; returning empty result.")
        return {
            "Reviews": [],
            "Summary": "",
            "ReviewsScraped": 0,
            "SentimentScore": 0,
            "UserSentiment": "neutral",
            "FakeRatio": 0,
            "RelatedItems": [],
        }

    mean_final_score = sum(r.final for r in reviews) / len(reviews)
    mean_sentiment_score = sum(r.score['sent'] for r in reviews) / len(reviews)
    mean_fake_score = sum(r.score['plag'] > 0.5 for r in reviews) / len(reviews)
    user_sentiment = get_sentiment_text(mean_final_score)

    summary = get_llm_summary(reviews[:LLM_REVIEW_COUNT])
    summary = clean_text(summary)

    similar_items = get_similar_items_from_amazon(url_id)

    return_data = { 
        "Reviews" : [r.format() for r in reviews],
        "Summary" : summary,
        "ReviewsScraped": len(reviews),
        "SentimentScore" : (round(mean_sentiment_score * 100)),
        "UserSentiment": user_sentiment,
        "FakeRatio": round(mean_fake_score * 100),
        "RelatedItems": [r.format() for r in similar_items],
    }

    # Save to cache only if Redis is available
    if redis:
        try:
            redis.set(url_id, return_data)
            logger.info(f"Dumped data to redis for {url_id!r}")
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
    
    return return_data


def get_processed_reviews(url: str):
    reviews = scrape_reviews(url)
    score_reviews(reviews)

    # Run ML only on reviews that have text; align results back by index
    text_indices = [i for i, r in enumerate(reviews) if r.text and r.text.strip()]
    review_texts = [reviews[i].text for i in text_indices]
    
    # Only run ML models if we have valid text reviews
    if review_texts:
        sentiment_scores = get_sentiment_scores(review_texts)
        verifier_scores = get_verifier_scores(review_texts)
    else:
        sentiment_scores = []
        verifier_scores = []
        logger.warning("No valid review texts found for ML processing")

    grads = {
        "ldr": 0.0829,
        "eng": 0.4726,
        "len": 0.0363,
        "sent": 0.3277,
        "plag": 0.4035,
    }

    # Initialize defaults
    for r in reviews:
        r.score.setdefault('sent', 0.0)
        r.score.setdefault('plag', 0.0)

    # Assign scores to the corresponding reviews with text
    for idx, sentiment, plagarism in zip(text_indices, sentiment_scores, verifier_scores):
        reviews[idx].score['sent'] = float(sentiment)
        reviews[idx].score['plag'] = float(plagarism)

    for review in reviews:
        review.final = sum(grads[k] * review.score[k] for k in grads)
        review.final = min(review.final, 1.0)

    return reviews


def get_llm_summary(reviews: list[FlipkartReview]) -> str:
    text_list = [r.text for r in reviews]
    llm_prompt = (
        "You are given a list of user reviews. Read them all carefully and generate a concise, balanced summary that captures the overall sentiment, common themes, notable pros and cons, and any frequently mentioned issues or praises. Use clear language and aim to reflect the general consensus as well as any strong outliers. DO NOT USE POINTS. "
        f"GIVE ME A 150 WORD REVIEW: {text_list}"
    )
    try:
        response = llm_model.generate_content(llm_prompt).text
        logger.info(f"Generated llm response of size = {len(response)}")
        return response
    except Exception as err:
        logger.error(f"Encountered error while generating llm summary | ERROR: {err}")
        return ''


if __name__ == '__main__':
    import uvicorn
    DEV_MODE = True

    if DEV_MODE:
        uvicorn.run("main:app", reload=True)
    else:
        uvicorn.run("main:app", host='0.0.0.0')
