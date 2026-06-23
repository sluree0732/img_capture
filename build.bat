@echo off
pip install pyinstaller
pyinstaller --onefile --noconsole --name InstaCapture main.py
echo 빌드 완료: dist\InstaCapture.exe
