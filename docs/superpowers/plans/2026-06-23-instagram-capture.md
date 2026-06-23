# 인스타그램 게시물 캡처 도구 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인스타그램 프로필의 게시물(이미지 1장짜리)을 과거 → 최신 순서로 순회하며 게시물 영역만 스크린샷으로 캡처하여 `{접두어}_인스타_카드뉴스{NN}.png`로 저장하는 Tkinter GUI 도구를 만든다.

**Architecture:** 순수 로직(파일명 생성, 링크 정렬/중복제거, 로그인 상태 판별)과 Selenium 구동 로직(로그인, 스크롤 수집, 캡처)을 분리한다. 순수 로직은 TDD로 단위 테스트하고, 실제 브라우저 자동화 부분은 라이브 인스타그램에 의존하므로 단위 테스트 대상에서 제외하고 수동 스모크 테스트로 검증한다.

**Tech Stack:** Python 3, Selenium 4, webdriver-manager, Tkinter, pytest, PyInstaller

참고 설계 문서: `docs/superpowers/specs/2026-06-23-instagram-capture-design.md`

---

## 파일 구조

```
img_capture/
├── config.py          # 상수 (셀렉터, URL, 타임아웃, 파일명 패턴)
├── naming.py          # 파일명 생성/기존 파일 탐색 (순수 로직)
├── collector.py       # 링크 정렬/중복제거(순수) + 게시물 수집(Selenium)
├── auth.py            # 로그인 상태 판별(순수) + 로그인 자동화(Selenium)
├── capture.py         # 캡처 및 저장(Selenium)
├── main.py            # Tkinter GUI, 전체 오케스트레이션
├── requirements.txt
└── tests/
    ├── conftest.py
    ├── test_naming.py
    ├── test_collector.py
    └── test_auth.py
```

---

### Task 1: 프로젝트 초기 설정

**Files:**
- Create: `requirements.txt`
- Create: `tests/conftest.py`

- [ ] **Step 1: requirements.txt 작성**

```text
selenium>=4.18
webdriver-manager>=4.0
pytest>=8.0
```

- [ ] **Step 2: tests/conftest.py 작성 (루트 디렉터리를 import 경로에 추가)**

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 3: 의존성 설치**

Run: `pip install -r requirements.txt`
Expected: 설치 완료, 에러 없음

- [ ] **Step 4: 커밋 및 푸시**

```bash
git add requirements.txt tests/conftest.py
git commit -m "chore: 프로젝트 초기 설정 (의존성, 테스트 경로)"
git push origin main
```

---

### Task 2: naming.py — 파일명 생성 및 기존 파일 탐색 (TDD)

**Files:**
- Create: `naming.py`
- Test: `tests/test_naming.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_naming.py
import os

from naming import build_filename, find_existing_capture_files, has_existing_captures


def test_build_filename_pads_index_to_two_digits():
    assert build_filename("대성", 1) == "대성_인스타_카드뉴스01.png"


def test_build_filename_handles_double_digit_index():
    assert build_filename("대성", 12) == "대성_인스타_카드뉴스12.png"


def test_find_existing_capture_files_returns_matching_files(tmp_path):
    (tmp_path / "대성_인스타_카드뉴스01.png").write_text("x")
    (tmp_path / "대성_인스타_카드뉴스02.png").write_text("x")
    (tmp_path / "다른파일.png").write_text("x")

    result = find_existing_capture_files(str(tmp_path), "대성")

    assert sorted(result) == ["대성_인스타_카드뉴스01.png", "대성_인스타_카드뉴스02.png"]


def test_find_existing_capture_files_returns_empty_when_no_match(tmp_path):
    result = find_existing_capture_files(str(tmp_path), "대성")
    assert result == []


def test_has_existing_captures_true_when_files_present(tmp_path):
    (tmp_path / "대성_인스타_카드뉴스01.png").write_text("x")
    assert has_existing_captures(str(tmp_path), "대성") is True


def test_has_existing_captures_false_when_folder_empty(tmp_path):
    assert has_existing_captures(str(tmp_path), "대성") is False
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/test_naming.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'naming'`

- [ ] **Step 3: naming.py 구현**

```python
# naming.py
import glob
import os


def build_filename(prefix: str, index: int) -> str:
    return f"{prefix}_인스타_카드뉴스{index:02d}.png"


def find_existing_capture_files(folder: str, prefix: str) -> list[str]:
    pattern = os.path.join(folder, f"{prefix}_인스타_카드뉴스*.png")
    return [os.path.basename(path) for path in glob.glob(pattern)]


def has_existing_captures(folder: str, prefix: str) -> bool:
    return len(find_existing_capture_files(folder, prefix)) > 0
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/test_naming.py -v`
Expected: 6 passed

- [ ] **Step 5: 커밋 및 푸시**

```bash
git add naming.py tests/test_naming.py
git commit -m "feat: 캡처 파일명 생성 및 기존 파일 탐색 기능 추가"
git push origin main
```

---

### Task 3: collector.py — 링크 정렬/중복제거 순수 로직 (TDD)

**Files:**
- Create: `collector.py`
- Test: `tests/test_collector.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_collector.py
from collector import dedupe_preserve_order, oldest_first


def test_dedupe_preserve_order_removes_duplicates_keeps_first_order():
    links = ["a", "b", "a", "c", "b"]
    assert dedupe_preserve_order(links) == ["a", "b", "c"]


def test_dedupe_preserve_order_handles_empty_list():
    assert dedupe_preserve_order([]) == []


def test_oldest_first_reverses_list():
    links = ["newest", "middle", "oldest"]
    assert oldest_first(links) == ["oldest", "middle", "newest"]


def test_oldest_first_handles_empty_list():
    assert oldest_first([]) == []


def test_oldest_first_does_not_mutate_input():
    links = ["newest", "oldest"]
    oldest_first(links)
    assert links == ["newest", "oldest"]
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/test_collector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'collector'`

- [ ] **Step 3: collector.py에 순수 로직 함수 구현**

```python
# collector.py
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
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/test_collector.py -v`
Expected: 5 passed

- [ ] **Step 5: 커밋 및 푸시**

```bash
git add collector.py tests/test_collector.py
git commit -m "feat: 게시물 링크 중복제거 및 과거순 정렬 로직 추가"
git push origin main
```

---

### Task 4: auth.py — 로그인 상태 판별 순수 로직 (TDD)

**Files:**
- Create: `auth.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_auth.py
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
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/test_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: auth.py에 판별 함수 구현**

```python
# auth.py
LOGIN_URL_MARKER = "/accounts/login"
CHECKPOINT_URL_MARKERS = ["/challenge", "two_factor"]


def classify_login_state(current_url: str) -> str:
    if any(marker in current_url for marker in CHECKPOINT_URL_MARKERS):
        return "checkpoint"
    if LOGIN_URL_MARKER in current_url:
        return "pending"
    return "success"
```

주의: `two_factor` URL에 `/accounts/login`도 포함되어 있으므로, 체크포인트 검사를 로그인 검사보다 먼저 수행해야 한다 (순서가 바뀌면 Step 4 테스트가 실패한다).

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/test_auth.py -v`
Expected: 4 passed

- [ ] **Step 5: 커밋 및 푸시**

```bash
git add auth.py tests/test_auth.py
git commit -m "feat: URL 기반 로그인 상태(성공/대기/체크포인트) 판별 로직 추가"
git push origin main
```

---

### Task 5: config.py — 상수 정의

**Files:**
- Create: `config.py`

- [ ] **Step 1: config.py 작성**

```python
# config.py

LOGIN_URL = "https://www.instagram.com/accounts/login/"

USERNAME_INPUT_SELECTOR = "input[name='username']"
PASSWORD_INPUT_SELECTOR = "input[name='password']"
LOGIN_BUTTON_SELECTOR = "button[type='submit']"

POST_LINK_SELECTOR = "article a[href*='/p/']"
POST_DETAIL_PANEL_SELECTOR = "article"

PAGE_LOAD_TIMEOUT_SEC = 20
SCROLL_PAUSE_SEC = 2
LOGIN_POLL_INTERVAL_SEC = 2
LOGIN_POLL_TIMEOUT_SEC = 180
```

이 셀렉터들은 인스타그램 화면 구조가 바뀌면 깨질 수 있다. 실제 사이트에서 Task 6~8을 수동 검증할 때 개발자도구로 실제 셀렉터를 확인하고, 다르면 이 파일의 값만 수정하면 된다.

- [ ] **Step 2: 커밋 및 푸시**

```bash
git add config.py
git commit -m "feat: 셀렉터/URL/타임아웃 상수 정의"
git push origin main
```

---

### Task 6: auth.py — 로그인 자동화 (Selenium)

이 작업은 실제 인스타그램 로그인 페이지에 의존하므로 자동화된 테스트 대상이 아니다. 구현 후 수동 스모크 테스트로 검증한다.

**Files:**
- Modify: `auth.py`

- [ ] **Step 1: 로그인 입력/제출 함수 추가**

```python
# auth.py 에 추가
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


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
```

- [ ] **Step 2: 수동 스모크 테스트**

다음 스크립트를 임시로 작성해 직접 실행하며 확인한다 (확인 후 삭제, 커밋하지 않음):

```python
# manual_smoke_login.py (임시, 커밋 금지)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import auth

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
auth.login(driver, "테스트계정아이디", "테스트계정비밀번호")
success = auth.wait_for_login(
    driver,
    timeout_sec=180,
    poll_interval_sec=2,
    on_checkpoint=lambda: print("2FA/캡차 화면 감지 — 브라우저에서 직접 처리해주세요"),
)
print("로그인 성공 여부:", success)
input("확인 후 Enter를 누르면 브라우저를 닫습니다...")
driver.quit()
```

Run: `python manual_smoke_login.py`
Expected: 브라우저가 열리고, ID/PW가 자동 입력되어 로그인이 시도됨. 2FA/캡차가 뜨면 콘솔에 안내 문구가 출력되고 자동화가 멈춰 있다가, 직접 처리하면 "로그인 성공 여부: True"가 출력됨.

- [ ] **Step 3: 임시 스모크 테스트 파일 삭제**

Run: `rm manual_smoke_login.py`

- [ ] **Step 4: 커밋 및 푸시**

```bash
git add auth.py
git commit -m "feat: Selenium 기반 로그인 자동 입력 및 로그인 완료 대기 로직 추가"
git push origin main
```

---

### Task 7: collector.py — 게시물 링크 수집 (Selenium)

실제 인스타그램 프로필 페이지에 의존하므로 자동화된 테스트 대상이 아니다. 수동 스모크 테스트로 검증한다.

**Files:**
- Modify: `collector.py`

- [ ] **Step 1: 스크롤 수집 함수 추가**

```python
# collector.py 에 추가
import time

from selenium.webdriver.common.by import By

import config


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
```

- [ ] **Step 2: 수동 스모크 테스트**

Task 6에서 로그인까지 마친 `driver`를 이어서 사용:

```python
# 위 manual_smoke_login.py 에 이어서 (임시로 추가, 커밋 금지)
import collector

links = collector.collect_post_links(driver, "https://www.instagram.com/daesung_techwin/")
print(f"수집된 게시물 수: {len(links)}")
print("첫 번째(가장 오래된) 링크:", links[0] if links else None)
print("마지막(가장 최신) 링크:", links[-1] if links else None)
```

Expected: 실제 프로필의 게시물 수와 비슷한 개수가 출력되고, 마지막 링크가 가장 최근에 올린 게시물과 일치함.

- [ ] **Step 3: 커밋 및 푸시**

```bash
git add collector.py
git commit -m "feat: 프로필 스크롤하며 게시물 링크 수집 후 과거순 정렬"
git push origin main
```

---

### Task 8: capture.py — 게시물 캡처 및 저장 (Selenium)

실제 게시물 화면에 의존하므로 자동화된 테스트 대상이 아니다. 수동 스모크 테스트로 검증한다.

**Files:**
- Create: `capture.py`

- [ ] **Step 1: capture.py 구현**

```python
# capture.py
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
    panel.screenshot(os.path.join(save_path, filename))


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
```

- [ ] **Step 2: 수동 스모크 테스트**

Task 7의 `links`를 이어서 사용:

```python
import capture

saved = capture.capture_all_posts(
    driver,
    links[:2],  # 전체 실행 전 2개만 먼저 확인
    save_path="C:/temp/insta_test",
    prefix="테스트",
    on_progress=lambda i, t: print(f"{i}/{t} 캡처 완료"),
)
print("저장된 파일:", saved)
```

Expected: `C:/temp/insta_test` 폴더에 `테스트_인스타_카드뉴스01.png`, `테스트_인스타_카드뉴스02.png`가 생성되고, 열어보면 게시물 이미지+본문이 잘려서 보임.

- [ ] **Step 3: 커밋 및 푸시**

```bash
git add capture.py
git commit -m "feat: 게시물 영역 스크린샷 캡처 및 순차 파일 저장 추가"
git push origin main
```

---

### Task 9: main.py — Tkinter GUI 및 전체 오케스트레이션

GUI 전체 흐름은 실제 환경에서 수동으로 실행해 확인한다.

**Files:**
- Create: `main.py`

- [ ] **Step 1: main.py 구현**

```python
# main.py
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import auth
import capture
import collector
import config
import naming


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("인스타그램 게시물 캡처")
        self.geometry("480x420")

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.save_path_var = tk.StringVar()
        self.prefix_var = tk.StringVar()
        self.status_var = tk.StringVar(value="대기 중")

        self._build_widgets()

    def _build_widgets(self):
        tk.Label(self, text="아이디").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(self, textvariable=self.username_var, width=50).pack(padx=10)

        tk.Label(self, text="비밀번호").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(self, textvariable=self.password_var, show="*", width=50).pack(padx=10)

        tk.Label(self, text="게시물(프로필) URL").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(self, textvariable=self.url_var, width=50).pack(padx=10)

        tk.Label(self, text="저장 경로").pack(anchor="w", padx=10, pady=(10, 0))
        path_frame = tk.Frame(self)
        path_frame.pack(padx=10, fill="x")
        tk.Entry(path_frame, textvariable=self.save_path_var, width=40).pack(side="left")
        tk.Button(path_frame, text="찾아보기", command=self._choose_folder).pack(side="left", padx=5)

        tk.Label(self, text="파일명 접두어").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(self, textvariable=self.prefix_var, width=50).pack(padx=10)

        tk.Button(self, text="실행하기", command=self._on_run_clicked).pack(pady=15)

        tk.Label(self, textvariable=self.status_var, wraplength=440, justify="left").pack(
            padx=10, anchor="w"
        )

    def _choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path_var.set(folder)

    def _on_run_clicked(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        url = self.url_var.get().strip()
        save_path = self.save_path_var.get().strip()
        prefix = self.prefix_var.get().strip()

        if not all([username, password, url, save_path, prefix]):
            messagebox.showerror("입력 오류", "모든 항목을 입력해주세요.")
            return

        if naming.has_existing_captures(save_path, prefix):
            proceed = messagebox.askyesno(
                "기존 파일 발견",
                "이미 캡처된 파일이 있습니다. 계속하면 덮어씁니다. 진행하시겠습니까?",
            )
            if not proceed:
                return

        threading.Thread(
            target=self._run_pipeline,
            args=(username, password, url, save_path, prefix),
            daemon=True,
        ).start()

    def _set_status(self, text: str):
        self.status_var.set(text)

    def _run_pipeline(self, username, password, url, save_path, prefix):
        driver = None
        try:
            self._set_status("Chrome 실행 중...")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

            self._set_status("로그인 시도 중...")
            auth.login(driver, username, password)

            success = auth.wait_for_login(
                driver,
                timeout_sec=config.LOGIN_POLL_TIMEOUT_SEC,
                poll_interval_sec=config.LOGIN_POLL_INTERVAL_SEC,
                on_checkpoint=lambda: self._set_status(
                    "사용자 확인이 필요합니다. 브라우저에서 직접 처리해주세요."
                ),
            )
            if not success:
                self._set_status("로그인 실패 (시간 초과). 작업을 중단합니다.")
                return

            self._set_status("게시물 목록 수집 중...")
            links = collector.collect_post_links(driver, url)

            self._set_status(f"캡처 시작 (총 {len(links)}개)")
            saved = capture.capture_all_posts(
                driver,
                links,
                save_path,
                prefix,
                on_progress=lambda i, t: self._set_status(f"{i}/{t} 캡처 중..."),
            )

            self._set_status(f"완료, {len(saved)}개 캡처됨")
        except Exception as exc:
            self._set_status(f"오류 발생: {exc}")
        finally:
            if driver:
                driver.quit()


if __name__ == "__main__":
    App().mainloop()
```

- [ ] **Step 2: 수동 통합 테스트**

Run: `python main.py`
Expected: GUI 창이 뜨고, 모든 필드 입력 후 [실행하기] 클릭 시 Chrome이 열려 로그인 → 게시물 수집 → 순차 캡처가 진행되며 상태 라벨이 단계별로 갱신됨. 완료 후 지정한 저장 경로에 `{접두어}_인스타_카드뉴스01.png`부터 순서대로 파일이 생성됨.

- [ ] **Step 3: 커밋 및 푸시**

```bash
git add main.py
git commit -m "feat: Tkinter GUI 및 로그인-수집-캡처 전체 파이프라인 연결"
git push origin main
```

---

### Task 10: PyInstaller 패키징

**Files:**
- Create: `build.bat`

- [ ] **Step 1: 빌드 스크립트 작성**

```bat
@echo off
pip install pyinstaller
pyinstaller --onefile --noconsole --name InstaCapture main.py
echo 빌드 완료: dist\InstaCapture.exe
```

- [ ] **Step 2: 빌드 실행**

Run: `build.bat`
Expected: `dist/InstaCapture.exe` 생성됨, 에러 없음

- [ ] **Step 3: exe 실행 확인**

Run: `dist\InstaCapture.exe` 더블클릭 실행
Expected: GUI가 정상적으로 뜨고 Task 9의 통합 테스트와 동일하게 동작함

- [ ] **Step 4: 커밋 및 푸시**

```bash
git add build.bat
git commit -m "chore: PyInstaller 빌드 스크립트 추가"
git push origin main
```

---

## Self-Review 결과

- **스펙 커버리지**: 설계 문서의 로그인/수집/캡처/덮어쓰기 확인/파일명 규칙/예외처리/GUI/exe 패키징 항목 모두 Task 1~10에 매핑됨.
- **타입/시그니처 일관성**: `naming.build_filename(prefix, index)`, `collector.collect_post_links(driver, profile_url)`, `auth.login(driver, username, password)`, `auth.wait_for_login(driver, timeout_sec, poll_interval_sec, on_checkpoint)`, `capture.capture_all_posts(driver, post_links, save_path, prefix, on_progress)` — Task 6~9에서 동일한 이름/인자 순서로 일관되게 사용됨.
- **플레이스홀더 없음**: 모든 단계에 실행 가능한 실제 코드/명령어 포함.
