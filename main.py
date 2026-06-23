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
