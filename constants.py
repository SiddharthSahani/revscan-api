
# rate limiting
HITS_PER_MINUTE = 5
# how many threads to use for scraping (kept low for stability in containers)
NUM_THREADS = 1  # Reduced to 1 for Docker stability
# maximum amount of empty pages after which scraping is terminated for the thread
MAX_EMPTY_PAGE_COUNT = 3
# max amount of pages that can be scraped per product
MAX_REVIEW_PAGES = 10
# any text above this length is given a score of 1.0 in `length_score`
LENGTH_SCORE_NORM = 300
# interactions for achieving 1.0 in engagement
VOTES_NORM = 10
# reviews to be sent to llm
LLM_REVIEW_COUNT = 25

# if the max page count is lower than the threads present, its just a waste
NUM_THREADS = min(NUM_THREADS, MAX_REVIEW_PAGES)
