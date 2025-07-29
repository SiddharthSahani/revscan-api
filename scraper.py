
from utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor


def scrape_reviews(url: str) -> list[FlipkartReview]:
    page_count = get_total_pages(url)

    if page_count == 0:
        logger.warning(f"[ITEM={get_uuid(url)}]: No pages to scrape")
        return []
    else:
        logger.info(f"[ITEM={get_uuid(url)}]: {page_count=}")

    page_batches = batch_pages(page_count)
    logger.info(f"[ITEM={get_uuid(url)}]: {page_batches=}")

    with ThreadPoolExecutor(NUM_THREADS) as executor:
        futures = [
            executor.submit(scrape_multiple_pages, url, start, end, thread_id)
            for thread_id, (start, end) in enumerate(page_batches)
        ]
        all_reviews = [
            review
            for future in futures
            for review in future.result()
        ]

    logger.info(f"[ITEM={get_uuid(url)}]: Scraped {len(all_reviews)} reviews")
    return all_reviews


def scrape_multiple_pages(url: str, start: int, end: int, thread_id: int) -> list[FlipkartReview]:
    driver = make_webdriver()
    range_reviews = []
    empty_page_count = 0

    try:
        for page in range(start, end+1):
            page_reviews = scrape_single_page(driver, url, page)
            range_reviews.extend(page_reviews)
            if not page_reviews:
                empty_page_count += 1
                logger.info(f"[ITEM={get_uuid(url)}, PAGE={page}, THREAD={thread_id}]: Page had no reviews, {empty_page_count=}")
                if empty_page_count >= MAX_EMPTY_PAGE_COUNT:
                    logger.warning(f"[ITEM={get_uuid(url)}, THREAD={thread_id}]: Encountered max amount of empty pages")
                    break
            else:
                logger.info(f"[ITEM={get_uuid(url)}, PAGE={page}, THREAD={thread_id}]: Page had {len(page_reviews)} reviews")
    except Exception as err:
        logger.error(f"[ITEM={get_uuid(url)}, THREAD={thread_id}]: Encountered error while scraping multiple pages | ERROR: {err}")
    finally:
        driver.quit()

    return range_reviews


def scrape_single_page(driver: webdriver.Chrome, url: str, page: int) -> list[FlipkartReview]:
    paged_url = f"{url}&page={page}"
    driver.get(paged_url)

    wait = WebDriverWait(driver, timeout=3.0)
    try:
        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.EKFha-"))
        )
    except:
        return []

    reviews_divs = driver.find_elements(By.CSS_SELECTOR, "div.EKFha-")
    result = []

    for div in reviews_divs:
        review = FlipkartReview(
            text=None,
            user=None,
            rating=None,
            time=None,
            ldr=None,
            score=None,
            final=None
        )

        try:
            # text
            review.text = div.find_element(By.CSS_SELECTOR, "div.ZmyHeo").text
            review.text = clean_text(review.text)
            # rating
            review.rating = div.find_element(By.CSS_SELECTOR, "div.XQDdHH.Ga3i8K").text
            review.rating = review.rating.strip()
            # user & time
            p_elems = div.find_elements(By.CSS_SELECTOR, "p._2NsDsF")
            for p_elem in p_elems:
                class_list = p_elem.get_attribute("class").split()
                if "AwS1CA" in class_list:
                    review.user = p_elem.text.strip()
                elif len(class_list) == 1:
                    review.time = p_elem.text.strip()
            # ldr
            ldr_elems = div.find_elements(By.CSS_SELECTOR, "div._6kK6mk")
            review.ldr = [0, 0]
            for ldr_elem in ldr_elems:
                class_list = div.get_attribute("class").split()
                if "_6kK6mk" in class_list:
                    if "aQymJL" in class_list:
                        review.ldr[1] = int(ldr_elem.text.strip())
                    else:
                        review.ldr[0] = int(ldr_elem.text.strip())

            result.append(review)
        except:
            pass

    return result


def get_total_pages(url: str) -> int:
    try:
        driver = make_webdriver()
        driver.get(url)
        wait = WebDriverWait(driver, timeout=5.0)
        page_divs = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._1G0WLw.mpIySA"))
        )

        for div in page_divs:
            try:
                span = div.find_element(By.TAG_NAME, "span")
                if "Page" in span.text and "of" in span.text:
                    return int(span.text.strip().split()[-1])
            except:
                pass
        logger.error(f"[ITEM={get_uuid(url)}]: Unable to find the number of pages of reviews")
        return 1
    except Exception as err:
        logger.error(f"[ITEM={get_uuid(url)}] Encountered error while finding the number of pages of reviews | ERROR: {err}")
        return 1
    finally:
        driver.quit()
