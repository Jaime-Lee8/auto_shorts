"""
YouTube 데이터 수집 모듈
- YouTube Data API를 사용하여 인기 뉴스 채널의 최신 영상을 검색하고 필터링합니다.
- 트렌딩 이슈를 자동으로 선별합니다.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    YOUTUBE_API_KEY, YOUTUBE_NEWS_CHANNELS, MAX_RESULTS, 
    VIDEO_PUBLISHED_AFTER, MIN_VIEW_COUNT, DATA_DIR, LOGS_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'youtube_collector.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('youtube_collector')

class YouTubeCollector:
    """YouTube 데이터 수집 클래스"""
    
    def __init__(self, api_key=YOUTUBE_API_KEY):
        """
        초기화 함수
        
        Args:
            api_key (str): YouTube Data API 키
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 데이터 저장 디렉토리 생성
        os.makedirs(os.path.join(DATA_DIR, 'videos'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'channels'), exist_ok=True)
        
        logger.info("YouTubeCollector 초기화 완료")
    
    def get_channel_id(self, channel_name):
        """
        채널 이름으로 채널 ID 검색
        
        Args:
            channel_name (str): 채널 이름
            
        Returns:
            str: 채널 ID
        """
        try:
            search_response = self.youtube.search().list(
                q=channel_name,
                type='channel',
                part='id,snippet',
                maxResults=1
            ).execute()
            
            if search_response.get('items'):
                return search_response['items'][0]['id']['channelId']
            else:
                logger.warning(f"채널을 찾을 수 없음: {channel_name}")
                return None
        except HttpError as e:
            logger.error(f"채널 ID 검색 중 오류 발생: {e}")
            return None
    
    def get_recent_videos(self, channel_id, max_results=MAX_RESULTS, published_after=VIDEO_PUBLISHED_AFTER):
        """
        채널의 최근 영상 목록 검색
        
        Args:
            channel_id (str): 채널 ID
            max_results (int): 검색할 최대 영상 수
            published_after (str): 영상 업로드 기간 (예: '1day', '1week')
            
        Returns:
            list: 영상 정보 목록
        """
        try:
            # published_after 문자열을 datetime으로 변환
            time_map = {
                '1day': 1,
                '3days': 3,
                '1week': 7,
                '2weeks': 14,
                '1month': 30
            }
            days = time_map.get(published_after, 1)
            date_after = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
            
            # 채널의 최근 영상 검색
            search_response = self.youtube.search().list(
                channelId=channel_id,
                type='video',
                part='id,snippet',
                maxResults=max_results,
                order='date',
                publishedAfter=date_after
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                logger.info(f"채널 {channel_id}에서 최근 영상을 찾을 수 없음")
                return []
            
            # 영상 상세 정보 가져오기
            videos_response = self.youtube.videos().list(
                id=','.join(video_ids),
                part='snippet,contentDetails,statistics'
            ).execute()
            
            return videos_response.get('items', [])
        except HttpError as e:
            logger.error(f"최근 영상 검색 중 오류 발생: {e}")
            return []
    
    def filter_news_videos(self, videos, min_view_count=MIN_VIEW_COUNT):
        """
        뉴스 영상 필터링
        
        Args:
            videos (list): 영상 정보 목록
            min_view_count (int): 최소 조회수
            
        Returns:
            list: 필터링된 영상 정보 목록
        """
        filtered_videos = []
        
        for video in videos:
            # 조회수 확인
            view_count = int(video['statistics'].get('viewCount', 0))
            
            # 뉴스 관련 키워드 확인
            title = video['snippet']['title'].lower()
            description = video['snippet']['description'].lower()
            
            news_keywords = ['news', 'breaking', 'report', 'update', 'latest', 
                            'world', 'politics', 'economy', 'crisis', 'war', 
                            'election', 'president', 'minister', 'government']
            
            is_news = any(keyword in title or keyword in description for keyword in news_keywords)
            
            # 필터링 조건 적용
            if view_count >= min_view_count and is_news:
                filtered_videos.append(video)
        
        return filtered_videos
    
    def rank_trending_videos(self, videos):
        """
        트렌딩 영상 순위 매기기
        
        Args:
            videos (list): 영상 정보 목록
            
        Returns:
            list: 순위가 매겨진 영상 정보 목록
        """
        # 조회수, 좋아요 수, 댓글 수 기반으로 점수 계산
        for video in videos:
            stats = video['statistics']
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            # 간단한 가중치 점수 계산
            engagement_score = view_count + (like_count * 5) + (comment_count * 10)
            video['engagement_score'] = engagement_score
        
        # 점수 기준으로 정렬
        ranked_videos = sorted(videos, key=lambda x: x.get('engagement_score', 0), reverse=True)
        return ranked_videos
    
    def collect_trending_news(self):
        """
        트렌딩 뉴스 영상 수집
        
        Returns:
            list: 트렌딩 뉴스 영상 목록
        """
        all_videos = []
        
        # 각 뉴스 채널에서 영상 수집
        for channel_name in YOUTUBE_NEWS_CHANNELS:
            logger.info(f"{channel_name} 채널에서 영상 수집 중...")
            
            # 채널 ID 가져오기
            channel_id = self.get_channel_id(channel_name)
            if not channel_id:
                continue
            
            # 최근 영상 가져오기
            videos = self.get_recent_videos(channel_id)
            
            # 뉴스 영상 필터링
            news_videos = self.filter_news_videos(videos)
            
            all_videos.extend(news_videos)
            logger.info(f"{channel_name} 채널에서 {len(news_videos)}개의 뉴스 영상 수집 완료")
        
        # 트렌딩 영상 순위 매기기
        trending_videos = self.rank_trending_videos(all_videos)
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(DATA_DIR, 'videos', f'trending_news_{timestamp}.json')
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(trending_videos, f, ensure_ascii=False, indent=2)
        
        logger.info(f"총 {len(trending_videos)}개의 트렌딩 뉴스 영상 수집 완료")
        logger.info(f"결과 저장 완료: {result_file}")
        
        return trending_videos
    
    def get_video_details(self, video_id):
        """
        영상 상세 정보 가져오기
        
        Args:
            video_id (str): 영상 ID
            
        Returns:
            dict: 영상 상세 정보
        """
        try:
            video_response = self.youtube.videos().list(
                id=video_id,
                part='snippet,contentDetails,statistics'
            ).execute()
            
            if video_response.get('items'):
                return video_response['items'][0]
            else:
                logger.warning(f"영상을 찾을 수 없음: {video_id}")
                return None
        except HttpError as e:
            logger.error(f"영상 상세 정보 가져오기 중 오류 발생: {e}")
            return None

# 테스트 코드
if __name__ == "__main__":
    collector = YouTubeCollector()
    trending_news = collector.collect_trending_news()
    print(f"수집된 트렌딩 뉴스 영상 수: {len(trending_news)}")
    
    if trending_news:
        top_video = trending_news[0]
        print(f"최고 트렌딩 뉴스 영상:")
        print(f"제목: {top_video['snippet']['title']}")
        print(f"채널: {top_video['snippet']['channelTitle']}")
        print(f"조회수: {top_video['statistics'].get('viewCount', 0)}")
        print(f"게시일: {top_video['snippet']['publishedAt']}")
