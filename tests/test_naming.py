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
