import glob
import os


def build_filename(prefix: str, index: int) -> str:
    return f"{prefix}_인스타_카드뉴스{index:02d}.png"


def find_existing_capture_files(folder: str, prefix: str) -> list[str]:
    pattern = os.path.join(folder, f"{glob.escape(prefix)}_인스타_카드뉴스*.png")
    return [os.path.basename(path) for path in glob.glob(pattern)]


def has_existing_captures(folder: str, prefix: str) -> bool:
    return len(find_existing_capture_files(folder, prefix)) > 0
