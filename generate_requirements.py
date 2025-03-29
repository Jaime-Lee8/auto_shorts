#!/usr/bin/env python3
"""
requirements.txt 생성 스크립트
"""
import os
import sys

# 필요한 패키지 목록
packages = [
    "google-api-python-client",
    "google-auth",
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "youtube-transcript-api",
    "openai",
    "elevenlabs",
    "ffmpeg-python",
    "python-dotenv",
    "requests",
    "tqdm",
    "numpy",
    "pandas"
]

# requirements.txt 파일 생성
with open('requirements.txt', 'w') as f:
    for package in packages:
        f.write(f"{package}\n")

print("requirements.txt 파일이 생성되었습니다.")
