
from utils import *
from scraper import scrape_reviews
from ml_models import get_sentiment_scores, get_verifier_scores
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from upstash_redis import Redis
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json


load_dotenv()
app = FastAPI()
redis = Redis.from_env()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm_model = genai.GenerativeModel("gemini-1.5-flash")
logger = make_logger("entry")


@app.get("/")
def health_check():
    return {"health": "ok"}


@app.post("/analyse")
async def analyse(request: Request, url: UrlRequest):
    url = url.url
    url_id = get_uuid(url)
    logger.info(f"Hit with {url_id!r}")

    if res := redis.get(url_id):
        logger.info(f"Returning data for {url_id!r} from cache")
        return json.loads(res)

    logger.info(f"Processing {url_id!r}")

    reviews = get_processed_reviews(url)

    mean_final_score = sum(r.final for r in reviews) / len(reviews)
    mean_sentiment_score = sum(r.score['sent'] for r in reviews) / len(reviews)
    mean_fake_score = sum(r.score['plag'] > 0.5 for r in reviews) / len(reviews)
    user_sentiment = get_sentiment_text(mean_final_score)

    summary = get_llm_summary(reviews[:LLM_REVIEW_COUNT])
    summary = clean_text(summary)

    return_data = { 
        "Reviews" : [r.format() for r in reviews],
        "Summary" : summary,
        "ReviewsScraped": len(reviews),
        "SentimentScore" : (round(mean_sentiment_score * 100)),
        "UserSentiment": user_sentiment,
        "FakeRatio": round(mean_fake_score * 100),
        "RelatedItems": [],
        # "RelatedItems": similar_items,
    }

    redis.set(url_id, return_data)
    logger.info(f"Dumped data to redis for {url_id!r}")
    return return_data


def get_processed_reviews(url: str):
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
    uvicorn.run("main:app", reload=True)
