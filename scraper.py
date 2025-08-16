from utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import time


def scrape_reviews(url: str) -> list[FlipkartReview]:
    page_count = get_total_pages(url)
    url_id = get_uuid(url)

    if page_count == 0:
        logger.warning(f"[ITEM={url_id}]: No pages to scrape")
        return []
    else:
        logger.info(f"[ITEM={url_id}]: {page_count=}")

    page_batches = batch_pages(page_count)
    logger.info(f"[ITEM={url_id}]: {page_batches=}")

    with ThreadPoolExecutor(NUM_THREADS) as executor:
        futures = [
            executor.submit(scrape_multiple_pages, url, start, end, thread_id)
            for thread_id, (start, end) in enumerate(page_batches)
        ]
        all_reviews = [review for future in futures for review in future.result()]

    logger.info(f"[ITEM={url_id}]: Scraped {len(all_reviews)} reviews")
    return all_reviews


def scrape_multiple_pages(
    url: str, start: int, end: int, thread_id: int
) -> list[FlipkartReview]:
    driver = None
    range_reviews = []
    empty_page_count = 0
    url_id = get_uuid(url)

    try:
        driver = make_webdriver()
        for page in range(start, end + 1):
            # small backoff between pages
            time.sleep(0.5)  # Increased from 0.2 to 0.5 for better stability

            # retry each page once if it fails due to transient errors
            max_page_retries = 2
            page_reviews = []

            for retry in range(max_page_retries):
                try:
                    page_reviews = scrape_single_page(driver, url, page)
                    break  # Success, exit retry loop
                except Exception as e:
                    logger.warning(
                        f"[ITEM={url_id}, PAGE={page}, THREAD={thread_id}]: Error on attempt {retry + 1}: {e}"
                    )
                    if retry < max_page_retries - 1:  # Not the last retry
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        time.sleep(1)  # Wait before retry
                        driver = make_webdriver()
                    else:
                        logger.error(
                            f"[ITEM={url_id}, PAGE={page}, THREAD={thread_id}]: Failed after {max_page_retries} attempts"
                        )
                        page_reviews = []  # Empty list on failure

            range_reviews.extend(page_reviews)
            if not page_reviews:
                empty_page_count += 1
                logger.info(
                    f"[ITEM={url_id}, PAGE={page}, THREAD={thread_id}]: Page had no reviews, {empty_page_count=}"
                )
                if empty_page_count >= MAX_EMPTY_PAGE_COUNT:
                    logger.warning(
                        f"[ITEM={url_id}, THREAD={thread_id}]: Encountered max amount of empty pages"
                    )
                    break
            else:
                logger.info(
                    f"[ITEM={url_id}, PAGE={page}, THREAD={thread_id}]: Page had {len(page_reviews)} reviews"
                )
    except Exception as err:
        logger.error(
            f"[ITEM={url_id}, THREAD={thread_id}]: Encountered error while scraping multiple pages | ERROR: {err}"
        )
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(
                    f"[ITEM={url_id}, THREAD={thread_id}]: Error while quitting driver: {e}"
                )

    return range_reviews


def scrape_single_page(
    driver: webdriver.Chrome, url: str, page: int
) -> list[FlipkartReview]:
    paged_url = f"{url}&page={page}"
    logger.info(f"[PAGE={page}] Navigating to: {paged_url}")

    try:
        driver.get(paged_url)
        logger.info(
            f"[PAGE={page}] Successfully loaded page, current URL: {driver.current_url}"
        )
        logger.info(f"[PAGE={page}] Page title: {driver.title}")
    except Exception as e:
        logger.error(f"[PAGE={page}] Failed to load page: {e}")
        return []

    wait = WebDriverWait(driver, timeout=8.0)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.EKFha-")))
        logger.info(f"[PAGE={page}] Found review elements on page")
    except Exception as e:
        logger.warning(f"[PAGE={page}] Review elements not found: {e}")
        logger.info(f"[PAGE={page}] Page source length: {len(driver.page_source)}")
        # Log first 500 chars of page source to see what we got
        logger.info(f"[PAGE={page}] Page source preview: {driver.page_source[:500]}")
        return []

    reviews_divs = driver.find_elements(By.CSS_SELECTOR, "div.EKFha-")
    logger.info(f"[PAGE={page}] Found {len(reviews_divs)} review divs")
    result = []

    for div in reviews_divs:
        review = FlipkartReview(
            text=None,
            user=None,
            rating=None,
            time=None,
            ldr=None,
            score=None,
            final=None,
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
                class_list = ldr_elem.get_attribute("class").split()
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
    import time
    import random

    driver = None
    try:
        logger.info(f"[get_total_pages] Starting for URL: {url}")
        driver = make_webdriver()
        logger.info(f"[get_total_pages] WebDriver created, navigating to URL")

        # Add random delay to seem more human-like
        time.sleep(random.uniform(1, 3))

        # Add another delay before going to Flipkart
        time.sleep(random.uniform(2, 4))

        driver.get(url)
        logger.info(f"[get_total_pages] Page loaded, current URL: {driver.current_url}")
        logger.info(f"[get_total_pages] Page title: {driver.title}")

        # Wait a bit for page to fully load
        time.sleep(random.uniform(2, 5))

        wait = WebDriverWait(driver, timeout=10.0)  # Increased timeout
        logger.info(f"[get_total_pages] Waiting for pagination elements...")
        page_divs = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._1G0WLw.mpIySA"))
        )
        logger.info(f"[get_total_pages] Found {len(page_divs)} pagination divs")

        for i, div in enumerate(page_divs):
            try:
                span = div.find_element(By.TAG_NAME, "span")
                span_text = span.text
                logger.info(f"[get_total_pages] Pagination div {i}: '{span_text}'")
                if "Page" in span_text and "of" in span_text:
                    total_pages = int(span_text.strip().split()[-1])
                    logger.info(f"[get_total_pages] Found total pages: {total_pages}")
                    return total_pages
            except Exception as e:
                logger.warning(
                    f"[get_total_pages] Error processing pagination div {i}: {e}"
                )

        logger.error(
            f"[ITEM={get_uuid(url)}]: Unable to find the number of pages of reviews"
        )
        logger.info(f"[get_total_pages] Page source length: {len(driver.page_source)}")
        logger.info(
            f"[get_total_pages] Page source preview: {driver.page_source[:1000]}"
        )
        return 1
    except Exception as err:
        logger.error(
            f"[ITEM={get_uuid(url)}] Encountered error while finding the number of pages of reviews | ERROR: {err}"
        )
        if driver:
            try:
                logger.info(
                    f"[get_total_pages] Error occurred, current URL: {driver.current_url}"
                )
                logger.info(
                    f"[get_total_pages] Error page source length: {len(driver.page_source)}"
                )
                logger.info(
                    f"[get_total_pages] Error page source preview: {driver.page_source[:1000]}"
                )
            except:
                logger.warning(
                    "[get_total_pages] Could not get page source after error"
                )
        return 1
    finally:
        if driver:
            driver.quit()


def get_similar_items_from_amazon(url_id: str) -> list[AmazonProduct]:
    url_id = url_id.replace("-", "+")
    driver = make_webdriver(use_proxy=True)
    wait = WebDriverWait(driver, timeout=5.0)
    results = []

    try:
        driver.get(f"https://www.amazon.in/s?k={url_id}")

        container_xpath = '//div[contains(@class, "puis-card-container")]'
        wait.until(EC.presence_of_all_elements_located((By.XPATH, container_xpath)))

        images = driver.find_elements(By.XPATH, f"{container_xpath}//img")
        titles = driver.find_elements(By.XPATH, f"{container_xpath}//a//h2//span")
        prices = driver.find_elements(
            By.XPATH, f'{container_xpath}//span[@class="a-price-whole"]'
        )
        links = driver.find_elements(By.XPATH, f"{container_xpath}//a")

        min_length = min(len(ls) for ls in (images, titles, prices, links))
        for i in range(min(5, min_length)):
            img_src = images[i].get_attribute("src")
            title = titles[i].text
            price = prices[i].text
            link = links[i].get_attribute("href")

            # weird bug: some links are 'javascript:void(0)'
            if not link.startswith("https://"):
                continue

            results.append(
                AmazonProduct(
                    title=title,
                    url=link,
                    image=img_src,
                    price=price,
                )
            )
    except Exception as err:
        logger.error(
            f"Encountered error while fetching similar products fromm amazon | ERROR: {err}"
        )
    finally:
        driver.quit()

    return results
