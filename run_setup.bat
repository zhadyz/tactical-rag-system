@echo off
REM Force UTF-8 encoding for Python scripts with emojis
chcp 65001 > nul
python setup.py
