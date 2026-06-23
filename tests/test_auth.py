from auth import classify_login_state


def test_classify_login_state_returns_pending_for_login_url():
    url = "https://www.instagram.com/accounts/login/"
    assert classify_login_state(url) == "pending"


def test_classify_login_state_returns_checkpoint_for_challenge_url():
    url = "https://www.instagram.com/challenge/12345/abcde/"
    assert classify_login_state(url) == "checkpoint"


def test_classify_login_state_returns_checkpoint_for_two_factor_url():
    url = "https://www.instagram.com/accounts/login/two_factor/"
    assert classify_login_state(url) == "checkpoint"


def test_classify_login_state_returns_success_for_profile_url():
    url = "https://www.instagram.com/daesung_techwin/"
    assert classify_login_state(url) == "success"
