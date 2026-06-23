import logging
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
import naming


def capture_post(driver, post_url: str, save_path: str, filename: str) -> None:
    driver.get(post_url)
    wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT_SEC)
    panel = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, config.POST_DETAIL_PANEL_SELECTOR))
    )
    time.sleep(1)
    full_path = os.path.join(save_path, filename)
    if not panel.screenshot(full_path):
        raise RuntimeError(f"스크린샷 저장 실패: {full_path}")


def capture_all_posts(driver, post_links, save_path, prefix, on_progress=None) -> list[str]:
    saved_files: list[str] = []
    total = len(post_links)

    for index, post_url in enumerate(post_links, start=1):
        filename = naming.build_filename(prefix, index)
        try:
            capture_post(driver, post_url, save_path, filename)
            saved_files.append(filename)
        except Exception:
            logging.exception("게시물 캡처 실패: %s", post_url)

        if on_progress:
            on_progress(index, total)

    return saved_files
