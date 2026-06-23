import time

from selenium.webdriver.common.by import By

import config


def dedupe_preserve_order(links: list[str]) -> list[str]:
    seen = set()
    result = []
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def oldest_first(links: list[str]) -> list[str]:
    return list(reversed(links))


def collect_post_links(driver, profile_url: str) -> list[str]:
    driver.get(profile_url)
    time.sleep(config.SCROLL_PAUSE_SEC)

    collected: list[str] = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        elements = driver.find_elements(By.CSS_SELECTOR, config.POST_LINK_SELECTOR)
        for element in elements:
            href = element.get_attribute("href")
            if href:
                collected.append(href)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(config.SCROLL_PAUSE_SEC)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return oldest_first(dedupe_preserve_order(collected))
