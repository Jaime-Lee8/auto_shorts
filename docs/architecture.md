# GlobalNewsShortsRL 시스템 아키텍처

## 개요

GlobalNewsShortsRL은 YouTube에서 글로벌 이슈 관련 뉴스 영상을 자동으로 선별하고, 이를 한국어로 요약하여 쇼츠 콘텐츠로 제작하는 자동화 시스템입니다. 이 시스템은 Hook 멘트 생성, 자막 추출 및 번역, 영상 합성, 자동 업로드, 성과 분석, 그리고 강화학습 기반 피드백 루프를 통해 지속적으로 콘텐츠 품질을 개선합니다.

## 시스템 구성

GlobalNewsShortsRL은 다음과 같은 주요 모듈로 구성되어 있습니다:

1. **YouTube 데이터 수집 모듈** (`youtube_collector.py`)
   - YouTube Data API를 활용하여 인기 뉴스 채널의 최신 영상 검색
   - 트렌딩 이슈 자동 선별 알고리즘
   - 영상 메타데이터 수집 및 저장

2. **자막 추출 및 번역 모듈** (`transcript_processor.py`)
   - YouTube 자막 API를 통한 자막 추출
   - Whisper API를 활용한 음성-텍스트 변환
   - OpenAI API를 활용한 한국어 번역 및 요약

3. **콘텐츠 생성 모듈** (`content_generator.py`)
   - Hook 멘트 생성 및 스타일 적용
   - 핵심 요약 및 배경 설명 생성
   - 스크립트 템플릿 관리 및 최적화

4. **영상 제작 모듈** (`video_producer.py`)
   - ElevenLabs API를 활용한 TTS 오디오 생성
   - FFmpeg를 활용한 영상 합성 및 편집
   - 자막 삽입 및 쇼츠 형식 최적화

5. **업로드 및 분석 모듈** (`youtube_uploader.py`)
   - YouTube Upload API를 통한 자동 업로드
   - YouTube Analytics API를 통한 성과 지표 수집
   - 영상 성과 분석 및 리포트 생성

6. **피드백 및 강화학습 모듈** (`feedback_processor.py`)
   - ChatGPT 기반 피드백 생성
   - SQLite 데이터베이스를 통한 데이터 관리
   - 피드백 기반 템플릿 자동 수정
   - Notion API를 통한 주간 리포트 생성

## 데이터 흐름

1. YouTube 데이터 수집 모듈이 인기 뉴스 채널에서 트렌딩 영상을 선별하여 메타데이터를 저장합니다.
2. 자막 추출 및 번역 모듈이 선별된 영상의 자막을 추출하고 한국어로 번역합니다.
3. 콘텐츠 생성 모듈이 번역된 내용을 바탕으로 쇼츠용 스크립트를 생성합니다.
4. 영상 제작 모듈이 스크립트를 바탕으로 TTS 오디오를 생성하고 영상을 합성합니다.
5. 업로드 및 분석 모듈이 완성된 영상을 YouTube에 업로드하고 성과를 분석합니다.
6. 피드백 및 강화학습 모듈이 성과 데이터를 바탕으로 피드백을 생성하고 템플릿을 최적화합니다.

## 기술 스택

- **프로그래밍 언어**: Python 3.10+
- **API 서비스**:
  - YouTube Data API
  - YouTube Analytics API
  - OpenAI API (GPT-4o)
  - ElevenLabs API
  - Notion API (선택적)
- **라이브러리**:
  - google-api-python-client
  - youtube-transcript-api
  - openai
  - elevenlabs
  - ffmpeg-python
  - sqlite3
- **데이터 저장**: JSON 파일, SQLite 데이터베이스

## 시스템 요구사항

- Python 3.10 이상
- FFmpeg 설치
- 인터넷 연결
- 필요한 API 키 (YouTube, OpenAI, ElevenLabs)
- 최소 4GB RAM
- 최소 10GB 저장 공간

## 확장성 및 유지보수

GlobalNewsShortsRL은 모듈화된 구조로 설계되어 있어 각 모듈을 독립적으로 개선하거나 확장할 수 있습니다. 예를 들어:

- 새로운 뉴스 소스 추가
- 다른 언어로의 번역 지원
- 다양한 영상 스타일 템플릿 추가
- 추가 분석 지표 통합
- 다른 플랫폼(TikTok, Instagram Reels 등)으로 확장

## 보안 고려사항

- API 키는 환경 변수 또는 .env 파일을 통해 안전하게 관리
- OAuth 인증 토큰은 안전하게 저장
- 사용자 데이터 및 분석 정보는 로컬 데이터베이스에 저장
