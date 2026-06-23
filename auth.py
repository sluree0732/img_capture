LOGIN_URL_MARKER = "/accounts/login"
CHECKPOINT_URL_MARKERS = ["/challenge", "two_factor"]


def classify_login_state(current_url: str) -> str:
    if any(marker in current_url for marker in CHECKPOINT_URL_MARKERS):
        return "checkpoint"
    if LOGIN_URL_MARKER in current_url:
        return "pending"
    return "success"
