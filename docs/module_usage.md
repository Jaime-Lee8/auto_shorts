# GlobalNewsShortsRL 모듈 사용 설명서

이 문서는 GlobalNewsShortsRL 시스템의 각 모듈 사용 방법을 설명합니다.

## 목차

1. [YouTube 데이터 수집 모듈](#youtube-데이터-수집-모듈)
2. [자막 추출 및 번역 모듈](#자막-추출-및-번역-모듈)
3. [콘텐츠 생성 모듈](#콘텐츠-생성-모듈)
4. [영상 제작 모듈](#영상-제작-모듈)
5. [업로드 및 분석 모듈](#업로드-및-분석-모듈)
6. [피드백 및 강화학습 모듈](#피드백-및-강화학습-모듈)
7. [통합 실행](#통합-실행)

## YouTube 데이터 수집 모듈

`youtube_collector.py` 모듈은 YouTube Data API를 사용하여 인기 뉴스 채널의 최신 영상을 검색하고 트렌딩 이슈를 자동으로 선별합니다.

### 주요 기능

- 인기 뉴스 채널 검색
- 최신 영상 필터링
- 트렌딩 이슈 자동 선별
- 영상 메타데이터 저장

### 사용 예시

```python
from src.youtube_collector import YouTubeCollector

# 인스턴스 생성
collector = YouTubeCollector()

# 트렌딩 뉴스 영상 수집
trending_videos = collector.collect_trending_news()

# 특정 채널의 최근 영상 가져오기
channel_id = collector.get_channel_id('CNN')
videos = collector.get_recent_videos(channel_id)

# 뉴스 영상 필터링
news_videos = collector.filter_news_videos(videos)

# 영상 상세 정보 가져오기
video_details = collector.get_video_details('video_id')
```

### 설정 옵션

`config/config.py` 파일에서 다음 설정을 조정할 수 있습니다:

- `YOUTUBE_NEWS_CHANNELS`: 검색할 뉴스 채널 목록
- `MAX_RESULTS`: 채널당 검색할 최대 영상 수
- `VIDEO_PUBLISHED_AFTER`: 영상 업로드 기간 필터
- `MIN_VIEW_COUNT`: 최소 조회수 필터

## 자막 추출 및 번역 모듈

`transcript_processor.py` 모듈은 YouTube 영상의 자막을 추출하고, 필요한 경우 Whisper API를 사용하여 음성을 텍스트로 변환한 후 한국어로 번역합니다.

### 주요 기능

- YouTube 자막 추출
- Whisper API를 통한 음성-텍스트 변환
- OpenAI API를 통한 한국어 번역
- 내용 요약

### 사용 예시

```python
from src.transcript_processor import TranscriptProcessor

# 인스턴스 생성
processor = TranscriptProcessor()

# YouTube 자막 추출
transcript = processor.get_youtube_transcript('video_id')

# 오디오 다운로드 및 Whisper API 변환
audio_file = processor.download_audio('video_id')
transcript = processor.transcribe_audio_with_whisper(audio_file)

# 한국어 번역
translated_text = processor.translate_to_korean(transcript)

# 내용 요약
summary = processor.summarize_content(translated_text)

# 전체 처리 과정
result = processor.process_video('video_id')
```

## 콘텐츠 생성 모듈

`content_generator.py` 모듈은 추출된 자막과 번역된 내용을 바탕으로 쇼츠 콘텐츠에 최적화된 스크립트를 생성합니다.

### 주요 기능

- Hook 멘트 생성 및 강화
- 스크립트 템플릿 관리
- 쇼츠용 스크립트 최적화
- 제목 및 태그 생성

### 사용 예시

```python
from src.content_generator import ContentGenerator

# 인스턴스 생성
generator = ContentGenerator()

# 스크립트 생성
script = generator.generate_script(video_data, transcript_data)

# 스크립트 최적화
optimized_script = generator.optimize_script_for_shorts(script)

# 제목 및 태그 생성
title_and_tags = generator.generate_title_and_tags(optimized_script)

# Hook 멘트 강화
enhanced_hook = generator.enhance_hook(hook_text, style='question')
```

### 템플릿 관리

템플릿은 `data/templates.json` 파일에 저장되며, 다음과 같은 구조를 가집니다:

```json
{
  "hook": {
    "question": "{}?",
    "warning": "주의하세요! {}",
    "shocking": "충격! {}",
    "interesting": "놀라운 사실! {}"
  },
  "transition": [
    "자세히 알아보겠습니다.",
    "지금 바로 알려드립니다.",
    "함께 살펴보겠습니다.",
    "이것이 전체 내용입니다."
  ],
  "ending": [
    "이상 글로벌 뉴스 단신이었습니다.",
    "더 자세한 내용은 링크를 참고하세요.",
    "구독과 좋아요 부탁드립니다.",
    "다음 소식에서 다시 만나요."
  ]
}
```

## 영상 제작 모듈

`video_producer.py` 모듈은 ElevenLabs API를 사용하여 TTS 오디오를 생성하고, FFmpeg를 사용하여 영상을 합성합니다.

### 주요 기능

- ElevenLabs API를 통한 TTS 오디오 생성
- YouTube 영상 다운로드
- 자막 파일 생성
- FFmpeg를 통한 영상 합성
- 미리보기 이미지 생성

### 사용 예시

```python
from src.video_producer import VideoProducer

# 인스턴스 생성
producer = VideoProducer()

# TTS 오디오 생성
audio_path = producer.generate_tts_audio("안녕하세요, 오늘의 글로벌 뉴스입니다.")

# 영상 다운로드
video_path = producer.download_video('video_id')

# 자막 파일 생성
subtitle_path = producer.create_subtitle_file(script, 'subtitle.srt')

# 쇼츠 영상 제작
output_path = producer.create_shorts_video(script, 'video_id')

# 미리보기 이미지 생성
preview_path = producer.create_preview_image(output_path)
```

## 업로드 및 분석 모듈

`youtube_uploader.py` 모듈은 YouTube Upload API를 사용하여 영상을 업로드하고, YouTube Analytics API를 사용하여 성과를 분석합니다.

### 주요 기능

- YouTube API 인증
- 영상 업로드
- 성과 지표 수집
- 댓글 수집
- 성과 분석

### 사용 예시

```python
from src.youtube_uploader import YouTubeUploader

# 인스턴스 생성
uploader = YouTubeUploader()

# YouTube API 인증
uploader.authenticate()

# 영상 업로드
video_id = uploader.upload_video(
    video_path='output.mp4',
    title='글로벌 뉴스: 경제 위기 경고',
    description='미국 연방준비제도이사회의 금리 인상 결정과 그 영향에 대해 알아봅니다.',
    tags=['글로벌뉴스', '경제위기', '금리인상']
)

# 성과 지표 수집
analytics_data = uploader.get_video_analytics(
    video_id,
    start_date='2025-03-22',
    end_date='2025-03-29'
)

# 댓글 수집
comments = uploader.get_video_comments(video_id)

# 성과 분석
analysis = uploader.analyze_performance(video_id)
```

## 피드백 및 강화학습 모듈

`feedback_processor.py` 모듈은 수집된 성과 데이터를 바탕으로 ChatGPT 기반 피드백을 생성하고, 템플릿을 자동으로 최적화합니다.

### 주요 기능

- 영상 메타데이터 저장
- 성과 데이터 저장
- ChatGPT 기반 피드백 생성
- 템플릿 자동 최적화
- 주간 리포트 생성
- Notion API 연동

### 사용 예시

```python
from src.feedback_processor import FeedbackProcessor

# 인스턴스 생성
processor = FeedbackProcessor()

# 영상 메타데이터 저장
processor.store_video_metadata(video_id, title, script)

# 성과 데이터 저장
processor.store_performance_data(video_id, analytics_data)

# 피드백 생성
feedback = processor.generate_feedback(video_id, analytics_data, comments_data)

# 템플릿 업데이트
updated_templates = processor.update_templates_based_on_feedback([feedback1, feedback2, feedback3])

# 주간 리포트 생성
report_file = processor.generate_weekly_report()

# Notion 리포트 생성
notion_url = processor.create_notion_report(report_file, notion_api_key, database_id)
```

## 통합 실행

`main.py` 스크립트를 사용하여 전체 파이프라인을 실행할 수 있습니다:

```python
import os
import logging
from datetime import datetime
from src.youtube_collector import YouTubeCollector
from src.transcript_processor import TranscriptProcessor
from src.content_generator import ContentGenerator
from src.video_producer import VideoProducer
from src.youtube_uploader import YouTubeUploader
from src.feedback_processor import FeedbackProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 1. YouTube 데이터 수집
    collector = YouTubeCollector()
    trending_videos = collector.collect_trending_news()
    
    if not trending_videos:
        logger.error("트렌딩 뉴스 영상을 찾을 수 없습니다.")
        return
    
    # 최고 트렌딩 영상 선택
    top_video = trending_videos[0]
    video_id = top_video['id']
    
    # 2. 자막 추출 및 번역
    processor = TranscriptProcessor()
    transcript_data = processor.process_video(video_id)
    
    if not transcript_data:
        logger.error(f"자막 처리 실패: {video_id}")
        return
    
    # 3. 콘텐츠 생성
    generator = ContentGenerator()
    script = generator.generate_script(top_video, transcript_data)
    
    if not script:
        logger.error(f"스크립트 생성 실패: {video_id}")
        return
    
    # 스크립트 최적화
    optimized_script = generator.optimize_script_for_shorts(script)
    
    # 제목 및 태그 생성
    title_and_tags = generator.generate_title_and_tags(optimized_script)
    
    # 4. 영상 제작
    producer = VideoProducer()
    output_path = producer.create_shorts_video(optimized_script, video_id)
    
    if not output_path:
        logger.error(f"영상 제작 실패: {video_id}")
        return
    
    # 5. YouTube 업로드
    uploader = YouTubeUploader()
    
    if not uploader.authenticate():
        logger.error("YouTube API 인증 실패")
        return
    
    uploaded_video_id = uploader.upload_video(
        video_path=output_path,
        title=title_and_tags['title'],
        description=f"원본 영상: https://www.youtube.com/watch?v={video_id}\n\n{optimized_script['summary']}",
        tags=title_and_tags['tags']
    )
    
    if not uploaded_video_id:
        logger.error(f"영상 업로드 실패: {video_id}")
        return
    
    logger.info(f"영상 업로드 성공: {uploaded_video_id}")
    
    # 6. 피드백 처리 (24시간 후 실행 필요)
    logger.info("24시간 후 다음 명령을 실행하여 성과 분석 및 피드백을 생성하세요:")
    logger.info(f"python analyze_performance.py {uploaded_video_id}")

if __name__ == "__main__":
    main()
```

성과 분석 및 피드백 생성을 위한 `analyze_performance.py` 스크립트:

```python
import sys
import logging
from src.youtube_uploader import YouTubeUploader
from src.feedback_processor import FeedbackProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_performance(video_id):
    # 업로더 인스턴스 생성
    uploader = YouTubeUploader()
    
    if not uploader.authenticate():
        logger.error("YouTube API 인증 실패")
        return
    
    # 성과 분석
    analytics_data = uploader.analyze_performance(video_id)
    
    if not analytics_data:
        logger.error(f"성과 분석 실패: {video_id}")
        return
    
    # 댓글 수집
    comments_data = {"comments": uploader.get_video_comments(video_id)}
    
    # 피드백 처리
    processor = FeedbackProcessor()
    feedback = processor.generate_feedback(video_id, analytics_data, comments_data)
    
    if feedback:
        logger.info(f"피드백 생성 완료: {video_id}")
        logger.info(f"종합 점수: {feedback.get('overall_score')}/10")
    else:
        logger.error(f"피드백 생성 실패: {video_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python analyze_performance.py VIDEO_ID")
        sys.exit(1)
    
    video_id = sys.argv[1]
    analyze_performance(video_id)
```
