# GlobalNewsShortsRL 설치 및 설정 가이드

이 가이드는 GlobalNewsShortsRL 시스템을 설치하고 설정하는 방법을 안내합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [설치 방법](#설치-방법)
3. [API 키 설정](#api-키-설정)
4. [기본 설정](#기본-설정)
5. [실행 방법](#실행-방법)
6. [스케줄링 설정](#스케줄링-설정)

## 사전 요구사항

GlobalNewsShortsRL을 사용하기 위해서는 다음과 같은 사전 요구사항이 필요합니다:

- Python 3.10 이상
- FFmpeg 설치
- 인터넷 연결
- 다음 API 서비스 계정 및 키:
  - Google Cloud Platform 계정 (YouTube API 사용)
  - OpenAI API 키
  - ElevenLabs API 키
  - Notion API 키 (선택적)

## 설치 방법

### 1. 저장소 복제

```bash
git clone https://github.com/yourusername/GlobalNewsShortsRL.git
cd GlobalNewsShortsRL
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. FFmpeg 설치

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS (Homebrew)

```bash
brew install ffmpeg
```

#### Windows

1. [FFmpeg 공식 웹사이트](https://ffmpeg.org/download.html)에서 Windows 버전 다운로드
2. 압축 해제 후 시스템 환경 변수 PATH에 FFmpeg 실행 파일 경로 추가

## API 키 설정

### 1. .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 API 키를 설정합니다:

```
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
```

### 2. YouTube API 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. YouTube Data API v3 및 YouTube Analytics API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. 생성된 클라이언트 ID 정보를 `credentials.json` 파일로 다운로드하여 `data` 디렉토리에 저장

## 기본 설정

`config/config.py` 파일에서 다음 설정을 필요에 따라 수정할 수 있습니다:

### 1. 뉴스 채널 설정

```python
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
```

### 2. 검색 설정

```python
MAX_RESULTS = 10  # 채널당 검색할 최대 영상 수
VIDEO_PUBLISHED_AFTER = '1day'  # 1일 이내 업로드된 영상만 검색
MIN_VIEW_COUNT = 5000  # 최소 조회수
```

### 3. 콘텐츠 설정

```python
MAX_VIDEO_DURATION = 60  # 초 단위, 원본 영상 최대 길이
SHORTS_DURATION = 30  # 초 단위, 최종 쇼츠 영상 길이
```

### 4. 업로드 설정

```python
UPLOAD_SCHEDULE = {
    'morning': '10:00',
    'afternoon': '16:00'
}
```

## 실행 방법

### 1. 전체 파이프라인 실행

```bash
python main.py
```

### 2. 개별 모듈 실행

각 모듈을 개별적으로 테스트하거나 실행할 수 있습니다:

```bash
# YouTube 데이터 수집
python src/youtube_collector.py

# 자막 추출 및 번역
python src/transcript_processor.py

# 콘텐츠 생성
python src/content_generator.py

# 영상 제작
python src/video_producer.py

# YouTube 업로드 및 분석
python src/youtube_uploader.py

# 피드백 처리
python src/feedback_processor.py
```

## 스케줄링 설정

### Linux/macOS (Cron)

다음과 같이 crontab을 설정하여 하루에 두 번(오전 10시, 오후 4시) 자동으로 실행되도록 할 수 있습니다:

```bash
crontab -e
```

다음 내용 추가:

```
0 10 * * * cd /path/to/GlobalNewsShortsRL && /path/to/python main.py
0 16 * * * cd /path/to/GlobalNewsShortsRL && /path/to/python main.py
```

### Windows (작업 스케줄러)

1. 작업 스케줄러 열기
2. '기본 작업 만들기' 선택
3. 이름 및 설명 입력
4. '매일' 선택하고 시간 설정 (오전 10시, 오후 4시)
5. '프로그램 시작' 선택
6. 프로그램/스크립트: `python.exe` 경로 입력
7. 인수 추가: `main.py`
8. 시작 위치: GlobalNewsShortsRL 디렉토리 경로 입력
