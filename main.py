#!/usr/bin/env python3
"""
GlobalNewsShortsRL 메인 실행 스크립트
- 전체 파이프라인을 실행하여 글로벌 뉴스 쇼츠 콘텐츠를 자동으로 생성하고 업로드합니다.
"""
import os
import sys
import logging
import argparse
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 모듈 임포트
from src.youtube_collector import YouTubeCollector
from src.transcript_processor import TranscriptProcessor
from src.content_generator import ContentGenerator
from src.video_producer import VideoProducer
from src.youtube_uploader import YouTubeUploader
from src.feedback_processor import FeedbackProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'main_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='GlobalNewsShortsRL - 글로벌 뉴스 쇼츠 자동 생성 시스템')
    parser.add_argument('--collect-only', action='store_true', help='뉴스 수집만 실행')
    parser.add_argument('--process-only', action='store_true', help='자막 처리만 실행')
    parser.add_argument('--generate-only', action='store_true', help='콘텐츠 생성만 실행')
    parser.add_argument('--produce-only', action='store_true', help='영상 제작만 실행')
    parser.add_argument('--upload-only', action='store_true', help='업로드만 실행')
    parser.add_argument('--analyze', action='store_true', help='성과 분석 및 피드백 생성 실행')
    parser.add_argument('--video-id', type=str, help='처리할 특정 영상 ID')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    return parser.parse_args()

def main():
    """메인 실행 함수"""
    # 명령줄 인수 파싱
    args = parse_arguments()
    
    # 디버그 모드 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("디버그 모드 활성화")
    
    # 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    os.makedirs(os.path.join('data', 'videos'), exist_ok=True)
    os.makedirs(os.path.join('data', 'transcripts'), exist_ok=True)
    os.makedirs(os.path.join('data', 'scripts'), exist_ok=True)
    os.makedirs(os.path.join('data', 'output'), exist_ok=True)
    os.makedirs(os.path.join('data', 'analytics'), exist_ok=True)
    os.makedirs(os.path.join('data', 'feedback'), exist_ok=True)
    os.makedirs(os.path.join('data', 'reports'), exist_ok=True)
    
    # 성과 분석 및 피드백 생성 모드
    if args.analyze:
        if not args.video_id:
            logger.error("성과 분석을 위해 --video-id 인수가 필요합니다.")
            return
        
        logger.info(f"영상 ID {args.video_id}에 대한 성과 분석 및 피드백 생성 시작")
        
        # 업로더 인스턴스 생성
        uploader = YouTubeUploader()
        
        if not uploader.authenticate():
            logger.error("YouTube API 인증 실패")
            return
        
        # 성과 분석
        analytics_data = uploader.analyze_performance(args.video_id)
        
        if not analytics_data:
            logger.error(f"성과 분석 실패: {args.video_id}")
            return
        
        # 댓글 수집
        comments_data = {"comments": uploader.get_video_comments(args.video_id)}
        
        # 피드백 처리
        processor = FeedbackProcessor()
        feedback = processor.generate_feedback(args.video_id, analytics_data, comments_data)
        
        if feedback:
            logger.info(f"피드백 생성 완료: {args.video_id}")
            logger.info(f"종합 점수: {feedback.get('overall_score')}/10")
            
            # 템플릿 업데이트 (여러 피드백이 있을 경우)
            processor.update_templates_based_on_feedback([feedback])
        else:
            logger.error(f"피드백 생성 실패: {args.video_id}")
        
        return
    
    # 1. YouTube 데이터 수집
    if not args.process_only and not args.generate_only and not args.produce_only and not args.upload_only:
        logger.info("YouTube 데이터 수집 시작")
        collector = YouTubeCollector()
        trending_videos = collector.collect_trending_news()
        
        if not trending_videos:
            logger.error("트렌딩 뉴스 영상을 찾을 수 없습니다.")
            return
        
        # 최고 트렌딩 영상 선택
        top_video = trending_videos[0]
        video_id = top_video['id']
        logger.info(f"선택된 트렌딩 영상: {video_id} - {top_video['snippet']['title']}")
        
        if args.collect_only:
            logger.info("뉴스 수집 완료")
            return
    else:
        # 특정 영상 ID 사용
        video_id = args.video_id
        if not video_id:
            logger.error("처리할 영상 ID가 필요합니다. --video-id 인수를 사용하세요.")
            return
        
        # 영상 정보 가져오기
        collector = YouTubeCollector()
        top_video = collector.get_video_details(video_id)
        
        if not top_video:
            logger.error(f"영상 정보를 가져올 수 없습니다: {video_id}")
            return
    
    # 2. 자막 추출 및 번역
    if not args.generate_only and not args.produce_only and not args.upload_only:
        logger.info(f"자막 추출 및 번역 시작: {video_id}")
        processor = TranscriptProcessor()
        transcript_data = processor.process_video(video_id)
        
        if not transcript_data:
            logger.error(f"자막 처리 실패: {video_id}")
            return
        
        logger.info(f"자막 추출 및 번역 완료: {video_id}")
        
        if args.process_only:
            return
    else:
        # 저장된 자막 데이터 로드
        transcript_file = os.path.join('data', 'transcripts', f"{video_id}.json")
        
        if not os.path.exists(transcript_file):
            logger.error(f"자막 파일을 찾을 수 없습니다: {transcript_file}")
            return
        
        import json
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    
    # 3. 콘텐츠 생성
    if not args.produce_only and not args.upload_only:
        logger.info(f"콘텐츠 생성 시작: {video_id}")
        generator = ContentGenerator()
        script = generator.generate_script(top_video, transcript_data)
        
        if not script:
            logger.error(f"스크립트 생성 실패: {video_id}")
            return
        
        # 스크립트 최적화
        optimized_script = generator.optimize_script_for_shorts(script)
        
        # 제목 및 태그 생성
        title_and_tags = generator.generate_title_and_tags(optimized_script)
        
        logger.info(f"콘텐츠 생성 완료: {video_id}")
        logger.info(f"생성된 제목: {title_and_tags['title']}")
        
        if args.generate_only:
            return
    else:
        # 저장된 스크립트 로드
        script_file = os.path.join('data', 'scripts', f"{video_id}_final.json")
        
        if not os.path.exists(script_file):
            logger.error(f"스크립트 파일을 찾을 수 없습니다: {script_file}")
            return
        
        import json
        with open(script_file, 'r', encoding='utf-8') as f:
            optimized_script = json.load(f)
            title_and_tags = {
                'title': optimized_script.get('youtube_title', optimized_script.get('title', '')),
                'tags': optimized_script.get('youtube_tags', [])
            }
    
    # 4. 영상 제작
    if not args.upload_only:
        logger.info(f"영상 제작 시작: {video_id}")
        producer = VideoProducer()
        output_path = producer.create_shorts_video(optimized_script, video_id)
        
        if not output_path:
            logger.error(f"영상 제작 실패: {video_id}")
            return
        
        logger.info(f"영상 제작 완료: {output_path}")
        
        if args.produce_only:
            return
    else:
        # 저장된 영상 파일 경로
        output_path = os.path.join('data', 'output', f"{video_id}_shorts.mp4")
        
        if not os.path.exists(output_path):
            logger.error(f"영상 파일을 찾을 수 없습니다: {output_path}")
            return
    
    # 5. YouTube 업로드
    logger.info(f"YouTube 업로드 시작: {video_id}")
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
    logger.info(f"YouTube URL: https://www.youtube.com/watch?v={uploaded_video_id}")
    
    # 피드백 처리를 위한 메타데이터 저장
    processor = FeedbackProcessor()
    processor.store_video_metadata(
        uploaded_video_id,
        title_and_tags['title'],
        optimized_script
    )
    
    logger.info("24시간 후 다음 명령을 실행하여 성과 분석 및 피드백을 생성하세요:")
    logger.info(f"python main.py --analyze --video-id {uploaded_video_id}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"실행 중 오류 발생: {e}")
        sys.exit(1)
