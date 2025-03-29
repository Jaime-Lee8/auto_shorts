"""
GlobalNewsShortsRL 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 설정
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')

# YouTube 설정
YOUTUBE_NEWS_CHANNELS = [
    'CNN',
    'BBCNews',
    'BloombergTV',
    'AlJazeeraEnglish',
    'SkyNews',
    'ABCNews',
    'CBSNews',
    'NBCNews',
    'FoxNews',
    'Reuters'
]

# 검색 설정
MAX_RESULTS = 10  # 채널당 검색할 최대 영상 수
VIDEO_PUBLISHED_AFTER = '1day'  # 1일 이내 업로드된 영상만 검색
MIN_VIEW_COUNT = 5000  # 최소 조회수

# 콘텐츠 설정
MAX_VIDEO_DURATION = 60  # 초 단위, 원본 영상 최대 길이
SHORTS_DURATION = 30  # 초 단위, 최종 쇼츠 영상 길이

# 업로드 설정
UPLOAD_SCHEDULE = {
    'morning': '10:00',
    'afternoon': '16:00'
}

# 데이터 저장 경로
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
TEMP_DIR = os.path.join(DATA_DIR, 'temp')

# 로그 설정
LOG_LEVEL = 'INFO'
