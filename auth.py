import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config

LOGIN_URL_MARKER = "/accounts/login"
CHECKPOINT_URL_MARKERS = ["/challenge", "two_factor"]


def classify_login_state(current_url: str) -> str:
    if any(marker in current_url for marker in CHECKPOINT_URL_MARKERS):
        return "checkpoint"
    if LOGIN_URL_MARKER in current_url:
        return "pending"
    return "success"


def login(driver, username: str, password: str) -> None:
    driver.get(config.LOGIN_URL)
    wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT_SEC)
    username_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, config.USERNAME_INPUT_SELECTOR))
    )
    password_input = driver.find_element(By.CSS_SELECTOR, config.PASSWORD_INPUT_SELECTOR)

    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)

    driver.find_element(By.CSS_SELECTOR, config.LOGIN_BUTTON_SELECTOR).click()


def wait_for_login(driver, timeout_sec: int, poll_interval_sec: int, on_checkpoint=None) -> bool:
    elapsed = 0
    checkpoint_notified = False
    while elapsed < timeout_sec:
        state = classify_login_state(driver.current_url)
        if state == "success":
            return True
        if state == "checkpoint" and not checkpoint_notified:
            checkpoint_notified = True
            if on_checkpoint:
                on_checkpoint()
        time.sleep(poll_interval_sec)
        elapsed += poll_interval_sec
    return False
